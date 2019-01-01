from argparse import Action, ArgumentParser
import os

exchanges = ['coinbase']
products = ['BTC-USD','ETH-USD','LTC-USD']


class ExchangeArgumentAction(Action):
    def __call__(self, parser, namespace, values, option_string=None):
        exchange = values
        if exchange.lower() not in exchanges:
            parser.error("Unknown exchange")
        namespace.exchange = exchange.lower()

class SecretsArgumentAction(Action):
    def __call__(self, parser, namespace, values, option_string=None):
        secrets_file_name = values
        if os.path.isfile(secrets_file_name):
            pass
        else:
            parser.error("Secrets file does not exist")
        namespace.secrets = secrets_file_name
            
class ProductArgumentAction(Action):
    def __call__(self, parser, namespace, values, option_string=None):
        product = values
        if product.upper() not in products:
            parser.error("Unknown product")
        namespace.product = product.upper()            

def create_parser():
    parser = ArgumentParser(description="")
    parser.add_argument("--exchange", 
        help=f"Exchange to connect to.  Currently supported exchanges: {exchanges}",
        metavar=("EXCHANGE"),
        action=ExchangeArgumentAction,
        required=True)
    parser.add_argument("--secrets", 
        help="File that contains API secrets required to connect to your exchange",
        metavar=("SECRETS_FILE"),
        action=SecretsArgumentAction,
        required=False)  
    parser.add_argument("--product", 
        help=f"Coin pairing to trade with.  Currently supported products: {products}",
        metavar=("PRODUCT"),
        action=ProductArgumentAction,
        required=True) 
    return parser