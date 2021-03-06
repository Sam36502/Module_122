#
# Gets the receipt from the payment
# server, sends an email to the
# Sender, and stores an archive on
# the payment server
#
import os

import mail
from mail import config
from os import walk
from datetime import datetime
from ftplib import FTP
from zipfile import ZipFile
from bill import Bill

# Functions
def log(str):
    now = datetime.now()
    current_time = now.strftime("[%Y-%m-%d - %H:%M:%S] ")
    logfile.write(current_time + str + '\n')

def getReceiptNames(name):
    if name.startswith('quittungsfile'):
        receipt_names.append(name)

# Starting logger
logfile = open(config['LOG_FILE'], 'a')
logfile.write('\n -- Receipt Retriever Log --\n\n')

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
ftp = FTP(config['PAYSERVER_HOSTNAME'])
ftp.login(config['PAYSERVER_USERNAME'], config['PAYSERVER_PASSWORD'])
# TODO: Check if connection was successful
log('Logged in successfully.')
ftp.cwd(config['SERVER_OUT_PATH'])

# Retrieve Receipts
receipt_names = []
ftp.retrlines('NLST', getReceiptNames)
for receipt in receipt_names:
    with open(receipt, 'wb') as bd:
        ftp.retrbinary('RETR ' + receipt, bd.write)
        ftp.delete(receipt)
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
        config['PAYSERVER_HOSTNAME']
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
ftp = FTP(config['ABHOLSERVER_HOSTNAME'])
ftp.login(config['ABHOLSERVER_USERNAME'], config['ABHOLSERVER_PASSWORD'])
ftp.cwd(config['SERVER_IN_PATH'])

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
