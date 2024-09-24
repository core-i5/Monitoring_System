# Monitoring System

The **Monitoring System** consists of three core services: `folder_monitor`, `todecode_monitor`, and `service_monitor`, along with a management service `manage_monitor_app` for controlling the entire system. This utility manages the execution and termination of all services.

## Overview

### `folder_monitor`

The `folder_monitor` service watches a designated directory for new `.txt` files. When a file is detected:

1. A password-protected zip file is created, using the **UTC epoch time** as the password.
2. The zip file is named according to the format `YYYY_MM_DD_hh_mm_ss_am/pm.zip` (e.g., `2020_08_24_7_24_32_pm.zip`).
   - You can reference UTC epoch time at [Epoch Converter](https://www.epochconverter.com/).
3. The zip file is saved into the `todecode` folder (which is created if it does not already exist).
4. Any previously existing files in the `todecode` folder are deleted, retaining only the latest zip.

### `todecode_monitor`

The `todecode_monitor` service listens to the `todecode` folder for new zip files. Upon detecting a zip file:

1. The service extracts the file using the password (derived from the file name).
2. It applies **PII (Personally Identifiable Information)** filtering to the extracted file’s contents.
3. The filtered contents are saved as `PII_filtered_<original_name>.txt`, ensuring any sensitive information in the `file_path` is masked. For example:
   - `"file_path" : "C:\\Users\\john\\xyz"` is converted to `"file_path" : "<d>:\\Users\\<u>\\xyz"`.
4. If no PII is detected, the original file path remains unchanged.

### `service_monitor`

The `service_monitor` service tracks the health and status of both the `folder_monitor` and `todecode_monitor` services, ensuring they are up and running. It writes the status logs to rotating files (up to 1 MB each) every 5 minutes.

- Logs are stored in the `logs` directory under `applications_status`.

### `select_folder`

The `select_folder` utility, powered by `tkinter`, provides a GUI dialog box to help users select the directories for monitoring and output.

## Pre-requisites

- **Python 3.10** or higher.

## Installation and Setup

1. Clone the repository:
   ```bash
   git clone <repo-link>
   ```

2. Navigate to the project directory:
   ```bash
   cd ~/Monitoring_System
   ```

3. Install project dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Important Commands

### Start All Services
```bash
python3 manage_monitor_app.py
```

### Stop All Services
```bash
python3 manage_monitor_app.py --stop
```

### Run and Print Status Logs in Real-time
```bash
python3 manage_monitor_app.py --log
```

### Run test case
```bash
python -m unittest discover -s test -p tests
```

## How It Works

Upon running the project, a graphical dialog box will appear to let the user select two directories:

1. A folder to monitor for new `.txt` files.
2. An output folder where processed files will be saved.

**Note:** Input and output directories must be different.

Once the directories are selected, all services begin their respective operations as described.

## Folder Structure

```
monitoring_system/
  app/
    folder_monitor.py
    todecode_monitor.py
    service_monitor.py
    select_folder.py
    utils.py
  logs/
  test/
  manage_monitor_app.py
```

## Technologies and Modules Used

- **`psutil`**: Monitors and manages the status of running processes.
- **`watchdog`**: Detects and handles filesystem events.
- **`Thread`**: Manages concurrent tasks using multithreading.
- **`Queue`**: Manages tasks with in worker thread.
- **`pyzipper`**: Used for creating and extracting password-protected zip files.
- **`logging`**: Logs service statuses and exceptions, supporting rotating log files.
- **`subprocess`**: Manages the execution of external services in the management application.
- **`re`**: Facilitates the creation of PII filters using regular expressions.
- **`time` & `calendar`**: Handles UTC epoch conversions for file naming and password generation.
- **`tkinter`**: Provides a GUI for folder selection.
- **`unittest`**: Used for writing and managing unit tests to ensure code reliability.

## Area of Improvement

- The **PII filtering** functionality can be enhanced for more specific use cases. Currently, basic PII filters have been implemented based on general assumptions.
- There may be unhandled edge cases or scenarios in the current system. If you encounter any, please report them, and I'll address the issue in a future update.
