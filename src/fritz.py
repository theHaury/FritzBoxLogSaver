import os
import sys
import csv
import json
import yaml
import hashlib
import time
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
import requests

from datetime import datetime

LOGIN_SID_ROUTE = "/login_sid.lua?version=2"

class LoginState:
    def __init__(self, challenge: str, blocktime: int):
        """
        Initializes a LoginState object.

        Parameters:
            challenge (str): The challenge string used for authentication.
            blocktime (int): The time duration for which login is blocked after multiple failed attempts.
        """
        self.challenge = challenge
        self.blocktime = blocktime
        self.is_pbkdf2 = challenge.startswith("2$")

def get_sid(box_url: str, username: str, password: str) -> str:
    """
    Retrieves the session ID (SID) for a given user by performing the login process.

    Parameters:
        box_url (str): The URL of the login service.
        username (str): The user's username.
        password (str): The user's password.

    Returns:
        str: The session ID (SID) if the login is successful.

    Raises:
        Exception: If an error occurs during the login process.
    """
    try:
        state = get_login_state(box_url)
    except Exception as ex:
        raise Exception("Failed to get challenge") from ex

    if state.is_pbkdf2:
        print("PBKDF2 supported")
        challenge_response = calculate_pbkdf2_response(state.challenge, password)
    else:
        print("Falling back to MD5")
        challenge_response = calculate_md5_response(state.challenge, password)

    if state.blocktime > 0:
        print(f"Waiting for {state.blocktime} seconds...")
        time.sleep(state.blocktime)

    try:
        sid = send_response(box_url, username, challenge_response)
    except Exception as ex:
        raise Exception("Failed to login") from ex

    if sid == "0000000000000000":
        raise Exception("Wrong username or password")

    return sid

def get_login_state(box_url: str) -> LoginState:
    """
    Retrieves the login state from the given box URL.

    Parameters:
        box_url (str): The URL of the login service.

    Returns:
        LoginState: A LoginState object containing challenge and blocktime information.
    """
    url = box_url + LOGIN_SID_ROUTE
    http_response = urllib.request.urlopen(url)
    xml = ET.fromstring(http_response.read())
    challenge = xml.find("Challenge").text
    blocktime = int(xml.find("BlockTime").text)
    return LoginState(challenge, blocktime)

def calculate_pbkdf2_response(challenge: str, password: str) -> str:
    """
    Calculates the PBKDF2 response for the given challenge and password.

    Parameters:
        challenge (str): The challenge string received during login.
        password (str): The user's password.

    Returns:
        str: The PBKDF2 response in the format "salt2$hash2_hex".
    """
    challenge_parts = challenge.split("$")
    # Extract all necessary values encoded into the challenge
    iter1 = int(challenge_parts[1])
    salt1 = bytes.fromhex(challenge_parts[2])
    iter2 = int(challenge_parts[3])
    salt2 = bytes.fromhex(challenge_parts[4])
    # Hash twice, once with static salt...
    hash1 = hashlib.pbkdf2_hmac("sha256", password.encode(), salt1, iter1)
    # Once with dynamic salt.
    hash2 = hashlib.pbkdf2_hmac("sha256", hash1, salt2, iter2)
    return f"{challenge_parts[4]}${hash2.hex()}"

def calculate_md5_response(challenge: str, password: str) -> str:
    """
    Calculates the MD5 response for the given challenge and password.

    Parameters:
        challenge (str): The challenge string received during login.
        password (str): The user's password.

    Returns:
        str: The MD5 response in the format "challenge-md5_hex".
    """
    response = challenge + "-" + password
    # the legacy response needs utf_16_le encoding
    response = response.encode("utf_16_le")
    md5_sum = hashlib.md5()
    md5_sum.update(response)
    response = challenge + "-" + md5_sum.hexdigest()
    return response

def send_response(box_url: str, username: str, challenge_response: str) -> str:
    """
    Send the login response and return the session ID (SID). Raises an Exception on error.

    Parameters:
        box_url (str): The URL of the login service.
        username (str): The user's username.
        challenge_response (str): The challenge response generated during login.

    Returns:
        str: The session ID (SID) if the response is successful.

    Raises:
        Exception: If an error occurs during the response sending process.
    """
    # Build response params
    post_data_dict = {"username": username, "response": challenge_response}
    post_data = urllib.parse.urlencode(post_data_dict).encode()
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    url = box_url + LOGIN_SID_ROUTE
    # Send response
    http_request = urllib.request.Request(url, post_data, headers)
    http_response = urllib.request.urlopen(http_request)
    # Parse SID from resulting XML.
    xml = ET.fromstring(http_response.read())
    return xml.find("SID").text

def unix_timestamp_from_strings(date_string: str, time_string: str) -> int:
    """
    Converts the given date and time strings to a Unix timestamp.

    Parameters:
        date_string (str): The date string in the format "dd.mm.yy".
        time_string (str): The time string in the format "HH:MM:SS".

    Returns:
        int: The Unix timestamp representing the provided date and time.
    """
    datetime_string = f"{date_string} {time_string}"
    datetime_obj = datetime.strptime(datetime_string, "%d.%m.%y %H:%M:%S")

    # Get the Unix timestamp
    unix_timestamp = int(datetime_obj.timestamp())

    return unix_timestamp

def get_last_timestamp(file_path: str) -> int:
    """
    Retrieves the last timestamp from a CSV file.

    Parameters:
        file_path (str): The path to the CSV file.

    Returns:
        int: The last timestamp found in the CSV file or 1 if the file is empty or does not exist.
    """
    try:
        with open(file_path, 'r') as file:
            lines = file.readlines()
            if lines:
                last_line = lines[-1].strip()
                timestamp = int(last_line.split(";")[0].strip())
                return timestamp
            else:
                return 1
    except Exception:
        return 1

def create_or_append_to_csv(file_path: str, data: list, fieldnames: list):
    """
    Creates or appends data to a CSV file based on the given fieldnames.

    Parameters:
        file_path (str): The path to the CSV file.
        data (list): A list of dictionaries containing the data to be written.
        fieldnames (list): A list of field names for the CSV file.
    """
    file_exists = os.path.isfile(file_path)

    with open(file_path, mode='a', newline='') as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames, delimiter=";")
        if not file_exists:
            writer.writeheader()        

        last_timestamp = get_last_timestamp(file_path)

        for entry in data:
            if int(entry["Timestamp"]) > last_timestamp:
                writer.writerow(entry)

def get_fritzbox_event_log(url:str, sid: str, excludes: list) -> list:
    """
    Retrieves the event log data from the FritzBox using the provided session ID (SID).

    Parameters:
        sid (str): The session ID obtained after successful login.

    Returns:
        list: A list of dictionaries representing the event log data in CSV format.
    """
    # url = "http://fritz.box/data.lua"
    if url.endswith("/"):
        url = f"{url}data.lua"
    else:
        if "data.lua" not in url:
            url = f"{url}/data.lua"

    data = {
        'xhr': 1,
        'sid': sid,
        'lang': 'de',
        'page': 'log',
        'xhrId': 'log',
    }

    response = requests.post(url, data=data)

    if response.status_code == 200:
        # Process the event log data in the response
        event_log_data = response.text
        # print(event_log_data)
        jdata = json.loads(event_log_data)
        logData = jdata.get("data").get("log")
        csvData = []
        for entry in list(logData)[::-1]:
            Message = entry[2]
            if not is_excluded(Message, excludes):
                cdata = {
                    "Timestamp": f'{unix_timestamp_from_strings(entry[0], entry[1])}',
                    "Date": entry[0],
                    "Time": entry[1],
                    "Message": entry[2],
                    "Code": entry[3],
                }
                csvData.append(cdata)
            # else:
            #     print(f"Excluded Message: {Message}")
            

        return csvData
    else:
        print(f"Failed to retrieve event log. Status code: {response.status_code}")

def is_excluded(message: str, excludes: list) -> bool:
    """
    Checks if a message is excluded based on a list of exclusion criteria.

    The exclusion criteria can be either strings or lists of strings. For strings,
    the function checks if the item is present in the message. For lists, the function
    checks if all elements in the list are present in the message.

    Parameters:
        message (str): The message to be checked for exclusion.
        excludes (list): A list of strings or lists of strings representing exclusion criteria.

    Returns:
        bool: True if the message is excluded based on any exclusion criteria, False otherwise.
    """
    for item in excludes:
        if isinstance(item, str):
            # For string items, check if the item is present in the message
            if item in message:
                return True
        elif isinstance(item, list):
            # For list items, check if all elements in the list are present in the message
            if all(part in message for part in item):
                return True
    return False

def load_settings(path:str) -> dict:
    """
    Loads settings from a YAML file and returns them as a dictionary.

    The function reads the "settings.yaml" file and parses its content into a dictionary.

    Returns:
        dict: A dictionary containing the settings loaded from the YAML file.
    """
    with open(path, "r") as file:
        # Load the YAML data from the file
        data = yaml.safe_load(file)
        return data

def main():
    """
    Logs in to a FritzBox device, retrieves the event log data, and saves it to a CSV file.
    """
    settingsFile = os.path.join(os.path.dirname(sys.argv[0]),"settings.yaml")
    if not os.path.exists(settingsFile):
        print("No 'settings.yaml' found")
        if os.path.exists(settingsFile.replace("settings.yaml", "ex_settings.yaml")):
            print("Rename the 'ex_settings.yaml' to 'settings.yaml' and fill in your data.\nThen try starting the script again.")
        input("Press enter to exit...")
        exit()

    Settings = load_settings(settingsFile)
    url = Settings.get("url", "http://fritz.box")
    username = Settings.get("username", "")
    password = Settings.get("password", "")
    excludes = Settings.get("exclude", [])
    LogPath = Settings.get("logpath", "fritzLog.csv")
    sid = get_sid(url, username, password)
    print(f"Successful login for user: {username}")
    print(f"sid: {sid}")

    log = get_fritzbox_event_log(url, sid, excludes)
    keynames = list(log[0].keys())
    create_or_append_to_csv(LogPath, log, keynames)

if __name__ == "__main__":
    main()