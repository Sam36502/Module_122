#
# Bill Class for Bill Script
#

class Sender:
	def __init__(self, csv_line):
		self.csv_line = csv_line
		
		

class Bill:
	def __init__(self, filename):
		self.filename = filename
		
		with open(filename, 'r') as f:
			lines = f.readlines()
		
