#!/usr/bin/env python3
from email.mime.base import MIMEBase
from email.mime.image import MIMEImage
import subprocess
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email import encoders
import os
import re
from imm import validateuserinput


class SendNetworkEmail:
    def __init__(self):
        self.EMAIL_FROM = ''
        self.EMAIL_TO = ''
        self.SUBJECT = ''
        self.CONTENT = ''
        self.content_array = []

        # Create a multipart message of 'related' type to embed images
        self.MSG = MIMEMultipart('mixed')  # 'mixed' type can be more appropriate for both text and images
        self.MSG.preamble = 'This is a multi-part message in MIME format.'

        # Embed img counter
        self.img_counter = 0

    def sender(self, sender):
        self.EMAIL_FROM = sender
        self.MSG['From'] = self.EMAIL_FROM

    def recipients(self, emails):
        """ Receives emails argument as a list and converts to a comma-separated string """
        self.EMAIL_TO = ', '.join(emails)
        self.MSG['To'] = self.EMAIL_TO

    def subject(self, line):
        self.SUBJECT = line
        self.MSG['Subject'] = self.SUBJECT

    def html_content(self, content):
        """ Add HTML content to the email """
        content = self.strip_html_and_body(content)
        self.splice_content(content)

    def strip_html_and_body(self, content):
        """ Remove <html> and <body> tags if present """
        content = re.sub(r'</?html.*?>', '', content)
        content = re.sub(r'</?body.*?>', '', content)
        return content

    def splice_content(self, content):
        """ Split the content into tags and text """
        # Match both tags and the text between tags
        pattern = r'(</?[^>]+>)|([^<]+)'

        # Find all tags and text
        content_array = re.findall(pattern, content)

        # Flatten the results: Only take the non-empty part of the tuple
        content_array = [item[0] if item[0] else item[1] for item in content_array]

        self.content_array = self.content_array + content_array

    def prepare_html(self):
        """ Prepare the full HTML structure with content and body tags """
        starttags = """
        <html>
          <body>
        """

        endtags = """
          </body>
        </html>
        """

        # Combine all the content and tags
        html_body = starttags
        for text in self.content_array:
            html_body += text
        html_body += endtags

        self.CONTENT = html_body  # Final HTML body

        # Attach the prepared HTML as MIMEText
        text = MIMEText(self.CONTENT, 'html')
        self.MSG.attach(text)

    def attachment(self, file):
        """ Attach file to the email """
        try:
            with open(file, 'rb') as attachment:
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(attachment.read())
                encoders.encode_base64(part)
                part.add_header(
                    'Content-Disposition',
                    f'attachment; filename={file.split("/")[-1]}'
                )
                self.MSG.attach(part)
        except Exception as e:
            print(f"Failed to attach the file: {e}")
            return

    def embed_img(self, img_path):
        """ Embed a GIF in the email body using CID reference """
        self.img_counter += 1
        img_cid = f"image{self.img_counter}"

        # Append <img> tag with cid reference to HTML content
        img_tag = f"""<img src="cid:{img_cid}">"""
        self.html_content(img_tag)

        try:
            if not os.path.isfile(img_path):
                print(f"Image file not found: {img_path}")
                return

            with open(img_path, 'rb') as img_file:
                img = MIMEImage(img_file.read())
                img.add_header('Content-ID', f'<{img_cid}>')  # This ID is used in HTML
                self.MSG.attach(img)
                print(f"Image embedded with CID: {img_cid}")
        except Exception as e:
            print(f"Failed to embed image: {e}")

    def send(self):
        """ Prepare and send the email using sendmail """
        self.prepare_html()
        try:
            # Print the MIME message for debugging purposes
            print(self.MSG.as_string())  # Check the full MIME structure

            # Send the email using sendmail
            sendmail_command = ["sendmail", "-f", self.EMAIL_FROM, "-t", self.EMAIL_TO]
            sendmail_process = subprocess.Popen(sendmail_command, stdin=subprocess.PIPE)
            sendmail_process.communicate(input=self.MSG.as_bytes())
            print("Email sent successfully!")
        except Exception as e:
            print(f"Failed to send email: {e}")


if __name__ == "__main__":
    # Create an instance of the email class
    email = SendNetworkEmail()

    # Set the sender, recipients, and subject
    sender = "library@tv.cuny.edu"
    recipients = validateuserinput.emails(input("List recipient email(s) delimited by space: "))
    subject = input("Subject: ")
    html_content = input("Text content (HTML tags permitted, e.g. <br>, <p>, <h1>, <b>, etc)) or press enter to continue: ")
    embed_image = input("Embed image at the end of email? Input file path or press enter to continue: ")
    attachments = (input("List attachment(s) delimited by space: ")).split()

    # Set email parameters
    email.sender(sender)
    email.recipients(recipients) # Accepts array
    email.subject(subject)
    email.html_content(html_content)
    if embed_image:
        email.embed_img(embed_image)
    for attachment in attachments:
        email.attachment(attachment)

    # Send the email
    email.send()
