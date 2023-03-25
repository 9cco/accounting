# Here we collect all functions concerning accounting data, which is the result of reading transactions
# from a CSV-file. Accounting data is a list of dictionaries where each dictionary is formatted as
# 'date_book', 'date_rent', 'account_to', 'type', 'text', 'out', 'in'

from aux_functions import matchesAnyOne, formatNumber, eprint
from datetime import datetime
from tabulate import tabulate
import csv


# ----------------------------------------------------------------------------------
# Creation functions
# ----------------------------------------------------------------------------------

# Assume that the file path contains a file containing accounting data formatted as a CSV-file
# from Sbanken. Separate out the header and footer lines and accounting data and return these lines
# as separate Python lists.
def csvFileToLists(file_path, encoding="ISO-8859-1"):
    # Read the CSV file into a list
    try:
        with open(file_path, "r", newline='', encoding=encoding) as f:
            aux_list = list(csv.reader(f, delimiter=';'))
    except Exception as e:
        raise e
    # Create specific lists
    header = aux_list[0]
    footer = aux_list[-1]
    column_names = aux_list[2]
    account_data = aux_list[3:-2]
    # Return lists
    return (header, column_names, account_data, footer)

# Take in the list structure of an account CSV file and check that our assumptions are correct
# Return true if the lists are valid.
def validateCSVLists(header, column_names, account_data, footer):
    valid = True
    # Checking header list
    valid = valid and (len(header[5]) == 25 and header[0] == '')
    # Checking account_data
    valid = valid and len(account_data) > 0
    return valid


# Takes a string representing money and returns the floating point value
def formatMoney(money_string):
    if money_string != '':
        return float(money_string.replace(',','.'))
    else:
        return 0.0

# Formats the elements of a accounting_data list into the correct formats (see structureAcocuntDataToDicts
# for explanation).
def formatAccountingListLine(line):
    date_format = "%Y-%m-%d"
    date_book = datetime.strptime(line[0], date_format)
    date_rent = datetime.strptime(line[1], date_format)
    archive_ref = line[2]
    account_to = line[3]
    tr_type = line[4]
    text = line[5]
    tr_out = formatMoney(line[6])
    tr_in = formatMoney(line[7])

    return [date_book, date_rent, account_to, tr_type, text, tr_out, tr_in]


# Takes in account_data in the form of a list of lists which has been imported from a csv file. Each element in
# the outer list contains a list of 8 elements: date_booked, date_rent, archive_ref, account_to, type, text,
# out, and in. These elements are structured as dicts where we store the fields
# 'date_book', 'date_rent', 'account_to', 'type', 'text', 'out', 'in'
# The values are also deserialized into their respective python data-types.
def structureAccountDataToDicts(account_data):
    dicts = []

    for line in account_data:
        formatted_list = formatAccountingListLine(line)
        dict_line = { 'date_book': formatted_list[0], 'date_rent' : formatted_list[1],\
                'account_to' : formatted_list[2], 'type' : formatted_list[3], 'text' : formatted_list[4],\
                'out' : formatted_list[5], 'in' : formatted_list[6] }
        dicts.append(dict_line)

    return dicts

#We assume that the file path contains a valid CSV file and try to read it into a python list.
# This list is formatted so that each element is a dictionary containing the fields
#
# 'date_book', 'date_rent', 'account_to', 'type', 'text', 'out', 'in'
#
def readCSVAccountFile(file_path, encoding = "ISO-8859-1"):

    lists = csvFileToLists(file_path, encoding=encoding)

    if not validateCSVLists(*lists):
        eprint(f"ERROR: Invalid format of lists read from {file_path}!")
        exit(-1)
    
    account_data = lists[2]

    return structureAccountDataToDicts(account_data)

# Takes a completed list of dictionaries and checks that they have the correct data types for all elements.
def validateAccountingData(accounting_data):
    valid = True
    first_element_month = accounting_data[0]['date_book'].month
    for dic in accounting_data:
        # Checking data-types
        if not (isinstance(dic['date_book'], datetime) and isinstance(dic['date_rent'], datetime)\
                and isinstance(dic['account_to'], str) and isinstance(dic['type'], str)\
                and isinstance(dic['text'], str) and isinstance(dic['out'], float) and isinstance(dic['in'], float)):
            valid = False
            eprint(f"Error importing {dic}")
        # Checking if the element if in the same month as the first
        if not dic['date_book'].month == first_element_month:
            valid = False
            eprint(f"Date of {dic} does not match the first element's month")
    return valid

def importAndValidateCSV(path):
    try:
        accounting_data = readCSVAccountFile(path)
    except:
        eprint(f"ERROR importing file {path}")
        exit(-1)
    if not validateAccountingData(accounting_data):
        eprint(f"Invalid accounting data contained in file: {path}")
        exit(-1)

    return accounting_data



# ----------------------------------------------------------------------------------
# Processing functions
# ----------------------------------------------------------------------------------

# Sums all income listed in accounting data except for trasactions that match the skip-patterns from settings
def sumIncome(accounting_data, settings_dict):
    total = 0.0
    for line in accounting_data:
        if line['in'] > 0 and (not matchesAnyOne(settings_dict['skip_regexes'], line['text'])):
            total += line['in']
    return total


# ----------------------------------------------------------------------------------
# Input / Output functions
# ----------------------------------------------------------------------------------

# Print all income transactions nicely that are not excluded by the skip regexes.
def printIncome(accounting_data, settings_dict):
    data = [[trans['date_book'].strftime('%Y-%m-%d'), formatNumber(trans['in']), trans['text']] for trans in accounting_data if trans['in'] > 0 and (not matchesAnyOne(settings_dict['skip_regexes'], trans['text']))]
    headers = ["Date Booked", "In", "Comment"]
    print(tabulate(data, headers=headers, colalign=("left", "right", "left"), disable_numparse=True, tablefmt="rst"))
    return

# Returns a list of all the transaction dates in the accounting data.
def getTransactionDates(accounting_data):
    return [line['date_book'] for line in accounting_data]



