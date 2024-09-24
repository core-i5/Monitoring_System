import os
import logging
from logging.handlers import RotatingFileHandler
import psutil



def logger_setup(log_file, console_output=False):
    """
    Configures logging with rotating file logs. Log file size is limited to 1MB with a backup count of 5.
    :param log_file: The path of the log file to save logs.
    :param console_output: If True, logs will also be printed to the console.
    """
    logger = logging.getLogger(log_file)  
    logger.setLevel(logging.INFO)

    # Check if the logger already has handlers to avoid adding them multiple times
    if not logger.handlers:
        # File handler for rotating logs
        os.makedirs(os.path.dirname(log_file), exist_ok=True)  
        file_handler = RotatingFileHandler(log_file, maxBytes=1024 * 1024, backupCount=5)
        file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        logger.addHandler(file_handler)

    if console_output:
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        logger.addHandler(console_handler)
        
    return logger


def is_process_running(pid):
    """
    Check if a process with the given PID is running.
    :param pid: Process ID to check.
    :return: True if the process is running, else False.
    """
    pid = int(pid)
    try:
        process = psutil.Process(pid)
        return process.is_running() and process.status() != psutil.STATUS_ZOMBIE
    except Exception as e:
        print(f"Error checking process with PID {pid}: {str(e)}", stack_info=True, exc_info=True)
        return False

