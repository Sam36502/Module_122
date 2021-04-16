#
# Gets the receipt from the payment
# server, sends an email to the
# Sender, and stores an archive on
# the payment server
#
import os
from datetime import datetime
from ftplib import FTP
from bill import Bill

# Constants
# TODO: Config File
LOG_FILE = './latest.log'

PAYSERVER_HOSTNAME = '134.119.225.245'
PAYSERVER_USERNAME = '310721-297-zahlsystem'
PAYSERVER_PASSWORD = 'Berufsschule8005!'
PAYSERVER_PATH = 'in/AP18aPearce'

# Functions
def log(str):
    now = datetime.now()
    current_time = now.strftime("[%Y/%m/%d - %H:%M:%S] ")
    logfile.write(current_time + str + '\n')

# Starting logger
logfile = open(LOG_FILE, 'a')
logfile.write(' -- Bill Retriever Log --\n\n')

# Connect to Server
log('Connecting to server...')
ftp = FTP(PAYSERVER_HOSTNAME)
ftp.login(PAYSERVER_USERNAME, PAYSERVER_PASSWORD)
# TODO: Check if connection was successful
log('Logged in successfully.')
ftp.cwd(PAYSERVER_PATH)

# Retrieve Receipt


# Get bill info
(_, _, filenames) = os.walk('./').next()
log('Parsing Data...')
bills = []
for f in filenames:
    if f.startswith('rechnung'):
        bills.append(Bill(f))
# TODO: Check parsing was successful
log('Data Parsed Successfully.')

log('End of Script.')
logfile.close()