import fitz  # PyMuPDF
import pytesseract
import json
import os
from pathlib import Path

# Set the project root directory
project_root = Path(__file__).resolve().parent.parent

# Paths for directories and files
uploaded_files_log = project_root / "logs/uploaded_files.txt"
extracted_text_dir = project_root / "output/extracted_text/"

def read_uploaded_files():
    """
    Read the list of PDF file paths from the log file.
    """
    if not uploaded_files_log.exists():
        return []

    with uploaded_files_log.open("r") as f:
        file_paths = f.read().splitlines()
    
    return file_paths

def perform_ocr(pdf_path):
    """
    Perform OCR on a PDF file and return the extracted text with coordinates.
    """
    document = fitz.open(pdf_path)
    ocr_results = []

    for page_num in range(len(document)):
        page = document.load_page(page_num)
        text = page.get_text("text")
        blocks = page.get_text("blocks")

        page_data = {
            "page_num": page_num + 1,
            "text": text,
            "blocks": []
        }

        for block in blocks:
            x0, y0, x1, y1, block_text = block[:5]
            page_data["blocks"].append({
                "x0": x0,
                "y0": y0,
                "x1": x1,
                "y1": y1,
                "text": block_text
            })
        
        ocr_results.append(page_data)

    return ocr_results

def save_ocr_results(pdf_path, ocr_results):
    """
    Save the OCR results to a JSON file in the extracted_text directory.
    The JSON file is named after the PDF file.
    """
    pdf_name = Path(pdf_path).stem
    json_path = extracted_text_dir / f"{pdf_name}.json"

    with json_path.open("w") as f:
        json.dump(ocr_results, f, indent=2)

    print(f"OCR results saved to {json_path}")

def mark_files_as_processed(processed_files):
    """
    Mark the processed files in the log file to avoid reprocessing.
    """
    with uploaded_files_log.open("w") as f:
        for file in processed_files:
            f.write(f"{file}\n")

if __name__ == "__main__":
    # Ensure the output directory exists
    extracted_text_dir.mkdir(parents=True, exist_ok=True)

    # Read the list of PDF file paths from the log file
    pdf_files = read_uploaded_files()

    if not pdf_files:
        print("No PDF files to process.")
    else:
        processed_files = []
        for pdf_path in pdf_files:
            try:
                print(f"Processing file: {pdf_path}")
                # Perform OCR on the PDF file
                ocr_results = perform_ocr(pdf_path)
                # Save the OCR results to a JSON file
                save_ocr_results(pdf_path, ocr_results)
                # Add the file to the list of processed files
                processed_files.append(pdf_path)
            except Exception as e:
                print(f"Failed to process {pdf_path}: {e}")

        # Mark the processed files in the log file
        mark_files_as_processed(processed_files)