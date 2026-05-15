#!/usr/bin/env python3

import json
import os
import argparse
from datetime import datetime


class RSIngestManifest:
    def __init__(self, ingest_type):
        self.FOLDER = ""
        self.FILES = []
        self.ingest_type = ingest_type
        self.folder_dest = "/Volumes/CUNYTVMEDIA/archive_projects/_watch_for_ingest_RSsync"

    def to_dict(self):
        return {
            "folder": self.FOLDER,
            "files": self.FILES
        }

    def save(self):
        file_name = f"ingest_{datetime.now().strftime('%Y%m%d%H%M%S')}_{self.ingest_type}.json"
        output_path = os.path.join(self.folder_dest, file_name)

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=4)

        print(f"Saved manifest to: {output_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Create a ResourceSpace ingest manifest"
    )

    parser.add_argument(
        "--type",
        required=True,
        help="Ingest type"
    )

    parser.add_argument(
        "--folder",
        required=True,
        help="Source folder path"
    )

    parser.add_argument(
        "--files",
        nargs="+",
        required=False,
        help="List of files"
    )

    args = parser.parse_args()

    manifest = RSIngestManifest(args.type)
    manifest.FOLDER = args.folder
    manifest.FILES = args.files

    manifest.save()


if __name__ == "__main__":
    main()
