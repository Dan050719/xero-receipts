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
structured_data_dir = project_root / "output/structured_data/"
structured_data_code_dir = project_root / "output/structured_data_code/"
xero_info_file = project_root / "config/xero_info.json"

# OpenAI API key
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

def read_structured_data_files(directory: Path) -> dict:
    """
    Read all structured JSON files from a specified directory.
    """
    json_files = list(directory.glob("*.json"))
    json_data = {}
    for json_file in json_files:
        with json_file.open("r") as f:
            json_data[json_file.stem] = json.load(f)
    return json_data

def read_xero_info(file_path: Path) -> list:
    """
    Read the xero_info.json file.
    """
    with file_path.open("r") as f:
        return json.load(f)

def get_account_code(contact_name: str, xero_info: list, client: OpenAI) -> str:
    """
    Determine the appropriate AccountCode based on the ContactName using AI intuition.
    """
    messages = [
        {"role": "system", "content": "You are a helpful assistant that maps company names to expense codes based on their likely category."},
        {"role": "user", "content": f"""
        Based on the following list of expense categories and codes, determine the most appropriate numerical code for the company "{contact_name}":

        {json.dumps(xero_info, indent=2)}

        The company "{contact_name}" is likely associated with which expense category code? Please provide only the numerical code.
        """}
    ]

    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=messages,
        max_tokens=150,
        temperature=0.5
    )

    content = response.choices[0].message.content.strip()
    print(f"AI response for {contact_name}: {content}")  # Debugging print statement

    # Extract numerical code from response
    for word in content.split():
        if word.isdigit():
            return int(word)
    return "unidentified"

def update_account_codes(structured_data: dict, xero_info: list, client: OpenAI) -> dict:
    """
    Update the AccountCode field in the structured data files based on the ContactName.
    """
    for filename, data in structured_data.items():
        contact_name = data.get("ContactName", "unidentified")
        account_code = get_account_code(contact_name, xero_info, client)
        data["AccountCode"] = account_code
        print(f"Updated {filename} with AccountCode: {account_code}")  # Debugging print statement
    return structured_data

def save_updated_structured_data(directory: Path, structured_data: dict) -> None:
    """
    Save the updated structured data files with AccountCode.
    """
    for filename, data in structured_data.items():
        output_path = directory / f"{filename}.json"
        with output_path.open("w") as f:
            json.dump(data, f, indent=2)
        print(f"Updated structured data saved to {output_path}")

if __name__ == "__main__":
    # Ensure the output directory exists
    structured_data_code_dir.mkdir(parents=True, exist_ok=True)

    # Read structured data files from the structured_data directory
    structured_data = read_structured_data_files(structured_data_dir)

    # Read xero info data
    xero_info = read_xero_info(xero_info_file)

    # Update AccountCode fields in structured data
    updated_structured_data = update_account_codes(structured_data, xero_info, client)

    # Save the updated structured data files to the structured_data_code directory
    save_updated_structured_data(structured_data_code_dir, updated_structured_data)