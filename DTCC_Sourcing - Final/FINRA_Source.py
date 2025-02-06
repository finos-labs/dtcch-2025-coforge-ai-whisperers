import requests
import pandas as pd
from io import StringIO
from datetime import datetime, timedelta
import pytz
from prompt_templates import PROMPT_TEMPLATES, corporate_action_prompt
from anthropic_client import get_anthropic_client
import json

# Initialize the AnthropicBedrock client
client = get_anthropic_client()

def invoke_claude(prompt):
    """Sends a prompt to Claude 3.5 on AWS Bedrock and returns the response."""
    try:
        response = client.messages.create(
            model="anthropic.claude-3-5-sonnet-20241022-v2:0",
            max_tokens=200,
            temperature=0.5,
            messages=[{"role": "user", "content": prompt}]
        )
        return response.content
    except Exception as e:
        print(f"ERROR: Can't invoke the model. Reason: {e}")
        return None

def fetch_financial_data():
    url = 'https://api.finra.org/data/group/otcMarket/name/otcDailyList'
    data = {
        "offset": 0,
        "compareFilters": [
            {
                "fieldName": "calendarDay",
                "fieldValue": datetime.now().strftime('%Y-%m-%d'),  # Current date in yyyy-mm-dd format
                "compareType": "EQUAL"
            }
        ],
        "delimiter": "|",
        "limit": 5000,
        "quoteValues": False,
        "fields": [
            "dailyListDatetime",
            "dailyListReasonDescription",
            "newSymbolCode",
            "oldSymbolCode",
            "newSecurityDescription",
            "oldSecurityDescription",
            "exDate",
            "commentText",
            "newMarketCategoryCode",
            "oldMarketCategoryCode",
            "newOATSReportableFlag",
            "oldOATSReportableFlag",
            "newRoundLotQuantity",
            "oldRoundLotQuantity",
            "newRegFeeFlag",
            "oldRegFeeFlag",
            "newClassText",
            "oldClassText",
            "newFinancialStatusCode",
            "oldFinancialStatusCode",
            "subjectCorporateActionCode",
            "newADROrdnyShareRate",
            "oldADROrdinaryShareRate",
            "newMaturityExpirationDate",
            "oldMaturityExpirationDate",
            "offeringTypeDescription",
            "forwardSplitRate",
            "reverseSplitRate",
            "dividendTypeCode",
            "stockPercentage",
            "cashAmountText",
            "declarationDate",
            "recordDate",
            "paymentDate",
            "paymentMethodCode",
            "ADRFeeAmount",
            "ADRTaxReliefAmount",
            "ADRGrossRate",
            "ADRNetRate",
            "ADRIssuanceFeeAmount",
            "ADRWitholdingTaxPercentage",
            "qualifiedDividendDescription"
        ],
        "sortFields": [
            "-dailyListDatetime"
        ]
    }

    pd.set_option('display.width', 200)
    pd.set_option('display.max_columns', 8)

    df = pd.read_csv(StringIO(requests.post(url, json=data).text), delimiter='|')
    df['dailyListDatetime'] = pd.to_datetime(df['dailyListDatetime'])
    # from datetime import datetime, timedelta
    # import pytz

        # Ensure the 'dailyListDatetime' column is in datetime format
    df['dailyListDatetime'] = pd.to_datetime(df['dailyListDatetime'])

    # Calculate the time threshold for the last 10 hours
    time_threshold = datetime.now() - timedelta(hours=10)

    # Filter the dataframe to get the latest 10 hours of data
    latest_records = df[df['dailyListDatetime'] >= time_threshold]

    # Print the filtered dataframe
    print(latest_records)
    import os
# from datetime import datetime

    folder_path = 'FINRA_Raw_Data'
    os.makedirs(folder_path, exist_ok=True)
    filename = datetime.now().strftime('finra_%Y%m%d_%H%M%S.csv')
    latest_records.to_csv(os.path.join(folder_path, filename), index=False)
    # Convert dataframe to a list of dictionaries
    return latest_records.to_dict(orient='records')

def extract_financial_data(records_list):
    results = []
    for record in records_list:
        if not isinstance(record, dict):
            print(f"Skipping invalid record: {record}")
            continue
        
        event_type = record.get("dailyListReasonDescription", "").strip()
        prompt_template = PROMPT_TEMPLATES.get(event_type)

        if not prompt_template:
            print(f"Skipping record with unknown event type: {event_type}")
            continue

        record_str = "\n".join([f"{k}: {v}" for k, v in record.items()])
        prompt = prompt_template.format(data=record_str)
        response = invoke_claude(prompt)

        if response:
            results.append({
                "event_type": event_type,
                "original_data": record,
                "extracted_data": response[0].text
            })
    
    return results

def get_formatted_financial_data():
    records_list = fetch_financial_data()
    extracted_data = extract_financial_data(records_list)
    
    # Define the source and current date-time
    current_datetime = datetime.now().isoformat()

    # Create the list of dictionaries
    formatted_data = []

    for item in extracted_data:
        formatted_data.append({
            "Company": item['original_data'].get('newSecurityDescription', 'N/A'),
            "Corporate_Action": item['event_type'],
            "Date_Announcement": str(item['original_data'].get('dailyListDatetime', 'N/A')),
            "Source": 'FINRA',
            "Extracted_Information": item['extracted_data'],
            "Insertion_Date_Time": current_datetime,
            "Modified_Date_Time": current_datetime
        })
    
    return formatted_data

# Call this function from another file to get the formatted data
if __name__ == "__main__":
    formatted_data = get_formatted_financial_data()
    for entry in formatted_data:
        print(entry)
