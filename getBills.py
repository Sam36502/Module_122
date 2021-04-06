#
# Gets the bills from the FTP server and
# parses them before sending the processed
# versions on to the payment server.
#
# Samuel Pearce

from ftplib import FTP

import time
import csv

import bill.py

# Constants
LOG_FILE = './latest.log'

ABHOLSERVER_HOSTNAME = 'ftp.haraldmueller.ch'
ABHOLSERVER_USERNAME = 'schoolerinvoices'
ABHOLSERVER_PASSWORD = 'Berufsschule8005!'
ABHOLSERVER_PATH = 'out/AP18aPearce'

PAYSERVER_HOSTNAME = '134.119.225.245'
PAYSERVER_USERNAME = '310721-297-zahlsystem'
PAYSERVER_PASSWORD = 'Berufsschule8005!'

logfile = open(LOG_FILE, 'w')
nowstr = time.asctime(time.localtime())
logfile.write(nowstr + '\n -- LATEST LOG --\n\n')

# Connect to Server
logfile.write('Connecting to server...\n')
ftp = FTP(ABHOLSERVER_HOSTNAME)
ftp.login(ABHOLSERVER_USERNAME, ABHOLSERVER_PASSWORD)
# TODO: Check if connection was successful
logfile.write('Logged in successfully.\n')
ftp.cwd(ABHOLSERVER_PATH)

# Get names of new bills
bills = []
def getBillNames(name):
	if name.endswith('.data'):
		bills.append(name)
ftp.retrlines('NLST', getBillNames)
logfile.write('Retrieved bill names.\n')

# Get every bill file and delete it from the server
for bill in bills:
	with open(bill, 'wb') as bd:
		ftp.retrbinary('RETR ' + bill, bd.write)
	ftp.delete(bill)
logfile.write('Retrieved and deleted bill files.\nClosing connection.\n')
ftp.quit()

# Parse Datafile
logfile.write('Parsing Data...\n')
fieldNames = [
	'rechnungsnummer', 'auftragsnummer', 'absendeort', 'rechnungsdatum', 'rechnungszeit', 'zahlungsziel',
	'herkunft', 'party_ID', 'kundennummer', 'name', 'adresse', 'plz_und_ort', '
	]
for bill in bills:
	with open(bill, 'r') as bd:
		reader = csv.DictReader(bill, delimiter=';')
		for row in reader:
			

logfile.close()
