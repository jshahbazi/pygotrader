"""
Class for holding all of the current configuration information
 and loading secrets for connections to exchanges.  Also creates
 authenticated clients.
 
Config file format:

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
        
    def load_config(self,path_to_config_file):
        config_file = open(path_to_config_file)
        config = json.load(config_file)
        self._key = config['key']
        self._b64secret = config['b64secret']
        self._passphrase = config['passphrase']
        self._api_url = config['api_url']
        self._websocket_url = config['websocket_url']
        
    def get_coinbase_authenticated_client(self):
        return AuthenticatedClient(key=self._key, 
                                b64secret=self._b64secret,
                                passphrase=self._passphrase,
                                api_url=self._api_url)