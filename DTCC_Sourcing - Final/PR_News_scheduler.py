import time
import requests
import schedule
import datetime
from PR_News_Source import fetch_and_process_prnewswire
import math
# API endpoints
SCHEDULER_LOGS_URL = "http://74.249.184.110:8000/insert-scheduler-log/"
CORPORATE_ACTIONS_URL = "http://74.249.184.110:8000/insert-corporate-action/"

def process_and_log_pr_news():
    """ Fetch PR News data, log execution details, and post records """
    start_time = time.time()

    print("Fetching latest PR News data...")
    pr_results = fetch_and_process_prnewswire()

    end_time = time.time()
    execution_time = round(end_time - start_time, 2)
    total_records = len(pr_results)
    status = "Success" if total_records > 0 else "Unsuccess"
    current_time = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    execution_time = math.ceil(execution_time)  
    # Log execution details
    log_data = {
        "Scheduler_Name": "PR News Fetcher",
        "Source": "https://www.prnewswire.com/news-releases/news-releases-list/?page=1&pagesize=25",
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
    if pr_results:
        for record in pr_results:
            try:
                response = requests.post(CORPORATE_ACTIONS_URL, json=record)
                print(f"PR News | Status Code: {response.status_code}, Response: {response.json()}")
            except Exception as e:
                print(f"Error posting PR News data: {e}")

# Schedule the job every 15 minutes
schedule.every(15).minutes.do(process_and_log_pr_news)

print("Scheduler started. Running every 15 minutes...")

# Keep the scheduler running
while True:
    schedule.run_pending()
    time.sleep(60)  # Sleep for 1 minute to prevent high CPU usage
