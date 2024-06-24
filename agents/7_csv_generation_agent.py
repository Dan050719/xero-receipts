import json
import csv
import os
from pathlib import Path

# Paths for directories and files
validated_data_dir = Path("output/validated_data/")
final_csv_dir = Path("output/final_csv/")
log_file = Path("logs/csv_generation_log.txt")

# Xero template headers
xero_headers = [
    "ContactName", "EmailAddress", "POAddressLine1", "POAddressLine2", "POAddressLine3",
    "POAddressLine4", "POCity", "PORegion", "POPostalCode", "POCountry", "InvoiceNumber",
    "InvoiceDate", "DueDate", "InventoryItemCode", "Description", "Quantity", "UnitAmount",
    "AccountCode", "TaxType", "TrackingName1", "TrackingOption1", "TrackingName2", "TrackingOption2",
    "Currency"
]

def read_validated_json_files(directory):
    """
    Read all validated JSON files from a specified directory.
    """
    json_files = list(directory.glob("*.json"))
    json_data = {}
    for json_file in json_files:
        with json_file.open("r") as f:
            json_data[json_file.stem] = json.load(f)
    return json_data

def convert_to_csv(data, filename):
    """
    Convert the validated data to a CSV file following the Xero template.
    """
    csv_path = final_csv_dir / f"{filename}.csv"
    with csv_path.open("w", newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=xero_headers)
        writer.writeheader()
        for entry in data:
            writer.writerow(entry)
    print(f"CSV file saved to {csv_path}")

def log_processing_status(files):
    """
    Log the processing status of the files.
    """
    with log_file.open("a") as f:
        for file in files:
            f.write(f"Processed: {file}\n")

if __name__ == "__main__":
    # Ensure the output directory exists
    final_csv_dir.mkdir(parents=True, exist_ok=True)
    log_file.parent.mkdir(parents=True, exist_ok=True)

    # Read validated JSON files from the validated_data directory
    validated_data = read_validated_json_files(validated_data_dir)

    # Convert the validated data to CSV files following the Xero template
    for filename, data in validated_data.items():
        convert_to_csv(data, filename)

    # Log the processing status
    log_processing_status(validated_data.keys())