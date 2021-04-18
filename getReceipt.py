#
# Gets the receipt from the payment
# server, sends an email to the
# Sender, and stores an archive on
# the payment server
#
import os

import mail
from os import walk
from datetime import datetime
from ftplib import FTP
from zipfile import ZipFile
from bill import Bill

# Constants
# TODO: Config File
LOG_FILE = './latest.log'

ABHOLSERVER_HOSTNAME = 'ftp.haraldmueller.ch'
ABHOLSERVER_USERNAME = 'schoolerinvoices'
ABHOLSERVER_PASSWORD = 'Berufsschule8005!'
ABHOLSERVER_PATH = 'in/AP18aPearce'

PAYSERVER_HOSTNAME = '134.119.225.245'
PAYSERVER_USERNAME = '310721-297-zahlsystem'
PAYSERVER_PASSWORD = 'Berufsschule8005!'
PAYSERVER_RECEIPT_PATH = 'out/AP18aPearce'

# Functions
def log(str):
    now = datetime.now()
    current_time = now.strftime("[%Y/%m/%d - %H:%M:%S] ")
    logfile.write(current_time + str + '\n')

def getReceiptNames(name):
    if name.startswith('quittungsfile'):
        receipt_names.append(name)

# Starting logger
logfile = open(LOG_FILE, 'a')
logfile.write(' -- Bill Retriever Log --\n\n')

# Get bill info
_, _, filenames = next(walk('./'))
log('Parsing previous bill data...')
bills = []
for f in filenames:
    if f.startswith('rechnung'):
        bills.append(Bill(f))
# TODO: Check parsing was successful
log('Data parsed successfully.')

# Connect to Server
log('Connecting to server...')
ftp = FTP(PAYSERVER_HOSTNAME)
ftp.login(PAYSERVER_USERNAME, PAYSERVER_PASSWORD)
# TODO: Check if connection was successful
log('Logged in successfully.')
ftp.cwd(PAYSERVER_RECEIPT_PATH)

# Retrieve Receipts
receipt_names = []
ftp.retrlines('NLST', getReceiptNames)
for receipt in receipt_names:
    with open(receipt, 'wb') as bd:
        ftp.retrbinary('RETR ' + receipt, bd.write)
        # DEBUG: Don't delete file from server # ftp.delete(receipt)
log('Retrieved receipt files.')
log('Closing connection.')
ftp.quit()

# Make Zip File
for curr_bill in bills:
    out_filename = curr_bill.sender.customer_num + '_' + curr_bill.billInfo.bill_num + '_invoice'
    with ZipFile(out_filename + '.zip', 'w') as archive:
        archive.write(out_filename + '.txt')
        for receipt in receipt_names:
            archive.write(receipt)

# Send E-Mails
log('Sending notification Emails...')
for bill in bills:
    mail_content = mail.generateMailContent(
        bill.sender.name,
        bill.billInfo.bill_num,
        PAYSERVER_HOSTNAME
    )
    log('Generated Bill-' + bill.billInfo.bill_num + '\'s E-Mail.')
    archive_filename = curr_bill.sender.customer_num + '_' + curr_bill.billInfo.bill_num + '_invoice.zip'
    mail.sendMsg(
        bill.sender.email,
        'Erfolgte Verarbeitung Rechnung ' + bill.billInfo.bill_num,
        mail_content,
        archive_filename
    )
log('Sent all Emails.')

# Upload archive to customer server
log('Archiving bill info on customer server')
ftp = FTP(ABHOLSERVER_HOSTNAME)
ftp.login(ABHOLSERVER_USERNAME, ABHOLSERVER_PASSWORD)
ftp.cwd(ABHOLSERVER_PATH)

for curr_bill in bills:
    archive_filename = curr_bill.sender.customer_num + '_' + curr_bill.billInfo.bill_num + '_invoice.zip'
    with open(archive_filename, 'rb') as file:
        ftp.storbinary('STOR ' + archive_filename, file)

ftp.quit()
log('Finished archive upload.')

log('Deleting temporary files...')
for receipt in receipt_names:
    os.remove(receipt)
for curr_bill in bills:
    temp_filename = curr_bill.sender.customer_num + '_' + curr_bill.billInfo.bill_num + '_invoice'
    os.remove(temp_filename + '.txt')
    os.remove(temp_filename + '.xml')
    os.remove(temp_filename + '.zip')
    bill_name = 'rechnung' + curr_bill.billInfo.bill_num + '.data'
    os.remove(bill_name)
log('Finished removing temp files.')

log('End of Script.')
logfile.close()