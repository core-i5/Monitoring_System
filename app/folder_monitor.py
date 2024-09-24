import time
import pyzipper
import os
import sys
import pathlib
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from concurrent.futures import ThreadPoolExecutor
from utils import logger_setup

WORKER_TREAD_COUNT = 5

logger = logger_setup('logs/folder_monitor.log')


class TxtFileHandler(FileSystemEventHandler):
    """
    Handler for detecting new .txt files and creating a password-protected zip file.
    """

    def __init__(self, output_folder, executor):
        super().__init__()
        self.output_folder = output_folder
        self.executor = executor

    def on_created(self, event):
        if event.src_path.endswith(".txt"):
            logger.info(f"New txt file detected: {event.src_path}")
            self.executor.submit(self.process_files, event.src_path)

    def process_files(self, file_path):
        try:
            self.create_zip(file_path)
        except Exception as e:
            logger.error(f"Error creating zip file for {file_path}: {str(e)}", stack_info=True, exc_info=True)

    def create_zip(self, file_path):
        """
        Creates a zip file for the given text file with password protection.
        The password is the UTC epoch time.
        """
        epoch_time = int(time.time())
        txt_file_name = os.path.basename(file_path).replace(".txt", "")
        zip_name = f"{txt_file_name}_{time.strftime('%Y_%m_%d_%I_%M_%S_%p', time.gmtime())}.zip"
    
        zip_tmp_path = os.path.join(self.output_folder, zip_name + ".tmp")  # Write to a temporary file

        # Use pyzipper to create a password-protected zip file
        with pyzipper.AESZipFile(zip_tmp_path, 'w', compression=pyzipper.ZIP_DEFLATED, encryption=pyzipper.WZ_AES) as zipf:
            zipf.setpassword(bytes(str(epoch_time), 'utf-8'))
            zipf.write(file_path, os.path.basename(file_path))
        
        # After writing, rename the temporary file to the final .zip extension
        zip_final_path = os.path.join(self.output_folder, zip_name)
        os.rename(zip_tmp_path, zip_final_path)
        logger.info(f"Created zip file: {zip_final_path}")

        # Manually trigger a file creation event by updating the modification time
        pathlib.Path(zip_final_path).touch()  


def start_folder_monitor(input_folder):
    """
    Starts the folder monitor service to detect new .txt files and zip them.
    :param input_folder: The folder to monitor for new .txt files.
    """
    output_folder = "todecode"  
    os.makedirs(output_folder, exist_ok=True)

    with ThreadPoolExecutor(max_workers=WORKER_TREAD_COUNT) as executor:
        event_handler = TxtFileHandler(output_folder, executor)
        observer = Observer()
        observer.schedule(event_handler, input_folder, recursive=False)
        observer.start()

        logger.info(f"Folder monitor started. Monitoring folder: {input_folder}")

        try:
            while True:
                time.sleep(1)
        except Exception as e:
            logger.error(f"Error in Folder Monitor: {str(e)}", stack_info=True, exc_info=True)
            observer.stop()

        observer.join()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Please provide input folder.")
        sys.exit(1)

    input_folder = sys.argv[1]
    start_folder_monitor(input_folder)
