import time, sys, os 
from datetime import datetime
from termcolor import colored

class Logger:
	def __init__(self, tid):
		self.format = '%d/%m/%y | %H:%M:%S.%f'
		self.tid = str(tid)


	def log(self, text, color=None, file=None, messagePrint=False, logType='error'):
		timestamp = '[' + datetime.now().strftime(self.format)[:-3] + ']'

		timestamp_colour = colored(timestamp, "yellow")
		message_clear = '{} : Task [{}] : {}'.format(timestamp, self.tid, text)
		if color is not None:
			try:
				text = colored(text, color)
			except:
				print('WARNING: unrecognized color passed to logger instance')

		if file is not None:
			with open(file, 'a') as txt:
				txt.write(message_clear + '\n')

		if messagePrint:
			print('{} : Task [{}] : {}'.format(timestamp_colour, self.tid, text))