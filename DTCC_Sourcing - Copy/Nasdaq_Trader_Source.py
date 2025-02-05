import pandas as pd
from datetime import datetime
from sourcing_selenium_BeautifulSoup import nasdaq_corporate_actions
from anthropic_client import get_anthropic_client
from prompt_templates import PROMPT_TEMPLATES, corporate_action_prompt

def invoke_claude(prompt):
    """Sends a prompt to Claude 3.5 on AWS Bedrock and returns the response."""
    try:
        client = get_anthropic_client()
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

def process_corporate_actions():
    """Fetches corporate actions, processes them, and returns formatted data."""
    df = nasdaq_corporate_actions()
    formatted_data = []
    current_datetime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    for index, row in df.iterrows():
        headline = row['Article_Content']
        prompt = corporate_action_prompt.format(data=headline)
        corporate_action = invoke_claude(prompt)
        
        if corporate_action:
            corporate_action = corporate_action[0].text.strip()
            if corporate_action != "No Corporate Action Found":
                detail_prompt = PROMPT_TEMPLATES[corporate_action].format(data=row.to_dict())
                detail_response = invoke_claude(detail_prompt)
                
                if detail_response:
                    extracted_info = detail_response[0].text.split("\n")
                    company_name = next((line.split(": ")[1] for line in extracted_info if "Company_Name:" in line), "Unknown")
                    announcement_date = next((line.split(": ")[1] for line in extracted_info if "Announcement_Date:" in line), datetime.now().strftime("%Y-%m-%d"))
                    
                    formatted_data.append({
                        "Company": company_name,
                        "Corporate_Action": corporate_action,
                        "Date_Announcement": announcement_date,
                        "Source": row['Link'],
                        "Headline": row['Headline'],
                        "Extracted_Information": detail_response[0].text,
                        "Insertion_Date_Time": current_datetime,
                        "Modified_Date_Time": current_datetime
                    })
    
    return formatted_data
