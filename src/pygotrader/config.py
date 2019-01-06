"""
Class for holding all of the current configuration information
 and loading secrets for connections to exchanges.  Also creates
 authenticated clients.
 
Secrets file format:

{"key":"12345",
 "b64secret":"1l2o3o4n5g",
 "passphrase":"pass123",
 "api_url":"https://api-public.sandbox.pro.coinbase.com"
 "websocket_url":"wss://ws-feed-public.sandbox.pro.coinbase.com"
}

"""

import json,os
from cbpro import AuthenticatedClient

class MyConfig(object):
    def __init__(self,exchange='coinbase',product='BTC-USD',api_url='https://api.pro.coinbase.com',
        websocket_url='wss://ws-feed.pro.coinbase.com'):
        self._exchange = exchange
        self._product = product
        self._key = ''
        self._b64secret = ''
        self._passphrase = ''
        self._api_url = api_url
        self._websocket_url = websocket_url

    @property
    def exchange(self):
        return self._exchange
        
    @property
    def product(self):
        return self._product

    @property
    def websocket_url(self):
        return self._websocket_url
        
    def load_secrets(self,path_to_secrets_file):
        secrets_file = open(path_to_secrets_file)
        secrets = json.load(secrets_file)
        self._key = secrets['key']
        self._b64secret = secrets['b64secret']
        self._passphrase = secrets['passphrase']
        self._api_url = secrets['api_url']
        self._websocket_url = secrets['websocket_url']
        
    def get_coinbase_authenticated_client(self):
        return AuthenticatedClient(key=self._key, 
                                b64secret=self._b64secret,
                                passphrase=self._passphrase,
                                api_url=self._api_url)