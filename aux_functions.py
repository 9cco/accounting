import sys
import re

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

