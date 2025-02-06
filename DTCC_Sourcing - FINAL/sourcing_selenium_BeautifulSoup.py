import pandas as pd
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from datetime import datetime

def scrape_nasdaq_news():
    """Scrape NASDAQ news headlines using Selenium and return as a DataFrame."""
    try:
        # Set up Chrome options
        chrome_options = Options()
        chrome_options.add_argument("--headless")  # Run in headless mode
        
        # Initialize the driver
        driver = webdriver.Chrome(options=chrome_options)
        
        # Navigate to the NASDAQ news page
        url = "https://www.nasdaqtrader.com/Trader.aspx?id=currentheadlines"
        driver.get(url)
        
        # Wait for the news table to load
        wait = WebDriverWait(driver, 10)
        wait.until(EC.presence_of_element_located((By.ID, "curHeadlinesDiv")))

        # Lists to store extracted data
        dates, headlines, links = [], [], []
        
        # Locate all table rows
        rows = driver.find_elements(By.XPATH, "//div[@id='curHeadlinesDiv']/table/tbody/tr")[1:]

        for row in rows:
            cols = row.find_elements(By.TAG_NAME, "td")
            if len(cols) >= 2:
                dates.append(cols[0].text.strip())
                headlines.append(cols[1].text.strip())

                # Extract link if present
                try:
                    link = cols[1].find_element(By.TAG_NAME, "a").get_attribute("href")
                except:
                    link = ""
                links.append(link)

        # Close the browser
        driver.quit()

        # Create a DataFrame
        df = pd.DataFrame({"Date": dates, "Headline": headlines, "Link": links})
        return df

    except Exception as e:
        print(f"Error during NASDAQ scraping: {e}")
        return pd.DataFrame(columns=["Date", "Headline", "Link"])


def filter_corporate_actions(df):
    """Filter headlines containing 'Corporate Actions'."""
    return df[df["Headline"].str.contains("Corporate Actions", case=False, na=False)]


def scrape_article_content(url):
    # Fetch the HTML content
    response = requests.get(url)
    html_content = response.content

    # Parse the HTML content using BeautifulSoup
    soup = BeautifulSoup(html_content, 'html.parser')

    # Extract the relevant information
    news_content = soup.find('div', class_='newscontentbox2')
    
    if not news_content:
        return "Error: Content not found"

    paragraph = news_content.find('p').text.strip() if news_content.find('p') else ""
    
    # Check if the table exists
    table = news_content.find('table')
    data = {}
    if table:
        rows = table.find_all('tr')

        # Extract table data
        for row in rows:
            columns = row.find_all('td')
            header = row.find('th').text.strip() if row.find('th') else "Header not found"
            value = columns[0].text.strip() if columns else "Value not found"
            data[header] = value
    else:
        data = {"Note": "No table found"}

    # Combine paragraph and table data into a single string
    article_content = paragraph + "\n\n" + "\n".join([f"{key}: {value}" for key, value in data.items()])

    return article_content


def process_and_save_data(df):
    """Process the filtered DataFrame, scrape article content, and save to CSV."""
    if df.empty:
        print("No corporate actions found. Exiting.")
        return
    
    # Scrape article content for each news link
    # Scrape article content for each news link
    # Scrape article content for each news link
    df["Article_Content"] = df["Link"].apply(lambda url: scrape_article_content(url) if pd.notna(url) and url.startswith("http") else "")
    # df["Article_Content"] = df["Link"].apply(lambda url: scrape_article_content(url) if pd.notna(url) and url.startswith("http") else "")
    # df["Article_Content"] = df["Link"].apply(lambda url: scrape_article_content(url) if pd.notna(url) and url.startswith("http") else "")
    # Save the final DataFrame
    output_csv = "nasdaq_corporate_actions_with_Article_content.csv"
    df.to_csv(output_csv, index=False)
    print(f"Data saved to {output_csv}")
    return df


def nasdaq_corporate_actions():
    news_df = scrape_nasdaq_news()
    filtered_df = filter_corporate_actions(news_df)
    k=process_and_save_data(filtered_df)
    # Get today's date in the same format as the 'Date' column
    today = datetime.now().strftime('%b %d, %Y')

    # Filter the dataframe to get only the records of today
    today_records = k[k['Date'] == today]
    print(today_records)
    return today_records
