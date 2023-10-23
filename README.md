# FRITZ!Box Log Saver

![GitHub license](https://img.shields.io/badge/license-MIT-blue.svg)

## Description

"FRITZ!Box Log Saver" is a Python application that allows you to log in to a FRITZ!Box device, retrieve the event log data, and save it to a CSV file. This tool simplifies the process of accessing and saving log data from your FRITZ!Box router.

## Table of Contents

- [Installation](#installation)
- [Usage](#usage)
- [Configuration](#configuration)
- [Scheduled logging](#scheduled-logging)
- [Contributing](#contributing)
- [License](#license)

## Installation

1. Clone the repository:

   ```sh
   git clone https://github.com/yourusername/FRITZ-Box-Log-Saver.git
   ```

2. Change to the project directory:

    ```sh
    cd FRITZ-Box-Log-Saver
    ```

3. Install the required Python packages:

    ```sh
    pip install -r requirements.txt
    ```

## Usage

1. Make sure you have created a settings.yaml file with your [configuration](#configuration). See the Configuration section for details.

2. Run the application:

    ```sh
    python main.py
    ```

3. The application will log in to your FRITZ!Box, retrieve event log data, and save it to a CSV file.

## Configuration

Create a settings.yaml file with the following configuration:

    ```yaml
    url: http://fritz.box  # URL of your FRITZ!Box
    username: your_username  # Your FRITZ!Box username
    password: your_password  # Your FRITZ!Box password
    exclude:
    - ExcludedKeyword1  # List of keywords to exclude from log
    - ExcludedKeyword2
    logpath: fritzLog.csv  # Path to the CSV log file
    ```

Modify the values according to your FRITZ!Box login credentials and preferences.

## Scheduled logging

You can schedule the "FRITZ!Box Log Saver" to run automatically at specific times using crontab. To run the script daily at 00:00, follow these steps:

1. Open your crontab configuration for editing:

    ```sh
    crontab -e
    ```

2. Add the following line to schedule the script daily at midnight:

    ```sh
    0 0 * * * /usr/bin/python /path/to/FRITZ-Box-Log-Saver/main.py
    ```
    Replace ___'/usr/bin/python'___ with the path to your Python interpreter 
    (you can find it by running __'which python'__).

    Replace ___'/path/to/FRITZ-Box-Log-Saver'___ with the actual path to your project directory.

3. Save and exit the crontab editor.

This will run your script every day at midnight.


## Contributing

Contributions are welcome! If you have any suggestions, improvements, or bug fixes, please open an issue or a pull request.

## License
This project is licensed under the MIT License - see the LICENSE file for details.