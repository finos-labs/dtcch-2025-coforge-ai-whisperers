import time
import requests
import schedule
from FINRA_Source import get_formatted_financial_data

# formatted_data = get_formatted_financial_data()

# API endpoint to post the data
API_URL = "http://74.249.184.110:8000/insert-corporate-action/"

def job():
    print("Fetching latest FINRA data...")
    extracted_data = get_formatted_financial_data()

    if not extracted_data:
        print("No new data found in the last 15 minutes.")
        return

    # Selecting the first 3 records
    first_three_records = extracted_data

    for record in first_three_records:
        try:
            response = requests.post(API_URL, json=record)
            print(f"Status Code: {response.status_code}, Response: {response.json()}")
        except Exception as e:
            print(f"Error posting data: {e}")

# Schedule the job every 15 minutes
schedule.every(5).minutes.do(job)

print("Scheduler started. Running every 15 minutes...")

# Keep the scheduler running
while True:
    schedule.run_pending()
    time.sleep(60)  # Sleep for 1 minute to prevent high CPU usage
