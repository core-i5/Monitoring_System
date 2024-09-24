import pyzipper
import os
import glob
import sys
import re
import time
import calendar
from queue import Queue
from threading import Thread
from utils import logger_setup
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

logger = logger_setup('logs/todecode_monitor.log')


class ZipFileHandler(FileSystemEventHandler):
    """
    Handler for detecting new zip files, unzipping them, and applying PII filtering.
    """

    def __init__(self, output_folder, input_folder, processing_queue):
        super().__init__()
        self.output_folder = output_folder
        self.input_folder = input_folder
        self.processing_queue = processing_queue

    def on_modified(self, event):
        if event.src_path.endswith(".zip"):
            logger.info(f"Modified zip file detected: {event.src_path}")
            self.processing_queue.put(event.src_path)

    def on_created(self, event):
        if event.src_path.endswith(".zip"):
            logger.info(f"New zip file detected: {event.src_path}")
            self.processing_queue.put(event.src_path)

    def process_files(self):
        while True:
            zip_file_path = self.processing_queue.get()
            if zip_file_path is None:
                break  # Graceful exit
            try:
                # Ensure the file is not being written to (i.e., not locked)
                if self.is_file_locked(zip_file_path):
                    time.sleep(1)
                    continue  # Wait and retry if the file is locked
                self.extract_and_filter(zip_file_path)
                os.remove(zip_file_path)
            except Exception as e:
                logger.error(f"Error extracting and filtering zip file {zip_file_path}: {str(e)}", stack_info=True, exc_info=True)
            self.processing_queue.task_done()

    def extract_and_filter(self, zip_file):
        """
        Extracts the zip file and applies PII filtering on the text content.
        """
        password = self.extract_password(zip_file)

        try:
            with pyzipper.AESZipFile(zip_file, 'r') as zf:
                zf.pwd = bytes(password, 'utf-8')
                zf.extractall(self.input_folder)

        except RuntimeError as e:
            logger.error(f"Error during extraction: {e} password:{password}", stack_info=True, exc_info=True)
        except Exception as e:
            logger.error(f"An unexpected error occurred: {e}", stack_info=True, exc_info=True)

        txt_files = glob.glob(os.path.join(self.input_folder, "*.txt"))

        for txt_file_path in txt_files:
            self.pii_filter(txt_file_path)

    def pii_filter(self, file_path):
        """
        Filters out PII information from file paths and content such as:
        - File paths
        - Dates
        - Phone numbers
        - Social media accounts (Twitter, LinkedIn, Instagram, Facebook, GitHub)
        - Email addresses
        """
        with open(file_path, 'r') as file:
            content = file.read()

        # Patterns to filter out various forms of PII
        patterns = {
            # File paths like "C:\Users\username"
            "file_paths": r"[A-Z]:\\Users\\\w+",
            # Email addresses
            "emails": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b",
            # Phone numbers (e.g., (123) 456-7890, 123-456-7890, +1-234-567-8900)
            "phone_numbers": r"\b(?:\+?(\d{1,3})?[-.\s]?)?(?:\(?(\d{3})\)?[-.\s]?)?(\d{3})[-.\s]?(\d{4})\b",
            # Dates (e.g., 12/25/2023, 25-12-2023, Dec 25, 2023, 25th December 2023)
            "dates": r"\b(\d{1,2}[-/th|st|nd|rd\s]*[A-Za-z]{3,9}[-/\s]*\d{2,4}|\d{1,2}[-/]\d{1,2}[-/]\d{2,4}|[A-Za-z]{3,9} \d{1,2}(?:th|st|nd|rd)?, \d{4})\b",
            # Social media patterns
            "twitter": r"@([A-Za-z0-9_]{1,15})",  # Twitter handles
            "linkedin": r"https?://(www\.)?linkedin\.com/in/[A-Za-z0-9_-]+",  # LinkedIn URLs
            "instagram": r"@([A-Za-z0-9_.]{1,30})|https?://(www\.)?instagram\.com/[A-Za-z0-9_.]+",  # Instagram handles or URLs
            "facebook": r"https?://(www\.)?facebook\.com/[A-Za-z0-9_.]+",  # Facebook URLs
            "github": r"https?://(www\.)?github\.com/[A-Za-z0-9_-]+",  # GitHub URLs
            # Physical addresses (simple example, could be refined)
            "addresses": r"\b\d{1,4}\s[A-Za-z0-9\s]+(?:St|Street|Ave|Avenue|Blvd|Boulevard|Rd|Road|Lane|Ln|Dr|Drive|Ct|Court)\b",
        }

        # Replace matches with generic placeholders
        replacements = {
            "file_paths": r"<drive>:\\Users\\<username>",
            "emails": r"<email>",
            "phone_numbers": r"<phone_number>",
            "dates": r"<date>",
            "twitter": r"<twitter_handle>",
            "linkedin": r"<linkedin_profile>",
            "instagram": r"<instagram_handle>",
            "facebook": r"<facebook_profile>",
            "github": r"<github_profile>",
            "addresses": r"<address>",
        }

        for key, pattern in patterns.items():
            content = re.sub(pattern, replacements[key], content)

        filtered_file = os.path.join(self.output_folder, f"PII_filtered_{os.path.basename(file_path)}")
        with open(filtered_file, 'w') as file:
            file.write(content)

        os.remove(file_path)

        logger.info(f"PII filtered file created: {filtered_file}")

    def extract_password(self, file_path):
        """
        Extracts the password from the zip file's name. The password is derived from the timestamp 
        in the file name (format: YYYY_MM_DD_HH_MM_SS_AM/PM).
        """
        zip_file_name = os.path.basename(file_path)
        
        # Use regex to extract the timestamp from the file name
        match = re.search(r'(\d{4}_\d{2}_\d{2}_\d{2}_\d{2}_\d{2}_[AP]M)', zip_file_name)
        
        if match:
            timestamp_part = match.group(1)  
            parsed_time = time.strptime(timestamp_part, "%Y_%m_%d_%I_%M_%S_%p")        
            epoch_time_password = int(calendar.timegm(parsed_time))
            
            return str(epoch_time_password)
        else:
            logger.error(f"Timestamp not found in the zip file name: {zip_file_name}", stack_info=True, exc_info=True)


    def is_file_locked(self, file_path):
        """
        Check if the file is still being written (locked).
        Returns True if the file is locked, False otherwise.
        """
        try:
            with open(file_path, 'rb'):
                pass
        except OSError:
            return True
        return False


def start_todecode_monitor(output_folder):
    """
    Starts the todecode folder monitor to unzip files and apply PII filtering.
    :param output_folder: The folder where filtered files will be stored.
    """
    input_folder = "todecode"
    os.makedirs(input_folder, exist_ok=True)

    processing_queue = Queue()

    event_handler = ZipFileHandler(output_folder, input_folder, processing_queue)
    observer = Observer()
    observer.schedule(event_handler, input_folder, recursive=False)
    observer.start()

    # Start processing thread
    processing_thread = Thread(target=event_handler.process_files, daemon=True)
    processing_thread.start()

    logger.info(f"Todecode folder monitor started. Monitoring folder: {input_folder}")

    try:
        while True:
            time.sleep(1)
    except Exception as e:
        logger.error(f"Error in Todecode Monitor: {str(e)}", stack_info=True, exc_info=True)
        observer.stop()

    processing_queue.put(None)  # Signal thread to stop
    processing_thread.join()
    observer.join()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Please provide output folder.")
        sys.exit(1)

    output_folder = sys.argv[1]
    start_todecode_monitor(output_folder)
