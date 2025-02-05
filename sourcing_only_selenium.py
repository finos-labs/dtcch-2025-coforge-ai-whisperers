import pandas as pd
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


def scrape_nasdaq_news():
    """Scrape NASDAQ news headlines using Selenium and return as a DataFrame."""
    try:
        # Set up Selenium WebDriver options
        chrome_options = Options()
        chrome_options.add_argument("--headless")  # Run in headless mode
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")

        # Initialize the driver
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

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


def scrape_article_content(driver, url):
    """Scrape article content from NASDAQ pages using Selenium."""
    try:
        # Open the article URL
        driver.get(url)
        time.sleep(2)  # Allow time for the page to load (can be optimized with WebDriverWait)

        # Wait for the content div to load
        wait = WebDriverWait(driver, 10)
        content_div = wait.until(EC.presence_of_element_located(
            (By.XPATH, '//*[@id="MainContainer"]/div[1]/table/tbody/tr/td/div')
        ))

        # Find all <p> tags within the div
        paragraphs = content_div.find_elements(By.TAG_NAME, "p")

        # Extract text and concatenate it into a single string
        content = " ".join([p.text.strip() for p in paragraphs])

        return content
    except Exception as e:
        print(f"Error scraping {url}: {e}")
        return ""


def process_and_save_data(df):
    """Scrape article content using Selenium and save the final DataFrame."""
    if df.empty:
        print("No corporate actions found. Exiting.")
        return

    # Initialize Selenium WebDriver (Headless Mode)
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

    # Scrape article content for each news link
    df["Article_Content"] = df["Link"].apply(lambda url: scrape_article_content(driver, url) if pd.notna(url) and url.startswith("http") else "")

    # Close WebDriver
    driver.quit()

    # Save the final DataFrame
    output_csv = "nasdaq_corporate_actions_selenium.csv"
    df.to_csv(output_csv, index=False)
    print(f"Data saved to {output_csv}")


if __name__ == "__main__":
    news_df = scrape_nasdaq_news()
    filtered_df = filter_corporate_actions(news_df)
    process_and_save_data(filtered_df)
