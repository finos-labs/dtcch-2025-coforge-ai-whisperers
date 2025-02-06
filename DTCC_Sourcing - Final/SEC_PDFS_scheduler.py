import time
import requests
import schedule
import datetime
from SEC_PDFS import fetch_and_download_sec_filings
from CORPORATE_ACTIONS_PDFS_Source import Corporate_actions_formatted_data
import math
# API endpoints
SCHEDULER_LOGS_URL = "http://74.249.184.110:8000/insert-scheduler-log/"
CORPORATE_ACTIONS_URL = "http://74.249.184.110:8000/insert-corporate-action/"

def process_and_log_sec_filings():
    """ Fetch SEC filings and corporate actions data, log execution details, and post records """
    start_time = time.time()

    print("Fetching latest SEC filings...")
    fetch_and_download_sec_filings()  # Fetch SEC filings (No return value expected)

    print("Fetching latest Corporate Actions data...")
    records = Corporate_actions_formatted_data()

    end_time = time.time()
    execution_time = round(end_time - start_time, 2)
    execution_time = math.ceil(execution_time)
    total_records = len(records)
    status = "Success" if total_records > 0 else "Unsuccess"
    current_time = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")

    # Log execution details
    log_data = {
        "Scheduler_Name": "SEC & Corporate Actions Data Fetcher",
        "Source": "SEC & Corporate Actions API",
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
    if records:
        for record in records:
            try:
                response = requests.post(CORPORATE_ACTIONS_URL, json=record)
                print(f"Corporate Actions | Status Code: {response.status_code}, Response: {response.json()}")
            except Exception as e:
                print(f"Error posting Corporate Actions data: {e}")

# Schedule the job every 15 minutes
schedule.every(15).minutes.do(process_and_log_sec_filings)

print("Scheduler started. Running every 15 minutes...")

# Keep the scheduler running
while True:
    schedule.run_pending()
    time.sleep(60)  # Sleep for 1 minute to prevent high CPU usage
