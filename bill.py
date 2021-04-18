#
# Bill Class for Bill Script
#

import csv
import datetime
from io import StringIO


class BillInfo:
    def __init__(self, csv_line):
        field_names = [
            'bill_num', 'job_num', 'sender_location',
            'bill_date', 'bill_time', 'payment_target'
        ]
        f = StringIO(csv_line)
        reader = csv.DictReader(f, delimiter=';', fieldnames=field_names)
        for row in reader:
            self.bill_num = row['bill_num'].removeprefix('Rechnung_')  # Get rid of 'Rechnung' label
            self.job_num = row['job_num'].removeprefix('Auftrag_')  # Get rid of 'Auftrag' label
            self.sender_location = row['sender_location']
            self.bill_date = datetime.datetime.strptime(row['bill_date'], '%d.%m.%Y')
            self.bill_time = row['bill_time']
            self.payment_target = row['payment_target'].removeprefix('ZahlungszielInTagen_')  # Get rid of label


class Sender:
    def __init__(self, csv_line):
        field_names = [
            'label', 'party_ID', 'customer_num', 'name',
            'address', 'postcode_and_city', 'company_ID', 'email'
        ]
        f = StringIO(csv_line)
        reader = csv.DictReader(f, delimiter=';', fieldnames=field_names)
        for row in reader:
            self.party_ID = row['party_ID']
            self.customer_num = row['customer_num']
            self.name = row['name']
            self.address = row['address']
            self.postcode_and_city = row['postcode_and_city']
            self.company_ID = row['company_ID']
            self.email = row['email']


class Receiver:
    def __init__(self, csv_line):
        field_names = [
            'label', 'customer_ID', 'name',
            'address', 'postcode_and_city'
        ]
        f = StringIO(csv_line)
        reader = csv.DictReader(f, delimiter=';', fieldnames=field_names)
        for row in reader:
            self.customer_ID = row['customer_ID']
            self.name = row['name']
            self.address = row['address']
            self.postcode_and_city = row['postcode_and_city']


class BillItem:
    def __init__(self, csv_line):
        field_names = [
            'label', 'item_num', 'item_label',
            'amount', 'unit_price', 'total', 'VAT'
        ]
        f = StringIO(csv_line)
        reader = csv.DictReader(f, delimiter=';', fieldnames=field_names)
        for row in reader:
            self.item_num = row['item_num']
            self.item_label = row['item_label']
            self.amount = row['amount']
            self.unit_price = row['unit_price']
            self.total = row['total']
            self.VAT = row['VAT'].removeprefix('MWST_')  # Get rid of 'MWST' label


class Bill:
    def __init__(self, filename):
        self.filename = filename
        self.items = []

        with open(filename, 'r') as f:
            for line in f:
                # TODO: Constants/Config?
                if line.startswith('Rechnung'):
                    self.billInfo = BillInfo(line)
                elif line.startswith('Herkunft'):
                    self.sender = Sender(line)
                elif line.startswith('Endkunde'):
                    self.receiver = Receiver(line)
                elif line.startswith('RechnPos'):
                    self.items.append(BillItem(line))  # Add to list of items

        # Calculate other required info
        self.billInfo.totalVAT = 0.0
        for item in self.items:
            self.billInfo.totalVAT += (float(item.VAT.removesuffix('%')) / 100) * float(item.total)

        self.billInfo.total = self.billInfo.totalVAT
        for item in self.items:
            self.billInfo.total += float(item.total)

        self.billInfo.total_fr = int(self.billInfo.total)
        self.billInfo.total_rp = int(self.billInfo.total - int(self.billInfo.total))

        self.billInfo.pay_by = self.billInfo.bill_date + datetime.timedelta(days=int(self.billInfo.payment_target))