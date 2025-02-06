from sec_api import QueryApi, PdfGeneratorApi
import os
import re
from datetime import datetime

def fetch_and_download_sec_filings():
    # Get today's date in the required format
    today_date = datetime.today().strftime('%Y-%m-%d')
    
    # Initialize APIs
    queryApi = QueryApi(api_key=os.environ.get("SEC_API_KEY"))
    pdfGeneratorApi = PdfGeneratorApi(api_key=os.environ.get("SEC_API_KEY"))
    
    # Query for filings on the given date
    base_query = {
        "query": {
            "query_string": {
                "query": f"formType:(\"10-K\", \"10-Q\", \"8-K\", \"S-4\") AND filedAt:[{today_date} TO {today_date}]",
                "time_zone": "America/New_York"
            }
        },
        "from": "0",
        "size": "200",
        "sort": [{"filedAt": {"order": "desc"}}]
    }
    
    print(f"Querying SEC for filings on {today_date}...")
    response = queryApi.get_filings(base_query)
    
    # Extract filing URLs and metadata
    filing_data = [(filing["linkToFilingDetails"], filing["companyName"], filing["formType"]) for filing in response.get("filings", [])]
    
    # Save URLs to file
    with open("filing_urls.txt", "w") as log_file:
        for url, company, form_type in filing_data:
            log_file.write(f"{company},{form_type},{url}\n")
    
    print(f"{len(filing_data)} filing URLs retrieved.")
    
    # Ensure directory exists
    os.makedirs(r"C:\Users\hackathon\DTCC_Sourcing\CORPORATE_ACTIONS_PDFS\Present_CA_PDFS", exist_ok=True)
    
    # Function to sanitize filenames
    def sanitize_filename(name):
        return re.sub(r'[^a-zA-Z0-9_.-]', '_', name)
    
    # Download all filings as PDFs
    for url, company, form_type in filing_data:
        try:
            pdf_content = pdfGeneratorApi.get_pdf(url)
            file_name = f"{sanitize_filename(company)}_{sanitize_filename(form_type)}.pdf"
            download_to = os.path.join("SEC_filings", file_name)
            
            with open(download_to, "wb") as file:
                file.write(pdf_content)
            print(f"Downloaded: {file_name}")
        except Exception as e:
            print(f"Error downloading {url}: {e}")
    
    print("All filings downloaded and saved as PDFs.")

# Execute function
fetch_and_download_sec_filings()
