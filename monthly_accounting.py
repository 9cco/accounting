import sys
import os
import argparse
import json

from aux_functions import eprint
from results_dictionary import getSaveFileName, importOldResults, addResults, saveResults, printResults, exportResults, calculateResults, printHelp
from accounting_data import printIncome, importAndValidateCSV
from categories_dictionary import categorizeExpenses

# Takes the path to a CSV file, checks if the path is valid and then processes the transactions
# contained in it into a results dictionary
def importResultsFromCSV(import_path, settings_dict):

    import_path = os.path.normpath(import_path)
    # Check if it is a valid file path
    if not os.path.isfile(import_path):
        parser.print_usage(sys.stderr)
        eprint(f"ERROR: {import_path} is invalid file-path")
        exit(-1)

    # Now attempt to import the file.
    accounting_data = importAndValidateCSV(import_path)

    cats_dict, remainder_list = categorizeExpenses(accounting_data, settings_dict)
    if len(remainder_list) > 0:
        print(f"Warning: The file {import_path} still has {len(remainder_list)} uncategorized transactions.")

    # Determine Consumption commitments and calculate category sums.
    results_dict = calculateResults(cats_dict, accounting_data, settings_dict)

    return results_dict, accounting_data

# Reads a file specified from the file-path assuming that it is a CSV file containing transactions.
# Categorizes these transactions in categories defined in the settings_dict and produces a monthly overview
# of the finances including a plot, console output and csv-values copied to clipboard ready to be imported
# into spreadsheet programs.
def processCSVTransactionsToMonthlyOverview(file_path, settings_dict):

    results_dict, accounting_data = importResultsFromCSV(file_path, settings_dict)

    # Print income to console
    print("\nIncome transactions:")
    printIncome(accounting_data, settings_dict)

    # Print overview over results
    printResults(results_dict)
    # Generate output files (.pdf and .csv) and copy to clipboard.
    exportResults(results_dict, settings_dict)

    # Save results to file.
    results_fn =  getSaveFileName(accounting_data[0]['date_book'])
    # We have to first convert all the datetime objects to strings using .isoformat()
    saveResults(results_dict, results_fn)

    return

# Implements the logic of the command-line arguments.
def advancedUsage(parser, settings_dict):

    cli_input = parser.parse_args()

    # We start by seeing if an import argument was given
    no_results = False
    import_path = cli_input.imp
    if import_path != '' and import_path != None:

        print(f"Importing account information from {import_path}")
        results_dict, accounting_data = importResultsFromCSV(import_path, settings_dict)

        # Now we need to determine if there exists a file which the imported statements should be added to.
        save_path = cli_input.save_file
        if save_path == '' or save_path == None:
            print("No save file name specified. Generating from imported data.")
            # This means that no save-file argument was given. However an existing results file might still exist.
            # Try to find it by using the default file name of the current results. 
    
            # Set the save filename according to the date in the accounting data
            save_path = getSaveFileName(accounting_data[0]['date_book'])

        save_path = os.path.normpath(save_path)
        dont_ask = False
        if os.path.isfile(save_path):
            print(f"Existing file detected at {save_path}.\nCombining with information imported from {import_path}.")
            # We are now in a situation where we need to add the imported results into the existing file-information
            # and save this.

            old_results = importOldResults(save_path)
            results_dict = addResults(old_results, results_dict)
            dont_ask = True

        saveResults(results_dict, save_path, silent=dont_ask)

    else: # We can assume that no import file path was given, however an already existing file with results might still
        # exist. This file could be used with -p or -e to generate output.

        # Check if save-path was given as a command-line argument
        save_path = cli_input.save_file
        if save_path == '' or save_path == None:
            # If no path was given, try to find the file using the current date
            save_path = getSaveFileName()

        save_path = os.path.normpath(save_path)
        if os.path.isfile(save_path):
            print(f"Importing previously saved data from {save_path}")
            results_dict = importOldResults(save_path)
        else:
            # In this case we have failed to find any old results and also failed to import any new ones.
            no_results = True

    # Check if we should print income from some csv file
    income_path = cli_input.income
    if income_path != '' and income_path != None:

        income_path = os.path.normpath(income_path)
        if os.path.isfile(income_path):

            # Now attempt to import the file.
            income_accounting_data = importAndValidateCSV(income_path)

            # Print income statements in file to console.
            print("\nIncome transactions:")
            printIncome(income_accounting_data, settings_dict)

    if not no_results:
        # We can assume that results_dict exists.

        # Check if we should print results.
        if cli_input.pri:
            # Print results to console
            printResults(results_dict)

        if cli_input.export:
            exportResults(results_dict, settings_dict)
    
    return

# Function that tries to read a JSON file in the same folder as the script and return that file as a dict.
# In this program it is used to load the script file
def loadJsonFile(filename):
    # Get current script folder path
    script_folder = os.path.normpath(os.path.dirname(os.path.realpath(__file__)))
    conf_path = script_folder + "/" + filename
    
    if os.path.exists(conf_path):
        with open(conf_path, "r") as f:
            conf_dict = json.load(f)
        return conf_dict
    
    printHelp()
    eprint(f"Could not find settings file at: \n{conf_path}")
    exit(-2)


# Parse command-line arguments
#
# What we want here is to have the behavior.
# --import <csv file>
#   This imports the transactions in the csv file and generates results_dict which is saved to a json file, but
#   doesn't generate any normal output like plots and printouts etc. If a json file with the same month-year
#   combination already exists, it instead of overwriting it first loads the results from this, and then adds
#   the new results to the old ones and saves the updated results.
# --export
#   Looks for an already saved json file and outputs the results from this. This will then not be able to print
#   the income statements, since the json file only contains expenses.
# --print
#   Looks for saved json file and only prints output (does not generate pdf etc.)
# --save-file
#   Specified the name of the json file where the results are saved.
# --income <csv file>
#   Imports the csv file, but instead of categorizing expenses, prints the income statements contained.
# monthly_accounting.py [--import <csv file>] [--output]
def main(argv):

    try:
        # Treat everything after the python script as a path to the input file.
        file_path = os.path.normpath(''.join(argv))
    except:
        printHelp()
        eprint(argv)
        sys.exit(2)

    # Load settings from configuration file.
    settings_file = "settings.conf"
    settings_dict = loadJsonFile(settings_file)

    if not os.path.isfile(file_path):

        # If the argument after the script name is not a valid file-path, we try to see
        # if the arguments can be parsed according to optional arguments

        parser = argparse.ArgumentParser(prog='monthly_accounting.py',
        description='Categorize and generate financial figures for an individuals spending over a certain month. Do this by reading the account statements provided as a csv-file exported from Sbanken.')

        parser.add_argument('-i', '--import', metavar='<csv file>', help='Import expenses in %(metavar)s into categories and store them in an output json file named after the month-year (-s can be used to specify this). ', dest='imp')
        parser.add_argument('-p', '--print', action='store_true', help='Looks for a saved json file and only prints output (does not generate pdfs etc.)', dest='pri')
        parser.add_argument('-e', '--export', action='store_true', help='Looks for an already saved json file and outputs the results in this file by creating plot, generating ouput csv file and copying its content to the clipboard.')
        parser.add_argument('-s', '--save-file', metavar='<json file-path>', help='Specifies the name of the json-file used to save the results.')
        parser.add_argument('--income', metavar='<csv file>', help='Imports the file in %(metavar)s, but instead of categorizing expenses, prints the income statements contained.')

        advancedUsage(parser, settings_dict)

    else:
        # After determining that the argument is a file-path: we process the file contained there.
        processCSVTransactionsToMonthlyOverview(file_path, settings_dict)
        
    return

if __name__ == "__main__":
   main(sys.argv[1:])
   
