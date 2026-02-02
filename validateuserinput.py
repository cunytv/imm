#!/usr/bin/env python3

import re
import os
import cunymediaids
from datetime import datetime


def is_valid_package_name(s):
    #pattern = r'^[A-Za-z]+\d{4}(0[1-9]|1[0-2])(0[1-9]|[1-2]\d|3[0-1])_[A-Za-z0-9_]+$'

    #if not re.match(pattern, s):
    #    warning = f"{s} does not match show code and date pattern. Package name must include SHOWCODEYYYMMDD_DESCRIPTION. "
    #    return False, warning
    
    bool = True
    warning = ""
    show_code = re.match(r"[A-Za-z]+", s).group() if re.match(r"[A-Za-z]+", s) else None
    date = re.match(r".*?(\d+)_", s).group(1) if re.match(r".*?(\d+)_", s) else None
    today_str = datetime.now().strftime("%Y%m%d")

    if not show_code:
        warning += f"Show code is missing. "
        bool = False
    elif not cunymediaids.is_code_in_dict(show_code):
        warning += f"Show code {show_code} is not in dictionary. "
        bool = False

    if not date:
        warning += f"Date is missing. "
        bool = False
    elif date != today_str:
        warning += f"Date {date} is not today's date {today_str}. "
        bool = False

    return bool, warning

# Validates camera card package name by confirming show code and date pattern, capitalizing all letters, deleting spaces
def card_package_name(name):
    valid_name, error = is_valid_package_name(name)
    while not valid_name:
        name = input(f"\033[31mWarning. {error}Press enter to continue or type new package name: \033[0m")
        if not name:
            break
        else:
            valid_name, error = is_valid_package_name(name)

    # Eliminates spaces and capitalizes letters
    name = name.replace(" ", "")
    name = name.upper()

    # Remove characters which aren't underscores and alphanumerics
    name = re.sub(r'[^A-Za-z0-9_]', '', name)

    # Replace underscores with underscore
    re.sub(r'_+', '_', name)

    return name

# Validates camera card subfolder name by replacing spaces with underscores, capitalizing all letters
def card_subfolder_name(name):
    while not name:
        new_name = input(f"\033[31mSubfolder name cannot be blank. Please type new name: \033[0m")
        name = new_name

    # Eliminates spaces and capitalizes letters
    name = name.replace(" ", "")
    name = name.upper()
    return name

# Searches string for valid emails and returns an array of email(s)
def emails(string):
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'

    # Texts in string that match email pattern
    emails = re.findall(email_pattern, string)
    # Texts in string that do not match email pattern
    non_matching_parts = re.split(email_pattern, string)
    # Filter out empty strings (which are the matches) and strip any leading/trailing whitespace
    non_matching_text = [part.strip() for part in non_matching_parts if part.strip()]

    while non_matching_text:
        print ("\033[31mInvalid emails detected.\033[0m")
        print (f"\tValid: {emails}")
        print (f"\033[31m\tInvalid: {non_matching_text}\033[0m")
        string = input("Re-enter incorrect inputs: ")

        emails.extend(re.findall(email_pattern, string))
        non_matching_parts = re.split(email_pattern, string)
        non_matching_text = [part.strip() for part in non_matching_parts if part.strip()]

    return emails

# Checks if path exists
def path(path):
    while os.path.exists(path) == False:
        path = input("\033[31mInvalid path. Please reenter: \033[0m")
    return (path)
