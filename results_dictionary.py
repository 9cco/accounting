# Here we place all the functions that manipulate and operate on the results dicionaries
#
# These dicionaries follow the format
# { 'categories' : { <categories dictionary> }, 'sum_in', 'sum_out', 'sum_cons_commit', 'total_balance',
#   'date', 'nok_mbtc', 'mbtc', 'start_date', 'end_date'}

# sum_in: sum of processed income transactions
# sum_out: sum of processed expenses
# sum_cons_commit: sum of expenses that are considered consumption commitments
# total_balance: the sum of the balances of the accounts in Sbanken at the time of processing
# date: the date the dictionary was processed / updated
# nok_mbtc: exchange rate between NOKs and mBTC at the time of processing.
# mbtc: current amount of mBTC in the owners posession.
# start_date: the date of the first processed expense transaction
# end_date: the date of the last processed expense transaction
# categories: a dictionary containing all expense transactions sorted into categories following the format
# { '<category name>' : { 'sum_out' : <num>, 'transactions' : [
#       { 'in': <num>, 'out' : <num, ..}, { ...  }, ... ] }, '<category name2>' : { 'sum_out' : '<num>', 
#   ...}, { ... }, ... }
#
# Note that dates are stored in datetime-objects

from datetime import datetime
from aux_functions import formatNumber, eprint, saveDictToJson
from accounting_data import sumIncome, getTransactionDates
from categories_dictionary import determineConsumptionCommitments
from sbanken_api import getTotalBalance
from btc_api import getNOKPrmBTC
from tabulate import tabulate
import matplotlib.pyplot as plt
import csv
import json
import os



# ----------------------------------------------------------------------------------
# Creation functions
# ----------------------------------------------------------------------------------

def initializeResults(cats_dict):
    return { "categories" : cats_dict, "sum_in" : 0, "sum_out" : 0, "sum_cons_commit" : 0, "total_balance" : 0, "date" : datetime.now(), "nok_mbtc" : 0, "mbtc" : 0, "start_date" : datetime.now(), "end_date" : datetime.now() }

# Takes the completed category lists and calculates the sum in and out of the transactions
# contained in them: for each and also totally. Additionally determines the consumption commitment.
def calculateResults(cats_dict, accounting_data, settings_dict, credentials):
    results_dict = initializeResults(cats_dict)

    cats_dict = results_dict['categories']
    cat_keys = cats_dict.keys()

    for cat_key in cat_keys:
        transaction_list = cats_dict[cat_key]['transactions']
        cats_dict[cat_key]['sum_out'] = sum([trans['out'] for trans in transaction_list])

    # Calculate sum of income directly from the accounting data
    results_dict['sum_in'] = sumIncome(accounting_data, settings_dict)

    # We remove investments when calculating the sum of the expenses
    exp_keys = list(cat_keys)
    exp_keys.remove('investments')
    results_dict['sum_out'] = sum([cats_dict[key]['sum_out'] for key in exp_keys])

    results_dict['sum_cons_commit'] = determineConsumptionCommitments(cats_dict, settings_dict)
    
    if len(credentials) > 0:
        try:
            results_dict['total_balance'] = getTotalBalance(credentials)
        except:
            eprint("Error: Could not get total balance")
            results_dict['total_balance'] = 0
    else:
        eprint("Error: no credentials supplied. Cannot determine total balance. Setting it to 0")
        results_dict['total_balance'] = 0
    try:
        results_dict['nok_mbtc'] = getNOKPrmBTC()
    except:
        eprint("Error: Could not get Bitcoin exchange rate")
        results_dict['nok_mbtc'] = 300

    # Load amount of current bitcoins from settings
    results_dict['mbtc'] = settings_dict['mBTC']

    # Find start and end-date of transactions
    results_dict['start_date'] = min(getTransactionDates(accounting_data))
    results_dict['end_date'] = max(getTransactionDates(accounting_data))

    return results_dict


# ----------------------------------------------------------------------------------
# Saving functions
# ----------------------------------------------------------------------------------

# Take a datetime object and formats it according to the format YYYY-mm
def getOutFileDate(date, format_string = "%Y-%m"):
    return date.strftime(format_string)

# Returns the out-file string corresponding to the start date in a results dictionary
def getOutFileDateFromResults(results_dict):
    return getOutFileDate(results_dict['start_date'])

# Converts all the datetime-objects in the results dictionary to strings in an isoformat.
# The datetime object we needed to convert are deep in the results_dict dictionary, located at
# results_dict['categories']['<cat name>']['transactions'][<n>]['date_book']/['date_rent']
def convertResultDatetimesToStrings(results_dict):
    cats_dict = results_dict['categories']
    for cat_name in cats_dict:
        for trans in cats_dict[cat_name]['transactions']:
            trans['date_book'] = trans['date_book'].isoformat()
            trans['date_rent'] = trans['date_rent'].isoformat()
    results_dict['start_date'] = results_dict['start_date'].isoformat()
    results_dict['end_date'] = results_dict['end_date'].isoformat()
    results_dict['date'] = results_dict['date'].isoformat()
    return


# Does the same as the above, but in reverse.
def convertResultStringsToDatetimes(results_dict):
    cats_dict = results_dict['categories']
    for cat_name in cats_dict:
        for trans in cats_dict[cat_name]['transactions']:
            trans['date_book'] = datetime.fromisoformat(trans['date_book'])
            trans['date_rent'] = datetime.fromisoformat(trans['date_rent'])
    results_dict['start_date'] = datetime.fromisoformat(results_dict['start_date'])
    results_dict['end_date'] = datetime.fromisoformat(results_dict['end_date'])
    results_dict['date'] = datetime.fromisoformat(results_dict['date'])
    return

# Creates the name of the save file for the json given a date (default is current date)
def getSaveFileName(date=datetime.now()):
    out_file_date = getOutFileDate(date)
    return "monthly_results_" + out_file_date + ".json"



# ----------------------------------------------------------------------------------
# Combination functions
# ----------------------------------------------------------------------------------

# The categories dictionaries a b both have the format
# { '<category name>' : { 'sum_out' : <num>, 'transactions' : [
#       { 'in': <num>, 'out' : <num, ..}, { ...  }, ... ] }, '<category name2>' : { 'sum_out' : '<num>', 
#   ...}, { ... }, ... }
def combineCategories(a, b):
    keys = a.keys()
    c = {}
    for key in keys:
        c[key] = {}
        c[key]['sum_out'] = a[key]['sum_out'] + b[key]['sum_out']
        c[key]['transactions'] = a[key]['transactions'] + b[key]['transactions']
    return c

# returns the latest dictionary given two results dictionaries.
def latest(a_dict, b_dict):
    if a_dict['date'] > b_dict['date']:
        return a_dict
    else:
        return b_dict

# Takes two result dictionaries and combines them into a new result consisting of the sum of the two.
def addResults(dict1, dict2):
    # Concatinate the transactions in the different categories.
    cats_sum = combineCategories(dict1['categories'], dict2['categories'])
    sum_dict = initializeResults(cats_sum)
    sum_dict['sum_in'] = dict1['sum_in'] + dict2['sum_in']
    sum_dict['sum_out'] = dict1['sum_out'] + dict2['sum_out']
    sum_dict['sum_cons_commit'] = dict1['sum_cons_commit'] + dict2['sum_cons_commit']
    latest_dict = latest(dict1, dict2)
    sum_dict['total_balance'] = latest_dict['total_balance']
    sum_dict['date'] = datetime.now()
    sum_dict['nok_mbtc'] = latest_dict['nok_mbtc']
    sum_dict['mbtc'] = latest_dict['mbtc']
    sum_dict['start_date'] = min(dict1['start_date'], dict2['start_date'])
    sum_dict['end_date'] = max(dict1['end_date'], dict2['end_date'])
    return sum_dict



# ----------------------------------------------------------------------------------
# Input / Output functions
# ----------------------------------------------------------------------------------

def printHelp():
    eprint("\nUse:")
    eprint(":~$ py monthly_accounting.py <accounting csv file>\n")
    eprint("Here <accounting csv file> is the path to the file that contains your exported expenses from Sbanken.")

# Assume the path is to a json file containing a json file dump.
def importOldResults(path):
    with open(path, 'r') as file:
        results_dict = json.load(file)

    # Now we have to convert all the strings corresponding to dates, back into dates.
    convertResultStringsToDatetimes(results_dict)

    return results_dict

# Saves the results dictionary to a file given by output_fn by first transforming all datetime objects
# into isofrmatted strings.
def saveResults(results_dict, output_fn, silent=False):
    if not silent and os.path.isfile(output_fn):
        choice = input(f"Warning: file {output_fn} already exists. Overwrite? (y/n): ")
        if not ('y' in choice or 'Y' in choice):
            return
    convertResultDatetimesToStrings(results_dict)
    saveDictToJson(results_dict, output_fn)

    # Remember to convert back to datetime, since the results_dict might be used later.
    convertResultStringsToDatetimes(results_dict)
    return


# Takes a dictionary of results and prints it nicely.
def printResults(results_dict):

    cats_dict = results_dict['categories']
    cat_keys = cats_dict.keys()

    cat_names = list(cats_dict.keys())
    outs = [formatNumber(cats_dict[name]['sum_out']) for name in cat_names]
    total_sum = sum([cats_dict[name]['sum_out'] for name in cat_names])
    outs_percent = [round(cats_dict[name]['sum_out']/max(total_sum, 0.01)*100, 1) for name in cat_names]
    headers = ["Category", "OUT\n[NOK]", "OUT\n[%]"]
    data = [[cat_names[i], outs[i], outs_percent[i]] for i in range(len(cat_names))]

    print("\nExpense categories:")
    print(tabulate(data, headers=headers, colalign=("left", "right", "right"), disable_numparse=True, tablefmt="rst"))

    # Printing individual categories
#    print("\nCategories\n-----------------------------------------------------")
#    for name, category in cats_dict.items():
#        print(f"{name}: {formatNumber(category['sum_in'])} NOK in, {formatNumber(category['sum_out'])} NOK out")
#    print("-----------------------------------------------------\n")

    sum_in = results_dict['sum_in']
    sum_out = results_dict['sum_out']
    profit = sum_in - sum_out
    sum_cc = results_dict['sum_cons_commit']
    balance = results_dict['total_balance']
    nok_pr_mbtc = results_dict['nok_mbtc']
    mbtc = results_dict['mbtc']
    start_date = results_dict['start_date'].strftime("%d/%m")
    end_date = results_dict['end_date'].strftime("%d/%m/%Y")
    print(f"\nIn total for transactions between {start_date} and {end_date}")
    print(f"In:\t{formatNumber(sum_in)} NOK")
    print(f"Out:\t{formatNumber(sum_out)} NOK")
    print(f"Sbanken Balance:\t\t{formatNumber(balance)} NOK")
    print(f"Bitcoin Balance:\t\t{formatNumber(nok_pr_mbtc*mbtc)} NOK")
    print(f"Consumption commitments:\t{formatNumber(sum_cc)} NOK")
    print(f"Consumption fraction:\t\t{round(sum_cc/(max(0.01, sum_in))*100, 2)} %")
    print(f"Operating profit:\t\t{formatNumber(profit)} NOK")
    print(f"Operating margin:\t\t{round(profit/(max(0.01, sum_in))*100, 2)} %")
    print()


# This writes an output string that can be imported directly into my spreadsheet program.
def writeOutput(results_dict, output_file, settings_dict):
    cats = results_dict['categories']
    category_order = settings_dict['write_order']

    # Insert date string
    output_list = [results_dict['end_date'].strftime('%Y-%m')]

    # Insert category sums in correct order
    for category_name in category_order:
        if category_name in cats:
            output_list.append(round(cats[category_name]['sum_out'],2))
        else:
            output_list.append(0.0)

    # After all category expenses are inserted we need an extra element
    output_list.append('')

    # Then we write total in, out, profit and consumption commitment fraction
    # The consumption commitment fraction is the fraction of income spent on consumption commitments.
    sum_in = round(results_dict['sum_in'], 2)
    sum_out = round(results_dict['sum_out'], 2)
    profit = sum_in - sum_out
    if sum_in > 0:
        cc_perc = round(results_dict['sum_cons_commit'] / sum_in, 6)
    else:
        cc_perc = 'inf'
    output_list += [sum_in, sum_out, profit, cc_perc]

    # Then we add the bitcoin exchange rate, total account balance and total bitcoin value
    output_list += [results_dict['nok_mbtc'], results_dict['total_balance'], results_dict['nok_mbtc']*results_dict['mbtc']]

    # Skip one column for stocks and insert total crypto

    with open(output_file, 'w', newline='') as f:
        writer = csv.writer(f, delimiter='\t')
        writer.writerow(output_list)


# Plot a horizontal histogram of the different expense categories.
def plotResults(results_dict, output_fn):

    # Generate x and y lists
    categories = results_dict['categories']
    cat_names = list(categories.keys())
    cat_sums = [categories[cat_name]['sum_out'] for cat_name in cat_names]

    # Convert the date in the results to a datetime-object.
    report_date = results_dict['end_date']
    date_string = report_date.strftime("%B %Y")

    # Set bar colors according to Okabe & Ito standards
    bar_col = (204, 121, 167)
    bar_col = tuple(val/255 for val in bar_col)

    fig, ax = plt.subplots(figsize=(12, 8))
    ax.barh(cat_names, cat_sums, color=bar_col, facecolor=bar_col, edgecolor=bar_col)
    ax.invert_yaxis()
#    ax.barh(cat_names, cat_sums, facecolor='white', color=bar_col)
    plt.xticks(rotation=-60)
    plt.title(f'Monthly Expenses for {date_string}')
    plt.xlabel('Amount [NOK]')
    plt.ylabel('Category')
    plt.grid(axis='x')

    plt.savefig(output_fn)
    return

# Exports results by creating plot and writing output csv file and copying it to the cliboard
def exportResults(results_dict, settings_dict):

        out_file_date = getOutFileDateFromResults(results_dict)
        plot_filename = f'monthly_overview_{out_file_date}.pdf'
        output_fn =  "monthly_overview_" + out_file_date + ".csv"

        # Make a nice plot of the different expenses using matplotlib
        plotResults(results_dict, plot_filename)

        # Write processed data into a CSV file for easy import into spreadsheet programs
        writeOutput(results_dict, output_fn, settings_dict)

        # Do a system command to copy the file data into the clipboard
        cmd = "cat " + output_fn + "| xclip -sel clip"
        os.system(cmd)

        # Do a system command to show the pdf-file
        cmd = "evince " + plot_filename + " 2>&1 1>/dev/null &"
        os.system(cmd)
        return


