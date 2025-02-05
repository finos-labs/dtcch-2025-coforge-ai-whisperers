import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pandas as pd
from datetime import datetime, timedelta
import pytz
import requests
from bs4 import BeautifulSoup
from prompt_templates import PROMPT_TEMPLATES, corporate_action_prompt
from anthropic_client import get_anthropic_client
import json

# Initialize the AnthropicBedrock client
client = get_anthropic_client()

# Function to convert UTC to IST
def convert_utc_to_ist(utc_str):
    # Parse the UTC timestamp string
    utc_tz = pytz.utc  # UTC timezone
    ist_tz = pytz.timezone('Asia/Kolkata')  # IST timezone
    
    utc_time = datetime.strptime(utc_str, "%Y-%m-%dT%H:%M:%SZ")
    utc_time = pytz.utc.localize(utc_time)  # Localize to UTC
    
    # Convert to IST by changing the timezone
    ist_time = utc_time.astimezone(ist_tz)
    
    # Return IST time as a string in desired format
    return ist_time.strftime("%Y-%m-%d %H:%M:%S")  # Format like "2025-02-05 05:33:00"

# Setup Selenium WebDriver
chrome_options = Options()
chrome_options.add_argument("--headless")  # Headless mode for no UI
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--enable-unsafe-swiftshader")  # Enables software WebGL rendering
chrome_options.add_argument("--disable-gpu")  # Disables hardware acceleration to prevent conflicts
# chrome_options.add_argument("--headless")
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

# Function to scrape article details from each page
def scrape_article_data(driver, url):
    driver.get(url)
    time.sleep(2)  # wait for page to load

    # Extract all articles
    articles = []
    try:
        # Wait for articles list to load
        wait = WebDriverWait(driver, 10)
        article_elements = wait.until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="headlines"]/ul/li')))
        
        for article in article_elements:
            title_element = article.find_element(By.XPATH, './/a[@class="bwTitleLink"]')
            link = title_element.get_attribute("href")
            title = title_element.text.strip()

            # Extract timestamp
            time_element = article.find_element(By.XPATH, './/div[@class="bwTimestamp"]/time')
            timestamp_str = time_element.get_attribute("datetime") if time_element else None

            if timestamp_str:
                # Convert UTC timestamp to IST
                timestamp_ist = convert_utc_to_ist(timestamp_str)
                articles.append({
                    "Title": title,
                    "URL": link,
                    "Timestamp": timestamp_ist
                })
            else:
                # Send False instead of skipping
                articles.append({
                    "Title": title,
                    "URL": link,
                    "Timestamp": False
                })
                
    except Exception as e:
        print(f"Error scraping articles: {e}")
    
    return articles

# Function to continuously scrape articles until a timestamp is outside the last 15 minutes
def scrape_articles_until_time_limit(driver):
    base_url = "https://www.businesswire.com/portal/site/home/news/"
    driver.get(base_url)
    time.sleep(2)  # wait for the page to load

    all_articles = []

    while True:
        print(f"Scraping page: {driver.current_url}")
        # Scrape articles on the current page
        articles_on_page = scrape_article_data(driver, driver.current_url)
        
        # Filter out articles where timestamp is False (missing timestamp)
        articles_on_page = [article for article in articles_on_page if article["Timestamp"] != False]
        
        if articles_on_page:
            # Get the latest timestamp in IST format
            latest_timestamp = max(article["Timestamp"] for article in articles_on_page)

            # Convert it to datetime object for comparison and localize it to IST
            latest_timestamp_dt = datetime.strptime(latest_timestamp, "%Y-%m-%d %H:%M:%S")
            latest_timestamp_dt = pytz.timezone('Asia/Kolkata').localize(latest_timestamp_dt)
            
            # Calculate the time difference between now and the latest timestamp
            time_diff = datetime.now(pytz.timezone('Asia/Kolkata')) - latest_timestamp_dt

            # If the latest timestamp is more than 15 minutes ago, stop scraping
            if time_diff > timedelta(minutes=500):
                print("Stopping scraping as the latest article is older than 15 minutes.")
                break

            all_articles.extend(articles_on_page)

        try:
            # Check if the 'Next' link exists and click it
            next_button = driver.find_element(By.XPATH, '//*[@id="paging"]/div[2]/div[2]/a')
            next_url = next_button.get_attribute('href')
            if next_url:
                driver.get(next_url)
                time.sleep(2)  # wait for the next page to load
            else:
                break  # No more pages to scrape
        except Exception as e:
            print("No next page found or error navigating to next page:", e)
            break

    return all_articles

# Scrape article content from the URLs
def scrape_article_content(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')

    # Extract the article body content
    article_body = soup.find('div', class_='bw-release-story')
    if article_body:
        # Get text and remove line breaks
        article_text = " ".join(article_body.get_text().splitlines())
        return article_text
    return "Article content not found."

# Function to invoke Claude for processing
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

# Function to process corporate actions
def process_corporate_actions(df):
    formatted_data = []
    current_datetime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    for index, row in df.iterrows():
        # Determine corporate action type
        prompt = corporate_action_prompt.format(data=row['Article content'])
        response = invoke_claude(prompt)
        if response:
            corporate_action = response[0].text

            if corporate_action != "No Corporate Action Found":
                # Extract details based on corporate action type
                detail_prompt = PROMPT_TEMPLATES[corporate_action].format(data=row['Article content'])
                detail_response = invoke_claude(detail_prompt)
                detail_response = detail_response[0].text
                if detail_response:
                    extracted_info = detail_response.split("\n")
                    company_name = next((line.split(": ")[1] for line in extracted_info if "Company_Name:" in line), "Unknown")
                    announcement_date = next((line.split(": ")[1] for line in extracted_info if "Announcement_Date:" in line), current_datetime)
                    # announcement_date = next((line.split(": ")[1] for line in extracted_info if "Announcement_Date:" in line), datetime.now().strftime("%Y-%m-%d"))
                    announcement_date= announcement_date if announcement_date else datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    formatted_data.append({
                        "Company": company_name,
                        "Corporate_Action": corporate_action,
                        "Date_Announcement": announcement_date,
                        "Source": row['URL'],
                        "Extracted_Information": detail_response,
                        "Insertion_Date_Time": current_datetime,
                        "Modified_Date_Time": current_datetime
                    })
    
    return formatted_data

# Main function to fetch and process corporate actions
def fetch_and_process_corporate_actions():
    # Step 1: Scrape articles until time limit is reached
    print("Starting the article scraping process...")
    articles_data = scrape_articles_until_time_limit(driver)
    
    # Close the WebDriver
    driver.quit()
    
    # Step 2: Convert the scraped data into DataFrame
    if not articles_data:
        print("No articles found.")
        return []

    df = pd.DataFrame(articles_data)
    
    # Step 3: Scrape article content for each URL in the DataFrame
    print("Fetching article contents...")
    df['Article content'] = df['URL'].apply(scrape_article_content)
    
    # Step 4: Process corporate actions based on the article content
    print("Processing corporate actions...")
    formatted_data = process_corporate_actions(df)

    return formatted_data

# Execute the main function
if __name__ == "__main__":
    result = fetch_and_process_corporate_actions()
    print(result)