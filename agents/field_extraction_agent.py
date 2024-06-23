import openai
import json
import os
from pathlib import Path

# Paths for directories and files
cleaned_text_dir = Path("output/cleaned_text/")
structured_data_dir = Path("output/structured_data/")
log_file = Path("logs/field_extraction_log.txt")

# OpenAI API key
openai.api_key = 'your-openai-api-key'

def read_cleaned_json_files(directory):
    """
    Read all cleaned JSON files from a specified directory.
    """
    json_files = list(directory.glob("*.json"))
    json_data = {}
    for json_file in json_files:
        with json_file.open("r") as f:
            json_data[json_file.stem] = json.load(f)
    return json_data

def extract_fields_with_openai(text):
    """
    Use the OpenAI API to extract specific fields from the provided text.
    """
    prompt = f"""
    Extract the following information from the invoice text:
    - ContactName
    - EmailAddress
    - POAddressLine1
    - POAddressLine2
    - POAddressLine3
    - POAddressLine4
    - POCity
    - PORegion
    - POPostalCode
    - POCountry
    - InvoiceNumber
    - InvoiceDate
    - DueDate
    - InventoryItemCode
    - Description
    - Quantity
    - UnitAmount
    - AccountCode
    - TaxType
    - TrackingName1
    - TrackingOption1
    - TrackingName2
    - TrackingOption2
    - Currency

    Invoice text:
    {text}
    """

    response = openai.Completion.create(
        engine="text-davinci-003",
        prompt=prompt,
        max_tokens=1500,
        n=1,
        stop=None,
        temperature=0.5
    )

    return response.choices[0].text.strip()

def save_structured_data(filename, structured_data):
    """
    Save the extracted fields to a JSON file in the structured_data directory.
    """
    output_path = structured_data_dir / f"{filename}.json"
    with output_path.open("w") as f:
        json.dump(structured_data, f, indent=2)
    print(f"Structured data saved to {output_path}")

def log_processing_status(files):
    """
    Log the processing status of the files.
    """
    with log_file.open("a") as f:
        for file in files:
            f.write(f"Processed: {file}\n")

if __name__ == "__main__":
    # Ensure the output directory exists
    structured_data_dir.mkdir(parents=True, exist_ok=True)
    log_file.parent.mkdir(parents=True, exist_ok=True)

    # Read cleaned JSON files from the cleaned_text directory
    cleaned_data = read_cleaned_json_files(cleaned_text_dir)

    # Extract fields using the OpenAI API
    structured_data = {}
    for filename, data in cleaned_data.items():
        full_text = " ".join([page["text"] for page in data])
        extracted_fields = extract_fields_with_openai(full_text)
        structured_data[filename] = json.loads(extracted_fields)

    # Save the structured data to the structured_data directory
    for filename, data in structured_data.items():
        save_structured_data(filename, data)

    # Log the processing status
    log_processing_status(structured_data.keys())