"""
Class for holding all of the current configuration information
So far:

exchange
product
"""


class MyConfig(object):
    def __init__(self,exchange='coinbase',product='BTC-USD'):
        self.exchange = exchange
        self.product = product