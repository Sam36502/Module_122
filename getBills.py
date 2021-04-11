#
# Gets the bills from the FTP server and
# parses them before sending the processed
# versions on to the payment server.
#
# Samuel Pearce
from datetime import datetime
import chevron
from ftplib import FTP
from bill import Bill

# Constants
LOG_FILE = './latest.log'
TXT_TEMPLATE_FILENAME = 'txt_template.txt'
XML_TEMPLATE_FILENAME = 'xml_template.txt'

# TODO: Config File
ABHOLSERVER_HOSTNAME = 'ftp.haraldmueller.ch'
ABHOLSERVER_USERNAME = 'schoolerinvoices'
ABHOLSERVER_PASSWORD = 'Berufsschule8005!'
ABHOLSERVER_PATH = 'out/AP18aPearce'

PAYSERVER_HOSTNAME = '134.119.225.245'
PAYSERVER_USERNAME = '310721-297-zahlsystem'
PAYSERVER_PASSWORD = 'Berufsschule8005!'


# Functions
def log(str):
    now = datetime.now()
    current_time = now.strftime("[%H:%M:%S] ")
    logfile.write(current_time + str + '\n')


logfile = open(LOG_FILE, 'w')
logfile.write(' -- Bill Retriever Log --\n\n')

# Connect to Server
log('Connecting to server...')
ftp = FTP(ABHOLSERVER_HOSTNAME)
ftp.login(ABHOLSERVER_USERNAME, ABHOLSERVER_PASSWORD)
# TODO: Check if connection was successful
log('Logged in successfully.')
ftp.cwd(ABHOLSERVER_PATH)

# Get names of new bills
bill_names = []


def getBillNames(name):
    if name.endswith('.data'):
        bill_names.append(name)


ftp.retrlines('NLST', getBillNames)
log('Retrieved bill names.')

# Get every bill file and delete it from the server
for bill in bill_names:
    with open(bill, 'wb') as bd:
        ftp.retrbinary('RETR ' + bill, bd.write)
    # DEBUG: Don't delete file from server # ftp.delete(bill)
log('Retrieved and deleted bill files.')
log('Closing connection.')
ftp.quit()

# Parse Datafile
log('Parsing Data...')
bills = []
for bill_file in bill_names:
    bills.append(Bill(bill_file))
# TODO: Check parsing was successful
log('Data Parsed Successfully.')

for curr_bill in bills:
    # Generate Text Output
    log('Generating human-readable file...')
    with open(TXT_TEMPLATE_FILENAME, 'r') as template:

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
    with open(XML_TEMPLATE_FILENAME, 'r') as template:

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
            'total_squash': str(int(curr_bill.billInfo.total * 10)).zfill(10),
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

logfile.close()
