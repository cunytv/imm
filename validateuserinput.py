#!/usr/bin/env python3

import re
import os


def is_valid_package_name(s):
    pattern = r'^[A-Za-z]{3,4}\d{4}(0[1-9]|1[0-2])(0[1-9]|[1-2]\d|3[0-1])$'
    if not re.match(pattern, s.split('_', 1)[0]):
        return False
    else:
        return True

# Validates camera card package name by confirming show code and date pattern, capitalizing all letters, deleting spaces
def card_package_name(name):
    if not is_valid_package_name(name):
        new_name = input(f"\033[31mWarning. {name} does not match show code and date pattern, e.g. LTNS20250402. Press enter to continue or type new package name: \033[0m")
        while new_name and not is_valid_package_name(name):
                new_name = input(
                    f"\033[31mWarning. {new_name} does not match show code and date pattern. Press enter to continue or type new package name: \033[0m")
        if new_name:
            name = new_name

    # Eliminates spaces and capitalizes letters
    name = name.replace(" ", "")
    name = name.upper()
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
