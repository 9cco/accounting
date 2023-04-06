import sys
import os

from oauthlib.oauth2 import BackendApplicationClient
import requests
from requests_oauthlib import OAuth2Session
import urllib.parse

from credential_protection import loadCredentials

# Use OAuth2 in order to get an authenticated session. The "secret" is also known as "password" in the Sbanken UI.
def getAuthenticatedSession(client_id, client_secret):
    # This follows the procedure for OAuth2 authentication using the "Backend Application Flow"
    # which is documented at, e.g.: https://requests-oauthlib.readthedocs.io/en/latest/oauth2_workflow.html

    auth_url = "https://auth.sbanken.no"
    token_url = f'{auth_url}/identityserver/connect/token'

    # Setup a requests.Session() object.
    client = BackendApplicationClient(client_id=client_id)
    session = OAuth2Session(client=client)

    # Do the actual authentication for the session to the API.
    # This call returns a dictionary of token, but is not needed since it is implicit in the session object.
    session.fetch_token(token_url=token_url, client_id=client_id, client_secret=client_secret)

    return session


# Read files to obtain credential information
#def getCredentials(folder_name = "credentials", client_id_fn = "sbanken_clientID.txt", client_secret_fn = "sbanken_secret.txt"):
#
#    dir_path = os.path.normpath(os.path.dirname(os.path.realpath(__file__)))
#    folder_path = f'{dir_path}/{folder_name}'
#    with open(f'{folder_path}/{client_id_fn}', 'r') as f:
#        client_id = f.read().strip()
#    with open(f'{folder_path}/{client_secret_fn}', 'r') as f:
#        client_secret = f.read().strip()
#
#    return client_id, client_secret

# Find the correct credential data in the credential list and return it.
def getCredentials(credentials, client_id_name = "sbanken_clientID", client_secret_name = "sbanken_secret"):

    client_id = None
    client_secret = None
    
    # Find the elements in the credential list containing the wanted credentials.
    for cred in credentials:
        if cred.name == client_id_name:
            client_id = cred.data
        elif cred.name == client_secret_name:
            client_secret = cred.data

    # Check that we have found the correct credentials.
    if client_id == None or client_secret == None:
        raise Exception(f"Error getCredentials: Needed credentials \n{client_id_name} or {client_secret_name}\n\
                are not located in loaded credentials.")

    return client_id, client_secret

# Call the Sbanken Accounts API and obtain an overview of the accounts. Returns json reply.
def callAPI(session, api_url = 'https://publicapi.sbanken.no/apibeta/api/v2/Accounts'):
    response_object = session.get(api_url)
    return response_object.json()

# Go through all balances and compute the total. The input is an Sbanken json object
def calculateTotalBalance(response):
    balance = 0.0

    for account_dict in response['items']:
        if account_dict['accountType'] == "Standard account":
            balance += account_dict['available']
        elif account_dict['accountType'] == "Creditcard account":
            balance += account_dict['balance']

    return balance

# Get the total balance on the account given access to by the credentials by calling the Sbanken API
def getTotalBalance(credentials):

    # First we read credentials from files in the folder 'credentials'.
    client_id, client_secret = getCredentials(credentials)

    #print(client_id + "\n" + client_secret)

    # URL-encode the client_id and client_secret.
    urlencoded_id = urllib.parse.quote(client_id)
    urlencoded_secret = urllib.parse.quote(client_secret)

    # Authenticate to the Sbanken API.
    session = getAuthenticatedSession(urlencoded_id, urlencoded_secret)
    # Call the Accounts API endpoint to get account information
    response = callAPI(session)

    # Sum the balance on the accounts returned.
    total_balance = calculateTotalBalance(response)

    # List cards
#    card_api_url = "https://publicapi.sbanken.no/apibeta/api/v2/Cards"
#    response = callAPI(session, api_url = card_api_url)
#    pprint(response)

    return total_balance



# Parse command-line arguments
def main(argv):

    credentials = loadCredentials()

    balance = getTotalBalance(credentials)
    print(round(balance, 2))
    




if __name__ == "__main__":
   main(sys.argv[1:])
