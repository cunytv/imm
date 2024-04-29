#!/usr/bin/env python3

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
import subprocess

class SendNetworkEmail:
    def __init__(self):
        self.EMAIL_FROM = ''
        self.EMAIL_TO = ''
        self.SUBJECT = ''
        self.CONTENT = ''

        # Create a multipart message
        self.MSG = MIMEMultipart()

    def sender(self, sender):
        self.EMAIL_FROM = sender
        self.MSG['From'] = self.EMAIL_FROM

    # Recieves emails argument as array and converts to string
    def recipients(self, emails):
        i = 0
        l = len(emails)

        emails_string = ''

        while i < l:
            if i + 1 == l:
                emails_string = emails_string + emails[i]
                break
            emails_string = emails_string + emails[i] + ', '
            i = i + 1

        self.EMAIL_TO = emails_string
        self.MSG['To'] = self.EMAIL_TO

    def subject(self, line):
        self.SUBJECT = line
        self.MSG['Subject'] = self.SUBJECT

    def content(self, content):
        # Add text content
        text = MIMEText(content, 'html')
        self.MSG.attach(text)

    #def image(self):
        # Add an image attachment
        #with open("/Users/archivesx/Desktop/Felis_silvestris_silvestris_small_gradual_decrease_of_quality.png", 'rb') as fp:
        #    img = MIMEImage(fp.read())
        #img.add_header('Content-Disposition', 'attachment', filename="image.jpg")
        #msg.attach(img)

    def send(self):
        # Print the MIME message
        print(self.MSG.as_string())

        # Send email using sendmail
        sendmail_command = ["sendmail", "-f", self.EMAIL_FROM, "-t", self.EMAIL_TO]
        sendmail_process = subprocess.Popen(sendmail_command, stdin=subprocess.PIPE)
        sendmail_process.communicate(input=self.MSG.as_bytes())

if __name__ == "__main__":
    # Create package object
    email = SendNetworkEmail()

    # Change to user input
    sender =  "library@tv.cuny.edu"
    recipients = ["library@tv.cuny.edu, david.rice@tv.cuny.edu"]
    subject = "Test Python email."
    content = "Test python email."

    # Create email parameters
    email.sender(sender)
    email.recipients(recipients)
    email.subject(subject)
    email.content(content)

    # Send email
    email.send()
