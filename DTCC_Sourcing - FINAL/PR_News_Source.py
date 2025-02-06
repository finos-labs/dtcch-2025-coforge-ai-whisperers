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
import os
import requests
from bs4 import BeautifulSoup
from prompt_templates import PROMPT_TEMPLATES, corporate_action_prompt
from anthropic_client import get_anthropic_client
import json

# Initialize the AnthropicBedrock client
client = get_anthropic_client()

# def convert_et_to_ist(time_str):
#     # Get current date in ET
#     et_tz = pytz.timezone('US/Eastern')
#     ist_tz = pytz.timezone('Asia/Kolkata')
    
#     # Remove any trailing "ET" and whitespace
#     time_str = time_str.replace("ET", "").strip()
    
#     # Parse time string (format: "HH:MM")
#     try:
#         et_time = datetime.strptime(time_str, "%I:%M")
#     except ValueError as e:
#         print(f"Error parsing time {time_str}: {e}")
#         return None
    
#     # Create full datetime with current date in ET
#     now_et = datetime.now(et_tz)
#     combined_et = now_et.replace(hour=et_time.hour, minute=et_time.minute, second=0, microsecond=0)
    
#     # Convert to IST
#     ist_time = combined_et.astimezone(ist_tz)
#     return ist_time.strftime("%Y-%m-%d %H:%M:%S")
def convert_et_to_ist(time_str):
    # Get current date in ET
    et_tz = pytz.timezone('US/Eastern')
    ist_tz = pytz.timezone('Asia/Kolkata')
    
    # Remove any trailing "ET" and whitespace
    time_str = time_str.replace("ET", "").strip()
    
    # Parse time string (format: "HH:MM")
    try:
        et_time = datetime.strptime(time_str, "%H:%M")
    except ValueError as e:
        print(f"Error parsing time {time_str}: {e}")
        return None
    
    # Create full datetime with current date in ET
    now_et = datetime.now(et_tz)
    combined_et = now_et.replace(hour=et_time.hour, minute=et_time.minute, second=0, microsecond=0)
    
    # Convert to IST
    ist_time = combined_et.astimezone(ist_tz)
    return ist_time.strftime("%Y-%m-%d %H:%M:%S")

# Setup Selenium WebDriver
chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

def scrape_article_data(driver):
    articles = []
    try:
        WebDriverWait(driver, 10).until(
            EC.visibility_of_all_elements_located((By.XPATH, '//*[@class="row newsCards"]'))
        )
        news_cards = driver.find_elements(By.XPATH, '//*[@class="card col-view"]')
        
        for card in news_cards:
            try:
                link = card.find_element(By.XPATH, './/a').get_attribute('href')
                time_str = card.find_element(By.XPATH, './/h3/small').text.strip()
                title = card.find_element(By.XPATH, './/h3').text.strip()
                title = title.split('\n', 1)[-1]  # Remove time from title
                
                # Convert ET time to IST timestamp
                timestamp_ist = convert_et_to_ist(time_str)
                if not timestamp_ist:
                    continue
                
                articles.append({
                    "Title": title,
                    "URL": link,
                    "Timestamp": timestamp_ist
                })
            except Exception as e:
                print(f"Error processing card: {e}")
                
    except Exception as e:
        print(f"Error scraping page: {e}")
    
    return articles

def scrape_articles_until_time_limit(driver):
    base_url = "https://www.prnewswire.com/news-releases/news-releases-list/?page=1&pagesize=100"
    driver.get(base_url)
    time.sleep(3)
    all_articles = []

    while True:
        print(f"Scraping page: {driver.current_url}")
        articles_on_page = scrape_article_data(driver)
        
        # Filter valid timestamps
        valid_articles = [a for a in articles_on_page if a["Timestamp"]]
        
        if valid_articles:
            # Get latest timestamp
            latest_timestamp = max(a["Timestamp"] for a in valid_articles)
            latest_dt = datetime.strptime(latest_timestamp, "%Y-%m-%d %H:%M:%S")
            latest_dt = pytz.timezone('Asia/Kolkata').localize(latest_dt)
            
            # Check if older than 15 minutes
            time_diff = datetime.now(pytz.timezone('Asia/Kolkata')) - latest_dt
            if time_diff > timedelta(minutes=15):
                print("Stopping - found article older than 15 minutes")
                break

            all_articles.extend(valid_articles)

        try:
            next_btn = driver.find_element(By.XPATH, '//*[@id="main"]/section[4]/div/div/div/div/div/nav/ul/li[7]/a')
            next_url = next_btn.get_attribute('href')
            if not next_url or 'page=1' in next_url:  # Handle last page loop
                break
            driver.get(next_url)
            time.sleep(3)
        except Exception as e:
            print("No more pages:", e)
            break

    return all_articles

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

def scrape_article_content(url):
    try:
        response = requests.get(url, timeout=10)
        soup = BeautifulSoup(response.content, 'html.parser')
        content_div = soup.find('div', class_='col-lg-10 col-lg-offset-1')
        
        if content_div:
            # Limit content to 4000 characters to avoid token limits
            content = ' '.join(p.get_text() for p in content_div.find_all('p'))
            return content[:4000]
        return ""
    except Exception as e:
        print(f"Error scraping {url}: {e}")
        return ""

def process_corporate_actions_pr(df):
    formatted_data = []
    current_datetime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    for _, row in df.iterrows():
        if len(row['Article content']) > 3500:  # Skip long articles
            continue
            
        # Corporate action detection
        prompt = corporate_action_prompt.format(data=row['Article content'])
        response = invoke_claude(prompt)
        if not response:
            continue
            
        corporate_action = response[0].text
        if corporate_action == "No Corporate Action Found":
            continue

        # Detail extraction
        detail_prompt = PROMPT_TEMPLATES[corporate_action].format(data=row['Article content'])
        detail_response = invoke_claude(detail_prompt)
        if not detail_response:
            continue
            
        detail_text = detail_response[0].text
        extracted_info = detail_text.split("\n")
        
        formatted_data.append({
            "Company": next((line.split(": ")[1] for line in extracted_info if "Company_Name:" in line), "Unknown"),
            "Corporate_Action": corporate_action,
            "Date_Announcement": row['Timestamp'],
            "Source": row['URL'],
            "Extracted_Information": detail_text,
            "Insertion_Date_Time": current_datetime,
            "Modified_Date_Time": current_datetime
        })
    
    return formatted_data

def fetch_and_process_prnewswire():
    print("Starting PR Newswire scraping...")
    articles = scrape_articles_until_time_limit(driver)
    driver.quit()
    
    if not articles:
        return []
    
    df = pd.DataFrame(articles)
    df['Article content'] = df['URL'].apply(scrape_article_content)
    folder_path = 'PR_News_Raw_Data'
    os.makedirs(folder_path, exist_ok=True)
    filename = datetime.now().strftime('PR_News_%Y%m%d_%H%M%S.csv')
    df.to_csv(os.path.join(folder_path, filename), index=False)
    # Filter out empty content and long articles
    df = df[df['Article content'].str.len() > 0]
    df = df[df['Article content'].str.len() <= 3500]
    
    print(f"Processing {len(df)} articles...")
    return process_corporate_actions_pr(df)

if __name__ == "__main__":
    result = fetch_and_process_prnewswire()
    print(json.dumps(result, indent=2))