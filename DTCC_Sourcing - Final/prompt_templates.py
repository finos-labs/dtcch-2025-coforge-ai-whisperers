PROMPT_TEMPLATES = {
    "Forward Split": """We have received the following financial record:

{data}

We require the following details (if available):
Company_Name:
Company_Symbol:
Value_Date:
Custodian_ID:
Account_Number:
Settlement_Amount:
Currency:
Tax_Details:
Eligibility:
Debit_Security_Details:
Remarks:
Stock_Split_Ratio:
Ex-Date:
Record_Date:
Announcement_Date:
Payment_Date:
Adjusted_Share_Price_and_Quantity:
Adjustment_Factor:
Credit_New_Security_Asset_ID:

If any value is missing in the record, leave it empty.

Please provide the extracted values as key-value pairs in the format:
Key: Value

Do not provide any explanations or add any extra information other than this.
""",
    "Reverse Split": """We have received the following financial record:

{data}

We require the following details (if available):
Company_Name:
Company_Symbol:
Value_Date:
Custodian_ID:
Account_Number:
Settlement_Amount:
Currency:
Tax_Details:
Eligibility:
Debit_Security_Details:
Remarks:
Reverse_Split_Ratio:
Ex-Date:
Record_Date:
Announcement_Date:
Adjusted_Share_Price_and_Quantity:
Adjustment_Factor:
Credit_New_Security_Asset_ID:

If any value is missing in the record, leave it empty.

Please provide the extracted values as key-value pairs in the format:
Key: Value

Do not provide any explanations or add any extra information other than this.
""",
    "Stock Dividend Regular": """We have received the following financial record:

{data}

We require the following details (if available):
Company_Name:
Company_Symbol:
Value_Date:
Custodian_ID:
Account_Number:
Settlement_Amount:
Currency:
Tax_Details:
Eligibility:
Debit_Security_Details:
Remarks:
Stock_Dividend_Ratio:
Ex-Date:
Record_Date:
Announcement_Date:
Payment_Date:
Adjusted_Share_Price_and_Quantity:
Credit_New_Security_Asset_ID:
Cost_Allocation:

If any value is missing in the record, leave it empty.

Please provide the extracted values as key-value pairs in the format:
Key: Value

Do not provide any explanations or add any extra information other than this.
""",
    "Cash Dividend Regular": """We have received the following financial record:

{data}

We require the following details (if available):
Company_Name:
Company_Symbol:
Value_Date:
Custodian_ID:
Account_Number:
Settlement_Amount:
Currency:
Tax_Details:
Eligibility:
Debit_Security_Details:
Remarks:
Dividend_Amount_per_Share:
Ex-Date:
Record_Date:
Announcement_Date:
Payment_Date:
Sedol:
Currency:
Dividend_Rate:

If any value is missing in the record, leave it empty.

Please provide the extracted values as key-value pairs in the format:
Key: Value

Do not provide any explanations or add any extra information other than this.
""",
    "Rights Issue": """We have received the following financial record:

{data}

We require the following details (if available):
Company_Name:
Company_Symbol:
Value_Date:
Custodian_ID:
Account_Number:
Settlement_Amount:
Currency:
Tax_Details:
Eligibility:
Debit_Security_Details:
Remarks:
Ex-Date:
Credit_New_Security_Asset_ID:

If any value is missing in the record, leave it empty.

Please provide the extracted values as key-value pairs in the format:
Key: Value

Do not provide any explanations or add any extra information other than this.
""",
    "Bonus Issue": """We have received the following financial record:

{data}

We require the following details (if available):
Company_Name:
Company_Symbol:
Value_Date:
Custodian_ID:
Account_Number:
Settlement_Amount:
Currency:
Tax_Details:
Eligibility:
Debit_Security_Details:
Remarks:
Bonus_Issue_Ratio:
Ex-Date:

If any value is missing in the record, leave it empty.

Please provide the extracted values as key-value pairs in the format:
Key: Value

Do not provide any explanations or add any extra information other than this.
""",
    "Mergers": """We have received the following financial record:

{data}

We require the following details (if available):
Company_Name:
Company_Symbol:
Value_Date:
Custodian_ID:
Account_Number:
Settlement_Amount:
Currency:
Tax_Details:
Eligibility:
Debit_Security_Details:
Remarks:
Ex-Date:
Credit_New_Security_Asset_ID:
Stock_Merger_Ratio:
Dividend_Ratio:

If any value is missing in the record, leave it empty.

Please provide the extracted values as key-value pairs in the format:
Key: Value

Do not provide any explanations or add any extra information other than this.
"""
}






corporate_action_prompt = '''We have received the following financial record:

{data}

Please determine the type of corporate action from the following options:

 Forward Split
 Reverse Split
 Stock Dividend Regular
 Cash Dividend Regular
 Rights Issue
 Bonus Issue
 Mergers

If the record matches one of these corporate actions, return only the corresponding action type. If the record does not match any of the corporate actions, return 'No Corporate Action Found'. If there is more than one matching action, choose the one with the most details provided in the data.

Return only the result, no explanations or extra information.
'''
