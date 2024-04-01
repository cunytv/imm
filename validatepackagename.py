#!/usr/bin/env python3

import re

# Validates package name by confirming show code and date pattern, capitalizing all letters, deleting spaces
def package(name):
    # Checks pattern
    pattern = r'^[A-Za-z]{3,4}\d{4}(0[1-9]|1[0-2])(0[1-9]|[1-2]\d|3[0-1])$'
    if not re.match(pattern, name.split('_', 1)[0]):
        new_name = input(f"Warning. {name} does not match show code and date pattern. Press enter to continue or type new package name: ")
        while new_name and not re.match(pattern, new_name.split('_', 1)[0]):
                new_name = input(
                    f"Warning. {new_name} does not match show code and date pattern. Press enter to continue or type new package name: ")
        if new_name:
            name = new_name

    # Eliminates spaces and capitalizes letters
    name = name.replace(" ", "")
    name = name.upper()
    return name

# Validates subfolder name by replacing spaces with underscores, capitalizing all letters
def subfolder(name):
    while not name:
        new_name = input(f"Subfolder name cannot be blank. Please type new name: ")
        name = new_name
    name = name.replace(" ", "")
    name = name.upper()
    return name
