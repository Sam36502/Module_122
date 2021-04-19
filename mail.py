#
# Script to handle E-Mail rendering
# and transfer via GMail.
#

import chevron
import smtplib
import ssl
import codecs
import configparser
from datetime import datetime
from email import encoders
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText

# Config
CONFIG_FILENAME = 'config.ini'
parser = configparser.ConfigParser()
parser.read(CONFIG_FILENAME)
config = parser['DEFAULT']


def sendMsg(recipient_address, subject, content, attachment):
    context = ssl.create_default_context()

    message = MIMEMultipart()
    message['Subject'] = subject
    message['From'] = config['EMAIL_ADDRESS']
    message['To'] = recipient_address

    message.attach(MIMEText(content, 'plain'))

    # Add attachment
    with open(attachment, 'rb') as attachedfile:
        part = MIMEBase("application", "octet-stream")
        part.set_payload(attachedfile.read())

    encoders.encode_base64(part)
    part.add_header(
        "Content-Disposition",
        f"attachment; filename= {attachment}",
    )
    message.attach(part)

    with smtplib.SMTP_SSL(config['MAIL_SERVER'], config['SSL_PORT'], context=context) as server:
        server.login(config['EMAIL_ADDRESS'], config['EMAIL_PASSWORD'])
        server.sendmail(config['EMAIL_ADDRESS'], recipient_address, message.as_string())

def generateMailContent(recipient_name, bill_num, payment_sys_address):
    with codecs.open(config['EMAIL_TEMPLATE'], 'r', 'utf-8') as template:

        now = datetime.now()
        fields = {
            'recipient_name': recipient_name,
            'date_now': now.strftime('%d.%m.%Y'),
            'time_now': now.strftime('%H:%M:%S'),
            'bill_num': bill_num,
            'payment_system_address': payment_sys_address
        }

        return chevron.render(template, fields)
