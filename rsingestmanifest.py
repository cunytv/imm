#!/usr/bin/env python3

import json
import os
from datetime import datetime

class RSIngestManifest:
    def __init__(self, ingest_type):
        self.FOLDER = ''
        self.FILES = []
        self.ingest_type = ingest_type
        self.folder_dest = '/Volumes/CUNYTVMEDIA/archive_projects/_watch_for_ingest_RSsync'

    def to_dict(self):
        return {
            "folder": self.FOLDER,
            "files": self.FILES
        }

    def save(self):
        file_name = f"ingest_{self.ingest_type}_{datetime.now().strftime('%Y%m%d%H%M%S')}.json"
        output_path = os.path.join(self.folder_dest, file_name)

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=4)
