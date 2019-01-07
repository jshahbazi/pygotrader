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

class ConfigArgumentAction(Action):
    def __call__(self, parser, namespace, values, option_string=None):
        config_file_name = values
        if os.path.isfile(config_file_name):
            pass
        else:
            parser.error("Config file does not exist")
        namespace.config = config_file_name
            
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
        required=False,
        default=exchanges[0])
    parser.add_argument("--config", 
        help="File that contains API secrets and configuration information required to connect to your exchange",
        metavar=("CONFIG_FILE"),
        action=ConfigArgumentAction,
        required=False)  
    parser.add_argument("--product", 
        help=f"Coin pairing to trade with.  Currently supported products: {products}",
        metavar=("PRODUCT"),
        action=ProductArgumentAction,
        required=False,
        default=products[0]) 
    return parser