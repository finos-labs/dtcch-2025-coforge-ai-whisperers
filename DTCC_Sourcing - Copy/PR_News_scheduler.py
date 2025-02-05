import time
import requests
import schedule
from PR_News_Source import fetch_and_process_prnewswire

# API endpoint to post the data
API_URL = "http://74.249.184.110:8000/insert-corporate-action/"

def process_pr_news_data():
    print("Fetching latest PR News data...")
    pr_results = fetch_and_process_prnewswire()

    if not pr_results:
        print("No new PR News data found in the last 15 minutes.")
        return

    # Selecting the first 3 records
    first_three_records = pr_results[:3]

    for record in first_three_records:
        try:
            response = requests.post(API_URL, json=record)
            print(f"PR News | Status Code: {response.status_code}, Response: {response.json()}")
        except Exception as e:
            print(f"Error posting PR News data: {e}")

# Schedule the job every 15 minutes
schedule.every(15).minutes.do(process_pr_news_data)

print("Scheduler started. Running every 15 minutes...")

# Keep the scheduler running
while True:
    schedule.run_pending()
    time.sleep(60)  # Sleep for 1 minute to prevent high CPU usage
