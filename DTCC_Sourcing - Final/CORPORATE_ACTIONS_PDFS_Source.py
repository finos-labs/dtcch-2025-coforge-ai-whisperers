import os
import PyPDF2
import pandas as pd
from datetime import datetime
from anthropic_client import get_anthropic_client
from prompt_templates import PROMPT_TEMPLATES, corporate_action_prompt
import json
# Initialize the AnthropicBedrock client
client = get_anthropic_client()

def extract_text_from_pdfs(folder_path):
    """Extract text from all PDFs in the given folder."""
    pdf_text_dict = {}
    
    for filename in os.listdir(folder_path):
        if filename.endswith(".pdf"):
            pdf_path = os.path.join(folder_path, filename)
            
            with open(pdf_path, "rb") as pdf_file:
                reader = PyPDF2.PdfReader(pdf_file)
                text = "".join(page.extract_text() for page in reader.pages if page.extract_text())
                
                pdf_text_dict[filename] = text
    
    return pdf_text_dict

# def move_files_to_master(present_folder, master_folder):
#     for filename in os.listdir(present_folder):
#         file_path = os.path.join(present_folder, filename)
#         destination_path = os.path.join(master_folder, filename)

#         if os.path.isfile(file_path):
#             if os.path.exists(destination_path):
#                 print(f"Skipping '{filename}': already exists in the master folder.")
#                 continue
            
#             os.rename(file_path, destination_path)
#             print(f"Moved '{filename}' to the master folder.")
import shutil

def move_files_to_master(present_folder, master_folder):
    """Move all files from Present_CA_PDFS to Master_CA_PDFS, skipping existing files."""
    for filename in os.listdir(present_folder):
        file_path = os.path.join(present_folder, filename)
        destination_path = os.path.join(master_folder, filename)

        if os.path.isfile(file_path):
            if os.path.exists(destination_path):
                print(f"Skipping '{filename}': already exists in the master folder.")
                continue

            try:
                shutil.move(file_path, destination_path)
                print(f"Moved '{filename}' to the master folder.")
            except UnicodeEncodeError:
                print(f"Unicode error encountered for file: {filename}. Skipping this file.")

def invoke_claude(prompt):
    """Sends a prompt to Claude 3.5 on AWS Bedrock and returns the response."""
    try:
        response = client.messages.create(
            model="anthropic.claude-3-5-sonnet-20241022-v2:0",
            max_tokens=200,
            temperature=0.5,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        return response.content
    except Exception as e:
        print(f"ERROR: Can't invoke the model. Reason: {e}")
        return None

def process_corporate_actions(pdf_text_dict):
    """Process extracted text to determine corporate actions and extract details."""
    formatted_data = []
    current_datetime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    for filename, text in pdf_text_dict.items():
        # Determine corporate action type
        prompt = corporate_action_prompt.format(data=text)
        response = invoke_claude(prompt)
        response=response[0].text
        if response and response != "No Corporate Action Found":
            corporate_action = response.strip()
            
            # Extract details based on corporate action type
            detail_prompt = PROMPT_TEMPLATES[corporate_action].format(data=text)
            detail_response = invoke_claude(detail_prompt)
            
            if detail_response:
                # Extract Company Name and Announcement Date (example logic, adjust as needed)
                extracted_info = detail_response[0].text.split("\n")
                company_name = next((line.split(": ")[1] for line in extracted_info if "Company_Name:" in line), "Unknown")
                announcement_date = next((line.split(": ")[1] for line in extracted_info if "Announcement_Date:" in line), datetime.now().strftime("%Y-%m-%d"))
                
                formatted_data.append({
                    "Company": company_name,
                    "Corporate_Action": corporate_action,
                    "Date_Announcement": announcement_date,
                    "Source": filename,
                    "Extracted_Information": detail_response[0].text,
                    "Insertion_Date_Time": current_datetime,
                    "Modified_Date_Time": current_datetime
                })
    
    return formatted_data

def Corporate_actions_formatted_data():
    # Define folder paths
    base_folder = "CORPORATE_ACTIONS_PDFS"
    present_folder = os.path.join(base_folder, "Present_CA_PDFS")
    master_folder = os.path.join(base_folder, "Master_CA_PDFS")
    frontend_master_folder = r"C:\Users\hackathon\Documents\DTCC\interface\src\assets\Master_CA_PDFS"
    # Step 1: Extract text from PDFs in Present_CA_PDFS
    pdf_text_dict = extract_text_from_pdfs(present_folder)
    # print(pdf_text_dict)
    
    # Step 2: Move files to Master_CA_PDFS and empty Present_CA_PDFS
    move_files_to_master(present_folder, master_folder)
    move_files_to_master(master_folder, frontend_master_folder)
    
    # Step 3: Process corporate actions
    formatted_data = process_corporate_actions(pdf_text_dict)
    
    # Step 4: Create a DataFrame and filter out "No Corporate Action Found" records
    df = pd.DataFrame(formatted_data)
    df = df[df["Corporate_Action"] != "No Corporate Action Found"]
    folder_path = 'CORPORATE_PDFS_Raw_Data'
    os.makedirs(folder_path, exist_ok=True)
    filename = datetime.now().strftime('pdfs_%Y%m%d_%H%M%S.csv')
    df.to_csv(os.path.join(folder_path, filename), index=False)
    # Step 5: Convert DataFrame to a list of dictionaries
    records_list = df.to_dict(orient='records')
    
    # Step 6: Print or save the results
    # records_list = formatted_data
    # print(records_list)
    # Optionally, save to a JSON file
    with open("corporate_actions_output.json", "w") as f:
        json.dump(records_list, f, indent=4)
    return records_list



import requests

# Define the API endpoint
url = "http://74.249.184.110:8000/insert-corporate-action/"

def main():
    records = Corporate_actions_formatted_data()  # Assuming this function is defined elsewhere
    
    # Loop through the records and send POST requests
    for record in records:
        response = requests.post(url, json=record)
        print(f"Status Code: {response.status_code}, Response: {response.json()}")

if __name__ == "__main__":
    main()
