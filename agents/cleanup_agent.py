import json
import os
from pathlib import Path

# Paths for directories and files
user_info_file = Path("config/user_info.json")
extracted_text_dir = Path("output/extracted_text/")
cleaned_text_dir = Path("output/cleaned_text/")
log_file = Path("logs/cleanup_log.txt")

def load_user_info():
    """
    Load user-specific information from the user_info.json file.
    """
    with user_info_file.open("r") as f:
        user_info = json.load(f)
    return user_info

def read_json_files(directory):
    """
    Read all JSON files from a specified directory.
    """
    json_files = list(directory.glob("*.json"))
    json_data = {}
    for json_file in json_files:
        with json_file.open("r") as f:
            json_data[json_file.stem] = json.load(f)
    return json_data

def filter_irrelevant_data(data, emails, addresses):
    """
    Filter out irrelevant data such as user-specific emails and addresses.
    """
    filtered_data = []
    for page in data:
        filtered_page = {
            "page_num": page["page_num"],
            "text": "",
            "blocks": []
        }
        for block in page["blocks"]:
            text = block["text"]
            if not any(email in text for email in emails) and not any(address in text for address in addresses):
                filtered_page["text"] += text + " "
                filtered_page["blocks"].append(block)
        filtered_data.append(filtered_page)
    return filtered_data

def save_cleaned_data(data, output_dir):
    """
    Save the cleaned data to a JSON file in the cleaned_text directory.
    """
    for filename, content in data.items():
        output_path = output_dir / f"{filename}.json"
        with output_path.open("w") as f:
            json.dump(content, f, indent=2)
        print(f"Cleaned data saved to {output_path}")

def log_processing_status(files):
    """
    Log the processing status of the files.
    """
    with log_file.open("a") as f:
        for file in files:
            f.write(f"Processed: {file}\n")

if __name__ == "__main__":
    # Ensure the output directory exists
    cleaned_text_dir.mkdir(parents=True, exist_ok=True)
    log_file.parent.mkdir(parents=True, exist_ok=True)

    # Load user-specific information
    user_info = load_user_info()
    emails = user_info["emails"]
    addresses = user_info["addresses"]

    # Read JSON files from the extracted_text directory
    json_data = read_json_files(extracted_text_dir)

    # Filter out irrelevant data
    cleaned_data = {}
    for filename, data in json_data.items():
        cleaned_data[filename] = filter_irrelevant_data(data, emails, addresses)

    # Save the cleaned data to the cleaned_text directory
    save_cleaned_data(cleaned_data, cleaned_text_dir)

    # Log the processing status
    log_processing_status(cleaned_data.keys())