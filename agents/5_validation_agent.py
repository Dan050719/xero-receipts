import json
import os
from pathlib import Path

# Set the project root directory
project_root = Path(__file__).resolve().parent.parent

# Paths for directories and files
structured_data_dir = project_root / "output/structured_data/"
validated_data_dir = project_root / "output/validated_data/"
log_file = project_root / "logs/validation_log.txt"

def read_structured_json_files(directory):
    """
    Read all structured JSON files from a specified directory.
    """
    json_files = list(directory.glob("*.json"))
    json_data = {}
    for json_file in json_files:
        with json_file.open("r") as f:
            json_data[json_file.stem] = json.load(f)
    return json_data

def validate_data(data):
    """
    Validate the extracted fields for accuracy and completeness.
    """
    required_fields = [
        "ContactName", "EmailAddress", "POAddressLine1", "POCity", "PORegion",
        "POPostalCode", "POCountry", "InvoiceNumber", "InvoiceDate", "DueDate",
        "InventoryItemCode", "Description", "Quantity", "UnitAmount",
        "AccountCode", "TaxType", "Currency"
    ]
    errors = []
    for field in required_fields:
        if field not in data or not data[field]:
            errors.append(f"Missing or empty field: {field}")

    return errors

def save_validated_data(filename, data):
    """
    Save the validated data to a JSON file in the validated_data directory.
    """
    output_path = validated_data_dir / f"{filename}.json"
    with output_path.open("w") as f:
        json.dump(data, f, indent=2)
    print(f"Validated data saved to {output_path}")

def log_validation_errors(filename, errors):
    """
    Log any validation errors or discrepancies for manual review.
    """
    with log_file.open("a") as f:
        f.write(f"Validation errors for {filename}:\n")
        for error in errors:
            f.write(f"  - {error}\n")
        f.write("\n")

if __name__ == "__main__":
    # Ensure the output directory exists
    validated_data_dir.mkdir(parents=True, exist_ok=True)
    log_file.parent.mkdir(parents=True, exist_ok=True)

    # Read structured JSON files from the structured_data directory
    structured_data = read_structured_json_files(structured_data_dir)

    # Validate the data and save the validated data
    for filename, data in structured_data.items():
        print(f"Validating file: {filename}")
        validation_errors = validate_data(data)
        if validation_errors:
            log_validation_errors(filename, validation_errors)
        else:
            save_validated_data(filename, data)