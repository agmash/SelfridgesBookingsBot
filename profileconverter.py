#!/usr/bin/python
 # -*- coding: utf-8 -*-
from time import time_ns
import xlrd
from collections import OrderedDict
import simplejson as json
# Open the workbook and select the first worksheet
wb = xlrd.open_workbook('Profiles/agNotify-profiles.xlsx')
sh = wb.sheet_by_index(0)

# List to hold dictionaries
cars_list = []
# Iterate through each row in worksheet and fetch values into dict
for rownum in range(1, sh.nrows):
    cars = OrderedDict()
    row_values = sh.row_values(rownum)
    cars['Timestamp'] = row_values[0]
    cars['Discord Username'] = row_values[1]
    cars['Discord ID'] = row_values[2]
    cars['ProfileName'] = row_values[3]
    cars['First Name'] = row_values[4]
    cars['Last Name'] = row_values[5]
    cars['Email'] = row_values[6]
    timePreferencesList = []
    timePreferences = row_values[7]
    if ';' in timePreferences:
        timePreferences = timePreferences.split(";")
        for time in timePreferences:
            timePreferencesList.append(time)
    else:
        timePreferencesList.append(timePreferences)
        timePreferences = timePreferencesList
    cars['Time Preferences'] = timePreferences
    cars['Instagram'] = row_values[8]
    cars['Nike Size'] = row_values[9]
    cars['Adidas Size'] = row_values[10]
    cars['Phone'] = row_values[11]
    cars['Shirt Size'] = 'M'
    cars['Trouser Size'] = 'M'
    cars['TYD What stores?'] = 'Kith, FOG'
    cars['Store ID'] = '37463'
    cars['Service ID'] = '54260'
    cars['Event Duration'] = '15'

    cars_list.append(cars)
# Serialize the list of dicts to JSON
j = json.dumps(cars_list, indent=4)
# Write to file
with open('Profiles/agNotify.json', 'w') as f:
    f.write(j)