import os
import time
from pathlib import Path

# Directory to monitor for new PDF uploads
input_dir = Path("input/pdfs/")
# Log file to record paths of new PDF files
log_file = Path("logs/uploaded_files.txt")

def log_new_files(new_files):
    """
    Log the paths of new PDF files to the log file.
    """
    with log_file.open("a") as f:
        for file in new_files:
            f.write(f"{file}\n")
            print(f"Logged new file: {file}")

def monitor_directory():
    """
    Monitor the input directory for new PDF files and log their paths.
    """
    # Set of already known files
    known_files = set()

    while True:
        # Get the current set of PDF files in the directory
        current_files = {str(file) for file in input_dir.glob("*.pdf")}

        # Determine new files by set difference
        new_files = current_files - known_files

        if new_files:
            log_new_files(new_files)
            known_files.update(new_files)

        # Sleep for a short time before checking again
        time.sleep(5)

if __name__ == "__main__":
    # Ensure the log file directory exists
    log_file.parent.mkdir(parents=True, exist_ok=True)

    print(f"Monitoring directory: {input_dir}")
    monitor_directory()