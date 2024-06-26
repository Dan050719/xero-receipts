import imaplib
import email
from email.header import decode_header
import os
from pathlib import Path
import pdfkit
from dotenv import load_dotenv
from datetime import datetime

# Load environment variables from .env file
load_dotenv()

EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS")
APP_PASSWORD = os.getenv("APP_PASSWORD")

# Define the project root and output directories
project_root = Path(__file__).resolve().parent.parent  # Move up one level to the project root
attachments_folder = project_root / "input/emails/emails_attachments"
pdf_folder = project_root / "input/emails/emails_pdfs"
text_folder = project_root / "input/emails/emails_txt"

# Create directories if they do not exist
attachments_folder.mkdir(parents=True, exist_ok=True)
pdf_folder.mkdir(parents=True, exist_ok=True)
text_folder.mkdir(parents=True, exist_ok=True)

print(f"Attachments folder exists: {attachments_folder.exists()}")
print(f"PDF folder exists: {pdf_folder.exists()}")
print(f"Text folder exists: {text_folder.exists()}")

# Configure pdfkit
path_wkhtmltopdf = '/usr/local/bin/wkhtmltopdf'  # Adjust this path if necessary
config = pdfkit.configuration(wkhtmltopdf=path_wkhtmltopdf)

# Connect to your email server
imap = imaplib.IMAP4_SSL("imap.gmail.com")

# Use your app password here
imap.login(EMAIL_ADDRESS, APP_PASSWORD)

imap.select("inbox")

# Search for all emails
status, messages = imap.search(None, "ALL")
email_ids = messages[0].split()

for email_id in email_ids:
    # Fetch the email by ID
    res, msg = imap.fetch(email_id, "(RFC822)")

    for response in msg:
        if isinstance(response, tuple):
            # Parse the email
            msg = email.message_from_bytes(response[1])
            # Decode the email subject
            subject, encoding = decode_header(msg["Subject"])[0]
            if isinstance(subject, bytes):
                subject = subject.decode(encoding if encoding else "utf-8")
            
            # Create a valid filename with a unique identifier
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            filename = f"{timestamp}_{''.join([c if c.isalnum() else '_' for c in subject])}"

            # Save the email content to a text file
            email_text_file = text_folder / f"{filename}.txt"
            email_pdf_file = pdf_folder / f"{filename}.pdf"

            print(f"Processing email: {filename}")

            body = None

            if msg.is_multipart():
                for part in msg.walk():
                    content_type = part.get_content_type()
                    content_disposition = str(part.get("Content-Disposition"))

                    if "attachment" in content_disposition:
                        # Download attachment
                        attachment_filename = part.get_filename()
                        if attachment_filename:
                            attachment_path = attachments_folder / f"{timestamp}_{attachment_filename}"
                            try:
                                with open(attachment_path, "wb") as f:
                                    f.write(part.get_payload(decode=True))
                                print(f"Saved attachment: {attachment_path}")
                            except IOError as e:
                                print(f"Error saving attachment {attachment_path}: {e}")
                    elif content_type == "text/plain":
                        try:
                            body = part.get_payload(decode=True).decode('utf-8')
                        except UnicodeDecodeError:
                            try:
                                body = part.get_payload(decode=True).decode('latin1')
                            except UnicodeDecodeError:
                                print(f"Failed to decode part of email: {filename}")
                                continue
            else:
                try:
                    body = msg.get_payload(decode=True).decode('utf-8')
                except UnicodeDecodeError:
                    try:
                        body = msg.get_payload(decode=True).decode('latin1')
                    except UnicodeDecodeError:
                        print(f"Failed to decode email: {filename}")
                        continue

            if body:
                try:
                    with open(email_text_file, "w") as f:
                        f.write(body)
                    print(f"Saved email text: {email_text_file}")
                except IOError as e:
                    print(f"Error saving text file {email_text_file}: {e}")

                # Convert the text file to PDF
                try:
                    pdfkit.from_file(str(email_text_file), str(email_pdf_file), configuration=config)
                    print(f"Converted to PDF: {email_pdf_file}")
                except Exception as e:
                    print(f"Failed to convert {email_text_file} to PDF: {e}")

                print(f"Text file exists: {email_text_file.exists()}")
                print(f"PDF file exists: {email_pdf_file.exists()}")

# Logout and close the connection
imap.logout()