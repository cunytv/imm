#!/usr/bin/env python3

import sys
from pathlib import Path
from datetime import datetime

# --------------------------------------------------
# Select package
# --------------------------------------------------

if len(sys.argv) > 1:
    package = Path(sys.argv[1]).expanduser().resolve()
else:
    package = Path(input("Package path: ").strip()).expanduser().resolve()

if not package.is_dir():
    raise SystemExit(f"Package not found: {package}")

original_name = package.name

# --------------------------------------------------
# Prepared by
# --------------------------------------------------

prepared_by = input("Prepared by: ").strip()

# --------------------------------------------------
# Rename package
# --------------------------------------------------

actions = []

print(f"\nCurrent package name:\n{original_name}")

rename = input("\nRename package? (y/n): ").strip().lower()

if rename == "y":

    new_name = input("New package name: ").strip()

    if new_name and new_name != original_name:

        new_package = package.parent / new_name

        if new_package.exists():
            raise SystemExit(f"Package '{new_name}' already exists.")

        package.rename(new_package)
        package = new_package

        actions.append(
            f"Renamed package from '{original_name}' to '{package.name}'."
        )

# --------------------------------------------------
# Create standard AIP folders
# --------------------------------------------------

metadata = package / "metadata"
logs = metadata / "logs"
objects = package / "objects"

created = []

for directory in (metadata, logs, objects):

    if not directory.exists():
        directory.mkdir(parents=True)
        created.append(directory.relative_to(package))

# --------------------------------------------------
# Additional preparation actions
# --------------------------------------------------

MENU = {
    "1": "Renamed folders",
    "2": "Moved LUT files",
    "3": "Removed timecode files",
    "4": "Removed preview files",
    "5": "Removed duplicate files",
    "6": "Removed empty folders",
    "7": "Added missing documentation",
    "8": "Other",
}

print("\nPreparation Actions")
print("-------------------")

for number, action in MENU.items():
    print(f"{number}. {action}")

selection = input(
    "\nSelect actions (comma separated, or press Enter for none): "
).replace(" ", "")

if selection:

    for choice in selection.split(","):

        if choice == "1":

            note = input("Describe folder rename(s): ").strip()
            actions.append(f"Renamed folders. {note}")

        elif choice == "2":

            # Create LUT folder only if needed
            luts = logs / "LUTs"
            luts.mkdir(exist_ok=True)

            note = input(
                "Describe LUT move (or press Enter for default): "
            ).strip()

            if note:
                actions.append(note)
            else:
                actions.append(
                    "Moved LUT (.cube/.look) files to metadata/logs/LUTs/."
                )

        elif choice == "3":

            note = input("Describe removed timecode files: ").strip()
            actions.append(note)

        elif choice == "4":

            note = input("Describe removed preview files: ").strip()
            actions.append(note)

        elif choice == "5":

            note = input("Describe duplicates removed: ").strip()
            actions.append(note)

        elif choice == "6":

            note = input("Describe empty folders removed: ").strip()
            actions.append(note)

        elif choice == "7":

            note = input("Documentation added: ").strip()
            actions.append(note)

        elif choice == "8":

            while True:

                note = input("Other action (blank when finished): ").strip()

                if not note:
                    break

                actions.append(note)

# --------------------------------------------------
# Write preparation.log
# --------------------------------------------------

logfile = logs / "preparation.log"

with logfile.open("w", encoding="utf-8") as log:

    log.write("Preparation Log\n")
    log.write("====================\n\n")

    log.write(f"Date: {datetime.now():%Y-%m-%d %H:%M:%S}\n")
    log.write(f"Prepared By: {prepared_by}\n\n")

    log.write("Original Package Name\n")
    log.write("---------------------\n")
    log.write(f"{original_name}\n\n")

    log.write("Current Package Name\n")
    log.write("--------------------\n")
    log.write(f"{package.name}\n\n")

    if created:

        log.write("Directories Created\n")
        log.write("-------------------\n")

        for directory in created:
            log.write(f"- {directory}\n")

        log.write("\n")

    log.write("Preparation Actions\n")
    log.write("-------------------\n")

    if actions:

        for i, action in enumerate(actions, start=1):
            log.write(f"{i}. {action}\n")

    else:
        log.write("None\n")

print(f"\nPreparation log created:\n{logfile}")