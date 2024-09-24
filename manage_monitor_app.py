import os
import subprocess
import sys
import time
import json
import signal
import psutil
from app.select_folder import select_folders
from app.utils import is_process_running

FOLDER_MONITOR = "app/folder_monitor.py"
TODECODE_MONITOR = "app/todecode_monitor.py"
SERVICE_MONITOR = "app/service_monitor.py"
LOG_FILE = "logs/app_status.log"
PID_FILE = 'pids.json'

folder_proc = None
todecode_proc = None
service_proc = None

def save_pids(folder_proc_pid=None, todecode_proc_pid=None, service_proc_pid=None):
    pids_data = {
        "folder_proc_pid": folder_proc_pid,
        "todecode_proc_pid": todecode_proc_pid,
        "service_proc_pid": service_proc_pid
    }
    with open(PID_FILE, 'w') as f:
        json.dump(pids_data, f)
    time.sleep(1)  # Small delay to ensure the file is written properly

def get_pids():
    try:
        with open(PID_FILE, 'r') as f:
            pids_data = json.load(f)
        folder_pid = int(pids_data.get("folder_proc_pid"))
        todecode_pid = int(pids_data.get("todecode_proc_pid"))
        service_pid = int(pids_data.get("service_proc_pid"))
        return folder_pid, todecode_pid, service_pid
    except (FileNotFoundError, ValueError):
        return None, None, None

def start_services(log_to_console=False):
    global folder_proc, todecode_proc, service_proc

    input_folder, output_folder = select_folders()

    if not input_folder or not output_folder:
        print("Folders not selected. Exiting.")
        sys.exit(1)

    folder_proc = subprocess.Popen([sys.executable, FOLDER_MONITOR, input_folder])
    todecode_proc = subprocess.Popen([sys.executable, TODECODE_MONITOR, output_folder])
    service_proc = subprocess.Popen([sys.executable, SERVICE_MONITOR, str(folder_proc.pid), str(todecode_proc.pid), str(log_to_console)])

    save_pids(folder_proc.pid, todecode_proc.pid, service_proc.pid)

def stop_services():
    folder_proc_pid, todecode_proc_pid, service_proc_pid = get_pids()

    if folder_proc_pid is None or todecode_proc_pid is None or service_proc_pid is None:
        print("No service running!")
        sys.exit(0)

    def terminate_proc(pid):
        """Gracefully terminate a process by its PID using psutil."""
        try:
            process = psutil.Process(pid)
            process.terminate()
            process.wait(timeout=5)
            print(f"Process with PID {pid} terminated gracefully.")
        except psutil.NoSuchProcess:
            print(f"No process with PID {pid} found.")
        except psutil.TimeoutExpired:
            print(f"Process with PID {pid} did not terminate in time.")
        except Exception as e:
            print(f"Error terminating process with PID {pid}: {str(e)}")

    terminate_proc(folder_proc_pid)
    terminate_proc(todecode_proc_pid)
    terminate_proc(service_proc_pid)
    
    print("All services terminated.")
    
    if os.path.exists(PID_FILE):
        os.remove(PID_FILE) 

    sys.exit(0)

def handle_keyboard_interrupt(signum, frame):
    print("\nKeyboard interrupt received. Stopping all services...")
    stop_services()
    sys.exit(0)

def main():
    signal.signal(signal.SIGINT, handle_keyboard_interrupt)  # Handle Ctrl+C
    signal.signal(signal.SIGTSTP, handle_keyboard_interrupt)  # Handle Ctrl+Z

    if "--stop" in sys.argv:
        if are_services_running():
            stop_services()
        else:
            print("No service running!")
    elif "--log" in sys.argv:
        if are_services_running():
            print("All services are already running")
        else:
            print("Starting all services and printing logs...")
            start_services(log_to_console=True)
    else:
        print("Starting all services...")
        start_services()

def are_services_running():
    folder_proc_pid, todecode_proc_pid, service_proc_pid = get_pids()

    if folder_proc_pid and todecode_proc_pid and service_proc_pid:
        if is_process_running(folder_proc_pid) and is_process_running(todecode_proc_pid) and is_process_running(service_proc_pid):
            return True
    return False

if __name__ == "__main__":
    main()
