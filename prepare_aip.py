#!/usr/bin/env python3

"""

Inspects an incoming package and turns it into an AIP

Determines:
    • Package type
    • Camera card folders
    • Existing AIP structure
    • File counts
    • Validation

"""

from pathlib import Path
import argparse
import sys
import shutil

CAMERA_EXTENSIONS = {".mxf"}
ACCESS_EXTENSIONS = {".mov", ".mp4"}

# ----------------------------------------------------------
# Helper functions
# ----------------------------------------------------------

# ----------------------------------------------------------
# Print heading
# ----------------------------------------------------------

def print_heading(title):
    """Print a section heading."""

    print()
    print("=" * 60)
    print(title)
    print("=" * 60)


# ----------------------------------------------------------
# Create directory
# ----------------------------------------------------------

def create_directory(path, package, dry_run=True):
    """
    Create a directory or report that it would be created.
    """

    print("Create directory")
    print("----------------")
    print(path.relative_to(package))
    print()

    if not dry_run:
        path.mkdir(parents=True, exist_ok=True)


# ----------------------------------------------------------
# Print operation
# ----------------------------------------------------------

def print_operation(source, destination):
    """
    Print a normalization operation.
    """

    print(source)
    print("    ↓")
    print(destination)
    print()

# ----------------------------------------------------------
# Find camera card folders
# ----------------------------------------------------------

def find_camera_cards(package):

    objects = package / "objects"

    #
    # Existing AIP
    #

    if objects.is_dir():

        cards = [
            d for d in sorted(objects.iterdir())
            if d.is_dir()
        ]

        return "existing_aip", cards

    #
    # Common typo
    #

    typo = package / "obects"

    if typo.is_dir():

        cards = [
            d for d in sorted(typo.iterdir())
            if d.is_dir()
        ]

        return "typo_objects", cards

    #
    # Editor delivery
    #

    cards = []

    for child in sorted(package.iterdir()):

        if not child.is_dir():
            continue

        if list(child.glob("*.MXF")) or list(child.glob("*.mxf")):
            cards.append(child)

    return "editor_delivery", cards


# ----------------------------------------------------------
# Create metadata structure
# ----------------------------------------------------------

def create_metadata_structure(inspection, dry_run=True):

    package = inspection["package"]

    metadata = package / "metadata"

    logs = metadata / "logs"

    print_heading("Metadata Structure")

    #
    # metadata/
    #

    if not metadata.exists():

        create_directory(
            metadata,
            package,
            dry_run
        )

    #
    # metadata/logs/
    #

    if not logs.exists():

        create_directory(
            logs,
            package,
            dry_run
        )

    #
    # metadata/logs/<camera card>
    #

    for number, card in enumerate(
            inspection["camera_cards"],
            start=1):

        log_directory = logs / str(number)

        if not log_directory.exists():

            create_directory(
                log_directory,
                package,
                dry_run
            )

    if dry_run:
        print("DRY RUN - No directories were created.")
    else:
        print("Metadata structure complete.")

# ----------------------------------------------------------
# Count files
# ----------------------------------------------------------

def count_files(package):

    counts = {
        "mxf": 0,
        "xml": 0,
        "bim": 0,
        "premiere": 0,
        "access": 0
    }

    for f in package.rglob("*"):

        if not f.is_file():
            continue

        ext = f.suffix.lower()

        if ext == ".mxf":
            counts["mxf"] += 1

        elif ext == ".xml":
            counts["xml"] += 1

        elif ext == ".bim":
            counts["bim"] += 1

        elif ext == ".prproj":
            counts["premiere"] += 1

        elif ext in ACCESS_EXTENSIONS:
            counts["access"] += 1

    return counts


# ----------------------------------------------------------
# Validation
# ----------------------------------------------------------

def validate(counts):

    messages = []

    if counts["mxf"] == 0:
        messages.append(("ERROR", "No MXF files found."))

    if counts["mxf"] == counts["xml"]:
        messages.append(("PASS", "MXF/XML counts match"))
    else:
        messages.append(("WARN",
                         f"MXF/XML mismatch ({counts['mxf']} vs {counts['xml']})"))

    if counts["mxf"] == counts["bim"]:
        messages.append(("PASS", "MXF/BIM counts match"))
    else:
        messages.append(("WARN",
                         f"MXF/BIM mismatch ({counts['mxf']} vs {counts['bim']})"))

    return messages


# ----------------------------------------------------------
# Report
# ----------------------------------------------------------

def report(package, package_type, cards, counts, validation):

    print("=" * 65)
    print("Package Inspection")
    print("=" * 65)

    print(f"\nPackage:\n    {package.name}")

    print("\nPackage Type")
    print("------------")

    if package_type == "existing_aip":
        print("✓ Existing AIP")

    elif package_type == "editor_delivery":
        print("✓ Editor Delivery")

    elif package_type == "typo_objects":
        print("⚠ Existing AIP (possible typo)")
        print("  Found directory named 'obects'")
        print("  Expected directory named 'objects'")

    print("\nDirectories")
    print("-----------")

    print(f"objects : {'YES' if (package/'objects').exists() else 'NO'}")
    print(f"metadata: {'YES' if (package/'metadata').exists() else 'NO'}")

    print("\nCamera Cards")
    print("------------")

    if cards:

        for i, card in enumerate(cards, start=1):
            print(f"{i}. {card.relative_to(package)}")

    else:
        print("None detected")

    print("\nFile Counts")
    print("-----------")

    print(f"MXF      : {counts['mxf']}")
    print(f"XML      : {counts['xml']}")
    print(f"BIM      : {counts['bim']}")
    print(f"Premiere : {counts['premiere']}")
    print(f"Access   : {counts['access']}")

    print("\nValidation")
    print("----------")

    for status, message in validation:

        icon = {
            "PASS": "✓",
            "WARN": "⚠",
            "ERROR": "✗"
        }[status]

        print(f"{icon} {message}")

    print("\nRecommendation")
    print("--------------")

    if package_type == "editor_delivery":

        print("• Create objects/")
        print("• Move camera card folder(s) into objects/")
        print("• Create metadata/logs/")
        print("• Move XML/BIM files")

    elif package_type == "existing_aip":

        if not (package / "metadata").exists():
            print("• Create metadata/logs/")
            print("• Move XML/BIM files")
        else:
            print("• Package already resembles an AIP")
            print("• Validate metadata layout")

    elif package_type == "typo_objects":

        print("• Rename 'obects' to 'objects'")
        print("• Continue normalization")



# ----------------------------------------------------------
# create an objects directory if needed
# ----------------------------------------------------------

def normalize_objects(inspection, dry_run=True):

    package = inspection["package"]
    objects = package / "objects"

    print_heading("Object Normalization")

    #
    # Create objects/
    #

    if not objects.exists():

        create_directory(
            objects,
            package,
            dry_run
        )

    #
    # Move camera card folders
    #

    print("Camera Card Mapping")
    print("-------------------")

    for number, card in enumerate(
            inspection["camera_cards"],
            start=1):

        destination = objects / str(number)

        print_operation(
            card.name,
            destination.relative_to(package)
        )

        if not dry_run:
            shutil.move(str(card), str(destination))

    if dry_run:
        print("\nDRY RUN - No files were modified.")
    else:
        print(f"\nMoved {len(inspection['camera_cards'])} camera card folder(s).")
        print("Object normalization complete.")


# ----------------------------------------------------------
# Main
# ----------------------------------------------------------

def main():

    ## inspect

    parser = argparse.ArgumentParser()

    parser.add_argument("package")

    args = parser.parse_args()

    package = Path(args.package)

    if not package.is_dir():
        sys.exit("Package not found.")

    package_type, cards = find_camera_cards(package)

    counts = count_files(package)

    validation = validate(counts)

    inspection = {
        "package": package,
        "package_type": package_type,
        "camera_cards": cards,
        "counts": counts,
        "validation": validation,
    }

    report(package, package_type, cards, counts, validation)

    ## normalize objects if needed

    if inspection["package_type"] == "editor_delivery":

        answer = input(
            "\nNormalize camera card folders into objects? [y/N] "
        )

        if answer.lower() == "y":

            normalize_objects(
                inspection,
                dry_run=False
            )
    else:
        print("\nObject normalization is not required.")

    ## normalize metadata directory if needed

    if not (package / "metadata").exists():

        answer = input(
            "\nCreate metadata/logs structure? [y/N] "
        )

        if answer.lower() == "y":
            create_metadata_structure(
                inspection,
                dry_run=False
            )
    else:
        print("\nMetadata structure already exists.")


if __name__ == "__main__":
    main()