import os
import json
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables from .env file
load_dotenv()

# Set the project root directory
project_root = Path(__file__).resolve().parent.parent

# Paths for directories and files
cleaned_text_dir = project_root / "output/cleaned_text/"
structured_data_dir = project_root / "output/structured_data/"
structured_data_code_dir = project_root / "output/structured_data_code/"
log_file = project_root / "logs/field_extraction_log.txt"

# OpenAI API key
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

def read_cleaned_json_files(directory: Path) -> dict:
    """
    Read all cleaned JSON files from a specified directory.
    """
    json_files = list(directory.glob("*.json"))
    json_data = {}
    for json_file in json_files:
        with json_file.open("r") as f:
            json_data[json_file.stem] = json.load(f)
    return json_data

def is_valid_person_name(name: str) -> bool:
    """
    Determine if the given name is likely a person's name.
    """
    # Define some simple rules to identify a person's name
    # This can be enhanced with more sophisticated checks if needed
    if any(word in name.lower() for word in ["inc", "corp", "llc", "ltd", "gmbh", "co", "company"]):
        return False
    if len(name.split()) > 1:
        return True
    return False

def extract_fields_with_openai(client: OpenAI, text: str) -> dict:
    """
    Use the OpenAI API to extract specific fields from the provided text.
    """
    messages = [
        {"role": "system", "content": "You are a helpful assistant that can extract structured information from unstructured text."},
        {"role": "user", "content": f"""
        Extract the following information from the receipt text. The ContactName field must be populated with the company name if no valid person's name is identified. If the company name cannot be identified, use "unidentified":
        - ContactName
        - EmailAddress (if available)
        - POAddressLine1 (if available)
        - POAddressLine2 (if available)
        - POAddressLine3 (if available)
        - POAddressLine4 (if available)
        - POCity (if available)
        - PORegion (if available)
        - POPostalCode (if available)
        - POCountry (if available)
        - InvoiceNumber
        - InvoiceDate
        - DueDate (if available)
        - InventoryItemCode (if available)
        - Description
        - Quantity (if available, otherwise default to 1)
        - UnitAmount
        - AccountCode (if available)
        - TaxType
        - TrackingName1 (if available)
        - TrackingOption1 (if available)
        - TrackingName2 (if available)
        - TrackingOption2 (if available)
        - Currency

        Receipt text:
        {text}
        """}
    ]

    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=messages,
        max_tokens=1500,
        temperature=0.5
    )

    # Log the response for debugging
    print(f"API response: {response}")

    # Access the content from the response object correctly
    content = response.choices[0].message.content.strip()

    # Log the content for debugging
    print(f"Extracted content: {content}")

    # Manually parse the content and clean up keys
    extracted_data = {}
    company_identified = False
    for line in content.split('\n'):
        if ': ' in line:
            key, value = line.split(': ', 1)
            clean_key = key.strip().lstrip('-').strip()
            clean_value = value.strip()

            # Handle ContactName specifically
            if clean_key == "ContactName" and clean_value.lower() in ["not available", "not provided"]:
                continue
            elif clean_key == "ContactName" and is_valid_person_name(clean_value):
                extracted_data["ContactName"] = clean_value
                company_identified = True
            elif clean_key == "Description" and not company_identified:
                extracted_data["ContactName"] = clean_value
                company_identified = True

            extracted_data[clean_key] = clean_value

    # Ensure ContactName is present
    if "ContactName" not in extracted_data:
        extracted_data["ContactName"] = "unidentified"

    # Default Quantity to 1 if not identified
    if "Quantity" not in extracted_data or extracted_data["Quantity"].lower() in ["not available", "not provided"]:
        extracted_data["Quantity"] = "1"

    # Set currency to AUD
    extracted_data["Currency"] = "AUD"

    # Set unidentified fields to "unidentified"
    for field in ["EmailAddress", "POAddressLine1", "POAddressLine2", "POAddressLine3", "POAddressLine4",
                  "POCity", "PORegion", "POPostalCode", "POCountry", "DueDate", "InventoryItemCode",
                  "AccountCode", "TrackingName1", "TrackingOption1", "TrackingName2", "TrackingOption2"]:
        if field not in extracted_data:
            extracted_data[field] = "unidentified"

    return extracted_data

def save_structured_data(filename: str, structured_data: dict) -> None:
    """
    Save the extracted fields to a JSON file in the structured_data directory.
    """
    output_path = structured_data_dir / f"{filename}.json"
    with output_path.open("w") as f:
        json.dump(structured_data, f, indent=2)
    print(f"Structured data saved to {output_path}")

def log_processing_status(files: list) -> None:
    """
    Log the processing status of the files.
    """
    with log_file.open("a") as f:
        for file in files:
            f.write(f"Processed: {file}\n")

def update_account_code(structured_data: dict, company: str, xero_info: list) -> dict:
    """
    Update the AccountCode based on the company name and Xero information.
    """
    account_code = "unidentified"
    for item in xero_info:
        if company.lower() in item['Name'].lower():
            account_code = item['Code']
            break
    structured_data["AccountCode"] = account_code
    return structured_data

def read_xero_info(file_path: Path) -> list:
    """
    Read the Xero information from the JSON file.
    """
    with file_path.open("r") as f:
        return json.load(f)

if __name__ == "__main__":
    # Ensure the output directory exists
    structured_data_dir.mkdir(parents=True, exist_ok=True)
    structured_data_code_dir.mkdir(parents=True, exist_ok=True)
    log_file.parent.mkdir(parents=True, exist_ok=True)

    # Read cleaned JSON files from the cleaned_text directory
    cleaned_data = read_cleaned_json_files(cleaned_text_dir)

    # Read Xero info from the config file
    xero_info_file = project_root / "config/xero_info.json"
    xero_info = read_xero_info(xero_info_file)

    # Extract fields using the OpenAI API and update account codes
    structured_data = {}
    for filename, data in cleaned_data.items():
        full_text = " ".join([page["text"] for page in data])
        extracted_fields = extract_fields_with_openai(client, full_text)
        updated_fields = update_account_code(extracted_fields, extracted_fields["ContactName"], xero_info)
        structured_data[filename] = updated_fields

    # Save the structured data to the structured_data directory
    for filename, data in structured_data.items():
        save_structured_data(filename, data)

    # Log the processing status
    log_processing_status(list(structured_data.keys()))