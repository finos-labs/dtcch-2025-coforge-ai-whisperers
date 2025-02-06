import time
import requests
import schedule
import datetime
from FINRA_Source import get_formatted_financial_data
import math
# API endpoints
SCHEDULER_LOGS_URL = "http://74.249.184.110:8000/insert-scheduler-log/"
CORPORATE_ACTIONS_URL = "http://74.249.184.110:8000/insert-corporate-action/"

def process_and_log_finra_data():
    """ Fetch FINRA data, log execution details, and post records """
    start_time = time.time()

    print("Fetching latest FINRA data...")
    extracted_data = get_formatted_financial_data()

    end_time = time.time()
    execution_time = round(end_time - start_time, 2)
    total_records = len(extracted_data)
    status = "Success" if total_records > 0 else "Unsuccess"
    current_time = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    execution_time = math.ceil(execution_time)
    # Log execution details
    log_data = {
        "Scheduler_Name": "FINRA Data Fetcher",
        "Source": "https://otce.finra.org/otce/dailyList",
        "Date_Time_Scheduler_Ran": current_time,
        "Total_Records_Fetched": total_records,
        "Time_Taken": execution_time,
        "Status": status
    }

    try:
        response = requests.post(SCHEDULER_LOGS_URL, json=log_data)
        print(f"Scheduler Log | Status Code: {response.status_code}, Response: {response.text}")
    except Exception as e:
        print(f"Error posting Scheduler Log: {e}")

    # If records exist, send them to the corporate actions API
    if extracted_data:
        for record in extracted_data:
            try:
                response = requests.post(CORPORATE_ACTIONS_URL, json=record)
                print(f"FINRA | Status Code: {response.status_code}, Response: {response.json()}")
            except Exception as e:
                print(f"Error posting FINRA data: {e}")

# Schedule the job every 5 minutes
schedule.every(5).minutes.do(process_and_log_finra_data)

print("Scheduler started. Running every 5 minutes...")

# Keep the scheduler running
while True:
    schedule.run_pending()
    time.sleep(60)  # Sleep for 1 minute to prevent high CPU usage
