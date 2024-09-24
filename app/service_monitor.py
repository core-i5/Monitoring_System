import sys
import time
import schedule
from utils import logger_setup,is_process_running


def monitor_applications(logger, folder_monitor_pid, todecode_monitor_pid):
    """
    Logs the status of the Folder Monitor and Todecode Monitor applications.
    The log will rotate when the size exceeds 1MB.
    """

    folder_monitor_status = "Running" if is_process_running(folder_monitor_pid) else "Not Running"
    todecode_monitor_status = "Running" if is_process_running(todecode_monitor_pid) else "Not Running"


    logger.info(f"Application 1 (Folder Monitor): {folder_monitor_status}")
    logger.info(f"Application 2 (Todecode Monitor): {todecode_monitor_status}")

    if folder_monitor_status == "Not Running" or todecode_monitor_status == "Not Running":
        logger.warning("One or more applications are not running!")


def start_monitoring_service(folder_monitor_pid, todecode_monitor_pid,log_to_console):
    """
    Starts the monitoring service to log the status of the two applications every 5 minutes.
    """

    logger = logger_setup('logs/app_status.log', log_to_console)

    # Schedule to check the applications' status every 5 minutes
    schedule.every(5).minutes.do(monitor_applications, folder_monitor_pid=folder_monitor_pid, todecode_monitor_pid=todecode_monitor_pid, logger=logger)

    logger.info("Monitoring service started. Logging application status every 5 minutes.")

    try:
        while True:
            schedule.run_pending()
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Monitoring service stopped.")


if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Please provide required PID's.")
        sys.exit(1)

    folder_monitor_pid = sys.argv[1]
    todecode_monitor_pid = sys.argv[2]
    log_to_console = sys.argv[3]
    start_monitoring_service(folder_monitor_pid, todecode_monitor_pid, log_to_console)
