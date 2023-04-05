# Here we collect functions concerning the cats_dict dictionaries. These are dictionaries of different
# expense categories containing lists of expense transactions as well as the sum of these expenses. They
# are used as part of the resaults dictionaries defined in results_dictionary.py. The format of the dictionaries
# is as defined as
# { '<category name>' : { 'sum_out' : <num>, 'transactions' : [
#       { 'in': <num>, 'out' : <num, ..}, { ...  }, ... ] }, '<category name2>' : { 'sum_out' : '<num>', 
#   ...}, { ... }, ... }

from aux_functions import formatNumber, matchesAnyOne
from tabulate import tabulate


# This function takes the dictionary associated with a single transaction and prints a nicely formatted string
# representing the transaction.
def printTransactionLine(transaction_dictionary):
    print(f"{transaction_dictionary['date_book'].strftime('%Y-%m-%d')}\t{formatNumber(transaction_dictionary['out'])}\t{transaction_dictionary['type']}\t{transaction_dictionary['text']}")


# ----------------------------------------------------------------------------------
# Creation functions
# ----------------------------------------------------------------------------------

# Initialize a dictionary where each key is the name of a category as defined in the settings,
# and the value of each such key is another dictionary. This dictionary contains a list which
# later will be populated with transaction data. It also contains variable sum_out
# which will be calculated after the list is populated.
def initializeCategories(settings_dict):
    cats_dict = {}
    for category in settings_dict['categories']:
        cats_dict[category['name']] = { "transactions" : [], "sum_out" : 0 }

    return cats_dict



# Takes accounting data in the form of a list of dicts and categorizes each element in this list according
# to the categories defined in settings_dict by using the lists of regex-patterns defined there.
# It also returns the remaining items that were not automatically categorized as a list.
# TODO: Make this only consider expenses and not income. Calculate total income by directly summing the accounting
# data without categorizing income data and remove the sum_in for each category.
# Account data takes the form [ {'date_book', 'date_rent', 'account_to', 'type', 'text', 'out', 'in'}, {...}, ... ]
def autoCategorizeExpenses(accounting_data, settings_dict):

    cats_dict = initializeCategories(settings_dict)
    categories = settings_dict['categories'] # List of dicts containg keys 'name' and 'regexes'
    remainder_list = []

    # Loop through the accounting data
    for line in accounting_data:
        # Only attemt to categorize expenses
        if line['out'] > 0:
            text = line['text']

            # Go through the list of categories to look for a place to put the line
            found_match = False
            for cat in categories:
                if matchesAnyOne(cat['regexes'], text):
                    # Put the line in the matching category.
                    cats_dict[cat['name']]['transactions'].append(line)
                    found_match = True
                    break

            # If the line was not found in any of the categories and we don't want to ignore it (meaning that
            # it is not found among the regexes in the skip_regexes list), then we save it for later in the remainder list.
            if (not found_match) and (not matchesAnyOne(settings_dict['skip_regexes'], text)):
                remainder_list.append(line)

    return cats_dict, remainder_list

def printCategoryChoiceHelp(options_menu, category_menu):
    print("Please select an option from the choices below.\n")
    print("Control options:")
    print(options_menu)
    print("Category options:")
    print(category_menu)

def validCategoryChoice(choice_str, enumerate_cat_names):
    if choice_str.isdigit() and int(choice_str) >= 0 and int(choice_str) < len(enumerate_cat_names):
        return True
    elif choice_str in ["a", "s", "e", "p", "h"]:
        return True
    else:
        return False

# Takes a list of accounting data and asks the user to choose which category to put each transaction in.
# Other options are as described in the options menu defined in the function.
def manuallyCategorizeData(cats_dict, accounting_data, settings_dict):
    remainder_list = []
    # Set the prompt used when asking for user input.
    prompt = settings_dict['prompt']

    # Generate category menu
    enumerated_cat_names = [f"  {i}: {k}" for i, k in enumerate(cats_dict.keys())]
    category_menu = '\n'.join(enumerated_cat_names)

    # Write help menu
    options_menu = """  a: Abort. Reset any previous choices and return.
  s: Skip. Put the transaction in a remainder list and continue to the next one.
  e: End. Skip the remaining transactions and return current choices.
  p: Print category choices.
  h: Print all available choices.
"""
    
    # Print categories
    print("For each transaction, please choose a category from the below list by typing the corresponding number.")
    print(category_menu)

    dict_keys = list(cats_dict.keys())
    # Create shallow backup copy of data dictionary
    backup_lists = [cats_dict[key]['transactions'][:] for key in dict_keys]

    # Loop through uncategorized data
    for i, line in enumerate(accounting_data):
        printTransactionLine(line)

        # Choice loop

        while True:
            choice_str = input(prompt)
            if not validCategoryChoice(choice_str, enumerated_cat_names):
                print(f'Invalid choice: \"{choice_str}\".')
                printCategoryChoiceHelp(options_menu, category_menu)
                continue
            elif choice_str.isdigit():
                choice = int(choice_str)
                cats_dict[dict_keys[choice]]['transactions'].append(line)
            elif choice_str == "a":
                # Reset all transaction lists to backups
                for i, key in enumerate(dict_keys):
                    cats_dict[key]['transactions'] = backup_lists[i]
                return
            elif choice_str == "s":
                remainder_list.append(line)
            elif choice_str == "e":
                return remainder_list + accounting_data[i:]
            elif choice_str == "p":
                print(category_menu)
                continue
            elif choice_str == "h":
                printCategoryChoiceHelp(options_menu, category_menu)
                continue
            else:
                raise Exception("This should not happen")
                exit(-1)
            break

    return remainder_list # After for-loop

# Takes a processed list of transactions and categorizes these transactions in cateogies defined in
# the settings_dict dictionary object.
def categorizeExpenses(accounting_data, settings_dict):

    # Use regexes from settings in order to categorize transactions of expenses.
    cats_dict, uncat_acc_data = autoCategorizeExpenses(accounting_data, settings_dict)
    #printCategories(cats_dict)

    # Manually categorize remaining expense transactions.
    remainder_list = manuallyCategorizeData(cats_dict, uncat_acc_data, settings_dict)
    #printCategories(cats_dict)

    return cats_dict, remainder_list



# ----------------------------------------------------------------------------------
# Input / Output functions
# ----------------------------------------------------------------------------------

# Prints all the transactions contained in the different categories in a nice format.
def printCategories(cats_dict):
    print("Transactions\n=============================================================", end='')

    # Loop through the different categories contained in the dictionary
    for name, cat_dict in cats_dict.items():
        print(f"\n{name}:")
        trans_list = cat_dict['transactions']
        # Check if the category is empty
        if len(trans_list) > 0:
            # Create list of list to be used in the tabulate module
            data = [[trans['date_book'].strftime('%Y-%m-%d'), formatNumber(trans['out']), trans['text']] for trans in trans_list]
            headers = ["Date Booked", "Out", "Comment"]
            print(tabulate(data, headers=[], colalign=("left", "right", "left"), disable_numparse=True))

        # Calculate category sums for out and in
        sum_out = sum([tr_line['out'] for tr_line in trans_list])
        sum_in = sum([tr_line['in'] for tr_line in trans_list])
        print(f"Sum In: {formatNumber(sum_in)} NOK,\tSum Out: {formatNumber(sum_out)} NOK")
    print("=============================================================")

# Takes a list of transactions and prints a table of it with numbers giving the indices of the transactions
# in the list.
def printExpensesTable(trans_list):
    if len(trans_list) <= 0:
        raise Exception("ERROR: tried to print empty list.")
    # Create list of list to be used in the tabulate module
    data = [[i, trans['date_book'].strftime('%Y-%m-%d'), formatNumber(trans['out']), trans['text']] for i, trans in enumerate(trans_list)]
    headers = ["Number", "Date Booked", "Out", "Comment"]
    print(tabulate(data, headers=[], colalign=("right", "left", "right", "left"), disable_numparse=True))


# Takes the list of category transactions, sums the categories that are relevant for 
# consumption commitments and then among the transactions in those categories asks whether
# any specific transactions should be excluded from the sum (i.e. subtracted).
def determineConsumptionCommitments(cats_dict, settings_dict):
    cons_commits = 0.0
    prompt = settings_dict['prompt']
    cons_commit_cats = settings_dict['consumption_commitment_categories']

    # Loop through consumption commitment categories
    for category_name in cons_commit_cats:
        cat_dict = cats_dict[category_name]
        cons_commits += cat_dict['sum_out']
        excluded_transactions = []
        included_transactions = cat_dict['transactions'][:]


        if len(included_transactions) > 0:
            # Get user input on which transactions should be subtracted
            print("Choose the numbers of any transactions below that should not be counted as consumption commitments.")
            print("Press 'x' to confirm current choices")
            printExpensesTable(included_transactions)
            while True:
                choice_str = input(prompt)
                if choice_str == "x":
                    break
                elif choice_str.isdigit() and int(choice_str) >= 0 and int(choice_str) < len(included_transactions):
                    # If the choice is valid: remove the element from the included list and place it in the excluded list.
                    excluded_transactions.append(included_transactions.pop(int(choice_str)))
                    printExpensesTable(included_transactions)
                else:
                    print(f"Invalid choice '{choice_str}', please try again.")

        # Subtract the excluded transactions from the consumption commitments sum
        exclusion_sum = sum([transaction['out'] for transaction in excluded_transactions])

        # Sanity check that things are right
        if  not abs(cat_dict['sum_out'] - exclusion_sum - sum([transaction['out'] for transaction in included_transactions])) < 0.1:
            print(f"Something went terribly wrong when calculating the consumption commitments of {category_name }")

        cons_commits -= exclusion_sum

    # End for loop
    return cons_commits


