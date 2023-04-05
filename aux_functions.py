import sys
import re
import os
import json

# Function for printing to stderr
def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)

# Check if any of the regex expressions in a list has any match in a string.
# Return True / False
def matchesAnyOne(regex_list, string):
    for regex in regex_list:
        if re.search(regex, string.lower()):
            return True
    return False


# Returns the string representation of a floating point number num according to standard accounting convention.
def formatNumber(num):
    return "{:,.2f}".format(num)

# Dumps a dictionary object to a file in the current folder given by filename.
def saveDictToJson(dictionary, filename):
    with open(filename, 'w') as file:
        json.dump(dictionary, file)
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
    
    raise Exception(f"ERROR: Could not find settings file at: \n{conf_path}")
    return

