#
# Gets the bills from the FTP server and
# parses them before sending the processed
# versions on to the payment server.
#
# Samuel Pearce
import os

import chevron
import configparser
from datetime import datetime
from ftplib import FTP
from bill import Bill

# Config
CONFIG_FILENAME = 'config.ini'
parser = configparser.ConfigParser()
parser.read(CONFIG_FILENAME)
config = parser['DEFAULT']

# Functions
def log(str):
    now = datetime.now()
    current_time = now.strftime("[%Y-%m-%d %H:%M:%S] ")
    logfile.write(current_time + str + '\n')


def getBillNames(name):
    if name.endswith('.data'):
        bill_names.append(name)


logfile = open(config['LOG_FILE'], 'a')
logfile.write('\n -- Bill Retriever Log --\n\n')

# Connect to Server
log('Connecting to server...')
ftp = FTP(config['ABHOLSERVER_HOSTNAME'])
ftp.login(config['ABHOLSERVER_USERNAME'], config['ABHOLSERVER_PASSWORD'])
log('Logged in successfully.')
ftp.cwd(config['SERVER_OUT_PATH'])

# Get names of new bills
bill_names = []
ftp.retrlines('NLST', getBillNames)
log('Retrieved bill names.')

# Get every bill file and delete it from the server
for bill in bill_names:
    with open(bill, 'wb') as bd:
        ftp.retrbinary('RETR ' + bill, bd.write)
    ftp.delete(bill)
log('Retrieved and deleted bill files.')
log('Closing connection.')
ftp.quit()

# Parse Datafile
log('Parsing Data...')
bills = []
for bill_file in bill_names:
    try:
        bills.append(Bill(bill_file))
    except AttributeError:
        log('Bill file \'' + bill_file + '\' has an invalid format.')
        os.remove(bill_file)
        continue
# TODO: Check parsing was successful
log('Data Parsed Successfully.')

for curr_bill in bills:
    # Generate Text Output
    log('Generating human-readable file...')
    with open(config['TXT_TEMPLATE_FILENAME'], 'r') as template:

        fields = {
            'sender_name': 			curr_bill.sender.name,
            'sender_address': 		curr_bill.sender.address,
            'sender_postcode': 		curr_bill.sender.postcode_and_city,
            'sender_company_name': 	curr_bill.sender.company_ID,
            'sender_location': 		curr_bill.billInfo.sender_location,
            'bill_date': 			curr_bill.billInfo.bill_date.strftime('%d.%m.%Y'),
            'receiver_name': 		curr_bill.receiver.name,
            'receiver_address': 	curr_bill.receiver.address,
            'receiver_postcode': 	curr_bill.receiver.postcode_and_city,
            'customer_number': 		curr_bill.receiver.customer_ID,
            'job_number': 			curr_bill.billInfo.job_num,
            'bill_number': 			curr_bill.billInfo.bill_num,
            'items': [],
            'bill_total_space':     ' ' * (16 - len(str(curr_bill.billInfo.total))),
            'bill_total': 		    curr_bill.billInfo.total,
            'VAT_total_space':      ' ' * (16 - len(str(curr_bill.billInfo.totalVAT))),
            'VAT_total': 		    curr_bill.billInfo.totalVAT,
            'payment_target': 	    curr_bill.billInfo.payment_target,
            'pay_by_date': 		    curr_bill.billInfo.pay_by.strftime('%d.%m.%Y'),
            'bill_total_fr': 	    curr_bill.billInfo.total_fr,
            'bill_total_rp': 	    curr_bill.billInfo.total_rp,
        }
        for curr_item in curr_bill.items:
            fields.get('items').append({
                'item_number': curr_item.item_num,
                'item_label': curr_item.item_label,
                'item_amount_space': ' ' * (40 - len(curr_item.item_label)),
                'amount': curr_item.amount,
                'unit_price_space': ' ' * (11 - len(curr_item.unit_price)),
                'unit_price': curr_item.unit_price,
                'total_space': ' ' * (12 - len(str(curr_item.total))),
                'total': curr_item.total,
                'VAT': curr_item.VAT
            })

        rendered_txt = chevron.render(template, fields)
        log('TXT File Generated Successfully.')

    # Generate XML Output
    log('Generating XML file...')
    with open(config['XML_TEMPLATE_FILENAME'], 'r') as template:

        fields = {
            'party_ID': curr_bill.sender.party_ID,
            'ref_num': datetime.now().strftime('%Y%m%d%H%M%S'),
            'date_squash': curr_bill.billInfo.bill_date.strftime('%Y%m%d'),
            'job_num': curr_bill.billInfo.job_num,
            'company_ID': curr_bill.sender.company_ID,
            'sender_name': curr_bill.sender.name,
            'sender_address': curr_bill.sender.address,
            'sender_postcode': curr_bill.sender.postcode_and_city,
            'receiver_name': curr_bill.receiver.name,
            'receiver_address': curr_bill.receiver.address,
            'receiver_postcode': curr_bill.receiver.postcode_and_city,
            'total_squash': str(int(curr_bill.billInfo.total * 100)).zfill(10),
            'bill_date_day': curr_bill.billInfo.bill_date.day,
            'payment_target': curr_bill.billInfo.payment_target,
            'pay_by_squash': curr_bill.billInfo.pay_by.strftime('%Y%m%d'),
        }

        rendered_xml = chevron.render(template, fields)
        log('XML File Generated Successfully.')

    # Write output Files
    out_filename = curr_bill.sender.customer_num + '_' + curr_bill.billInfo.bill_num + '_invoice'
    with open(out_filename + '.txt', 'w') as txt_file:
        txt_file.write(rendered_txt)
    with open(out_filename + '.xml', 'w') as xml_file:
        xml_file.write(rendered_xml)

    log('Generated text file.')

# Connect to Server
log('Connecting to server...')
ftp = FTP(config['PAYSERVER_HOSTNAME'])
ftp.login(config['PAYSERVER_USERNAME'], config['PAYSERVER_PASSWORD'])
# TODO: Check if connection was successful
log('Logged in successfully.')
ftp.cwd(config['SERVER_IN_PATH'])

# Upload Generated Files
log('Uploading Generated Files...')
with open(out_filename + '.txt', 'rb') as file:
    ftp.storbinary('STOR ' + out_filename + '.txt', file)
with open(out_filename + '.xml', 'rb') as file:
    ftp.storbinary('STOR ' + out_filename + '.xml', file)
ftp.quit()
log('Disconnected From Server.')
# TODO: Check if upload worked

log('End of Script.')
logfile.close()
