import time
import requests
import schedule
from Bussiness_Wire_Source import fetch_and_process_corporate_actions

# API endpoint to post the data
API_URL = "http://74.249.184.110:8000/insert-corporate-action/"

def process_business_wire_data():
    print("Fetching latest Business Wire data...")
    extracted_data = fetch_and_process_corporate_actions()

    if not extracted_data:
        print("No new Business Wire data found in the last 15 minutes.")
        return

    # Selecting the first 3 records
    first_three_records = extracted_data[:3]

    for record in first_three_records:
        try:
            response = requests.post(API_URL, json=record)
            print(f"Business Wire | Status Code: {response.status_code}, Response: {response.json()}")
        except Exception as e:
            print(f"Error posting Business Wire data: {e}")

# Schedule the job every 15 minutes
schedule.every(5).minutes.do(process_business_wire_data)

print("Scheduler started. Running every 15 minutes...")

# Keep the scheduler running
while True:
    schedule.run_pending()
    time.sleep(60)  # Sleep for 1 minute to prevent high CPU usage
