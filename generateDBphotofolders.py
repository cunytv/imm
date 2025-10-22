#!/usr/bin/env python3

import requests
import cunymediaids
from datetime import date
import dropboxuploadsession
import sendnetworkmail

db_main_dir = "/►CUNY TV REMOTE FOOTAGE (for DELIVERY & COPY from)"
email_recipients = ["library@tv.cuny.edu", "Laura.fuchs@tv.cuny.edu", "vincent.verdi@tv.cuny.edu"]
db_folder_paths = []
db_share_links = []
db_request_links = []

def get_todays_calendar_events(url, calendar_type):
    response = requests.get(url)
    response.raise_for_status()

    lines = response.text.splitlines()

    events = []
    event = {}
    inside_event = False

    for line in lines:
        if line.startswith("BEGIN:VEVENT"):
            inside_event = True
            event = {}
        elif line.startswith("END:VEVENT"):
            inside_event = False
            events.append(event)
        elif inside_event:
            if line.startswith("SUMMARY:"):
                event["summary"] = line[len("SUMMARY:"):]
            elif line.startswith("DTSTART"):
                event["start"] = line.split(":")[1]
            elif line.startswith("DTEND"):
                event["end"] = line.split(":")[1]
            elif line.startswith("LOCATION:"):
                event["location"] = line[len("LOCATION:"):]
            elif line.startswith("DESCRIPTION:"):
                event["description"] = line[len("DESCRIPTION:"):]

    for e in events:
        date = e.get("start")
        date = date.split("T")[0]
        date_f = f"{date[:4]}.{date[4:6]}.{date[6:]}" # formatted date with periods
        show = e.get("summary", "No title")
        show = show.strip()

        if date.startswith(date_today) and "cancelled" not in show.lower():
            showcode = ''
            showname = ''

            show_code_matches = cunymediaids.codes_string_contains(show)
            show_name_matches = cunymediaids.shows_string_contains(show)

            if show_code_matches and len(show_code_matches) == 1:
                showcode = show_code_matches[0]
                showname = cunymediaids.get_full_show_name(showcode)
            elif show_name_matches and len(show_name_matches) == 1:
                showcode = cunymediaids.shows[show_name_matches[0]]
                showname = show_name_matches[0]

            if showcode:
                folder_string = f"{date_f}-{showcode}-{calendar_type}-SELECTS"
                folder_string = folder_string.upper()
                db_path = f"{db_main_dir}/►{showname.upper()}/PHOTOS/{folder_string}"
                db_folder_paths.append(db_path)
            else:
                description = show.upper().replace(" ", "")
                folder_string = f"{date_f}-{calendar_type}-{description}-SELECTS"
                folder_string = folder_string.upper()
                db_path = f"{db_main_dir}/►NO SHOW/PHOTOS/{folder_string}"
                db_folder_paths.append(db_path)


def create_db_folders():
    db = dropboxuploadsession.DropboxUploadSession()
    db.refresh_access_token()
    for p in db_folder_paths:
        db.create_folder(p)
        link = db.get_shared_link(p)
        if isinstance(link, (list, tuple)):
            link = link[0]
        db_share_links.append(link)

def create_request_links():
    db = dropboxuploadsession.DropboxUploadSession()
    db.refresh_access_token()
    for p in db_folder_paths:
        url = db.file_request(p)
        db_request_links.append(url)

def send_notification():
    notification = sendnetworkmail.SendNetworkEmail()
    notification.sender("library@tv.cuny.edu")
    notification.recipients(email_recipients)
    notification.subject(f"Dropbox folders for photos: {date.today()}")

    notification.html_content("<p>Hello, </p><p>The following folders were created:</p>")

    for p, l, l2 in zip(db_folder_paths, db_request_links, db_share_links):
        notification.html_content(f"<p></p>{p}<br>")
        notification.html_content(f"""Upload link: <a href="{l}">{l}</a><p></p>""")
        notification.html_content(f"""Share link: <a href="{l2}">{l2}</a><p></p>""")

    notification.html_content("Best<br>Library Bot<p></p>")
    notification.send()

date_today = (date.today()).strftime("%Y%m%d")

studio_url = "https://p41-caldav.icloud.com/published/2/MjAyNzAwODMyMzAyMDI3MJtQtj1d8sB3i2_EBb5YQf7GbIc81l4k5QGsBLpdH5XoSwMQFI5QwHFelo8NqSCUFcIb2j8tP3lkbd9WomW9QtE"
remote_url = "https://p41-caldav.icloud.com/published/2/MjAyNzAwODMyMzAyMDI3MJtQtj1d8sB3i2_EBb5YQf4RWs1oqnD8fOY_IPeum0GuQqh2CTCMnI4fB66RX20nos1_eaIG_DbgU8_e5T10Huk"
urls = [studio_url, remote_url]
types = ["studio", "remote"]

for u, t in zip(urls, types):
    get_todays_calendar_events(u, t)

create_db_folders()
create_request_links()
send_notification()
