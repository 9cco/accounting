import requests
import json

# Find the amount of money in Norwegian Kroner one milli-bitcoin in worth by calling the coingecko API
def getNOKPrmBTC():
    # Set up the API endpoint and parameters
    api_endpoint = 'https://api.coingecko.com/api/v3/simple/price'
    currency = 'nok'
    crypto = 'bitcoin'

    # Make the API request and extract the exchange rate
    response_obj = requests.get(f'{api_endpoint}?ids={crypto}&vs_currencies={currency}')
    response = response_obj.json()
    
    return response[crypto][currency]/1000

