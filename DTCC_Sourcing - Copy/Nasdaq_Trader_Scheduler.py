import time
import requests
import schedule
from Nasdaq_Trader_Source import process_corporate_actions

# API endpoint to post the data
API_URL = "http://74.249.184.110:8000/insert-corporate-action/"

def process_nasdaq_data():
    print("Fetching latest Nasdaq corporate actions...")
    data = process_corporate_actions()

    if not data:
        print("No new Nasdaq corporate actions found.")
        return

    # Selecting the first 3 records
    first_three_records = data

    for record in first_three_records:
        try:
            response = requests.post(API_URL, json=record)
            print(f"Nasdaq | Status Code: {response.status_code}, Response: {response.json()}")
        except Exception as e:
            print(f"Error posting Nasdaq data: {e}")

# Schedule the job every 15 minutes
schedule.every(15).minutes.do(process_nasdaq_data)

print("Scheduler started. Running every 15 minutes...")

# Keep the scheduler running
while True:
    schedule.run_pending()
    time.sleep(60)  # Sleep for 1 minute to prevent high CPU usage
