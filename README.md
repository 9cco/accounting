Monthly Accounting
======================================================

![Visitors](https://visitor-badge.glitch.me/badge?page_id=9cco.accounting)
[![Say Thanks!](https://img.shields.io/badge/Say%20Thanks-!-1EAEDB.svg)](https://saythanks.io/to/9cco)

This python script calculates and presents an overview of monthly expendidatures and incomes.
It takes a csv files generated by exporting a month of transactions from an account in Sbanken.
This file needs to have "Skilletegn/delimiter" = "semikolon/semi colon" and "desimaltegn/decimal separator" = "komma/comma". 

The script first goes through all the expendidatures in the files and attempts to sort them in categories
acording to the categories and search strings / regex-patterns defined in the settings.conf file. For the transactions
that it was not able to automatically sort it asks you the user to sort them through an input dialoge.

Once the expenses are sorted, the script also asks the user what transactions to consider as "consumption commitments". Consumption commitments refer to the expenses that an individual commits to on a regular basis in order to maintain their standard of living. These expenses can include things like rent or mortgage payments, utilities, groceries, transportation costs, insurance premiums, and other monthly bills. The categories to consider as consumption commitments are defined in settings.conf. The script asks the user to remove any individual transaction in these categories the user does not think should be considered a consumption commitment.

Finally the script makes a few API-calls in order to get the current account balance and bitcoin exchange rate. The current amount of bitcoin in the users posession is defined in settings.conf.

The script then prints all the results to the console with some nice crushing of the numbers giving some key economic figures such as operating margin and consumption commitment fraction (this should ideally be below 30 %). It plots a nice horizontal histogram to visualize the spending on the different categories as shown in Fig. 2 and also writes a result-string to a tab-separated csv file. This string is then copied to the users clipboard in order for easy pasting into any spreadsheet program.

## Installation

1. Download the script folder.
2. Edit the settings.conf json file by inserting the number of bitcoins in you possession, what categories you want and what search strings in each category, what categories should be considered consumption commitments, and specify skip regexes if any transactions should be automatically skipped (like internal tranfers between accounts). An example settings file is included in the file `settings.example`. Use this as a starting point and rename it to `settings.conf` when you are done.
3. Add the line `alias accounting='python3 <path to script folder>/monthly_accounting.py'` to your `.bash_aliases` file (assuming you have the line `. ~/.bash_aliases` somewhere in your `.bashrc` file).

In order to have the nice API-calls:  
4. You need to enable Sbanken beta and download your client_id (api-key) and client_secret (password).
5. Make a new directory in the script folder called **credentials**.
6. In this folder, place the client_id in a file called **sbanken_clientID.txt** and client_secret in a file called **sbankoen_secret.txt**. This can be done, e.g., by issuing the following commands
```bash
echo "4vjeri549fdsklrgjei596gfdoivj549" > sbanken_api_key.txt
echo "pekv=IFE4BVIDFDxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx" > sbanken_secret.txt
```

## Use

After the above installation, you should be ready to use the script by downloading your csv-filed from Sbanken.
Then if you navigate to the folder of the file you simply issue the command
```bash
accounting 984357438_2023_02_01-2023_02_28.csv
```
to start the script.

After starting the first time you will probably want to go back to the settings.conf file and add more searches to the regexes in order to automatically categorize transactions. Don't be afraid to exit out of the script by pressing **CTRL** + **C** at any time.

When manually categorizing transactions you are supposed to input the number of the category as the scripts instructs you. There are also other options you can press in this state. Insert 'h' to get the full menu which consists of, in addition to the category options, the control  options:
-  a: Abort. Reset any previous choices and return.
-  s: Skip. Put the transaction in a remainder list and continue to the next one.
-  e: End. Skip the remaining transactions and return current choices.
-  p: Print category choices.
-  h: Print all available choices.

### Advanced usage

```
usage: monthly_accounting.py [-h] [-i <csv file>] [-p] [-e] [-s <json file-path>]
                             [--income <csv file>]

Categorize and generate financial figures for an individuals spending over a certain
month. Do this by reading the account statements provided as a csv-file exported from
Sbanken.

options:
  -h, --help            show this help message and exit
  -i <csv file>, --import <csv file>
                        Import expenses in <csv file> into categories and store them
                        in an output json file named after the month-year (-s can be
                        used to specify this).
  -p, --print           Looks for a saved json file and only prints output (does not
                        generate pdfs etc.)
  -e, --export          Looks for an already saved json file and outputs the results
                        in this file by creating plot, generating ouput csv file and
                        copying its content to the clipboard.
  -s <json file-path>, --save-file <json file-path>
                        Specifies the name of the json-file used to save the results.
  --income <csv file>   Imports the file in <csv file>, but instead of categorizing
                        expenses, prints the income statements contained.
```


### Requirements

The script requires python3

**Python modules**  
Essentials:  
- sys
- os
- json
- csv
- re
- tabulate
- datetime
- matplotlib.pyplot

To make the API-calls work we also need  
- oauthlib.oauth2
- requests_oauthlib
- requests
- urllib.parse

**Linux command**  
In order to show the plot and copy to clipboard, we use the linux commands  
- cat
- xclip
- evince

So for the nice automation, these need to be installed.
