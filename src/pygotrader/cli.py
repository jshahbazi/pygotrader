from argparse import Action, ArgumentParser
import signal
import curses
import os
import cbpro
import traceback
from pygotrader import tui, order_book


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
        required=True)  
    parser.add_argument("--product", 
        help=f"Coin pairing to trade with.  Currently supported products: {products}",
        metavar=("PRODUCT"),
        action=ProductArgumentAction,
        required=True) 
    return parser
    
class CustomExit(Exception):
    #custom class to handle catching signals
    pass    
    
def signal_handler(signum, frame):
    print('Caught signal %d' % signum)
    raise CustomExit



class MyConfig(object):
    def __init__(self,exchange='coinbase',product='BTC-USD'):
        self.exchange = exchange
        self.product = product


def main():

    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)
    
    try:
    
        args = create_parser().parse_args()
        
        my_config = MyConfig(exchange=args.exchange,product=args.product)
        my_order_book = order_book.OrderBook(product_id=my_config.product)
        my_order_book.start()
        
        mytui = tui.TerminalDisplay()
        curses.wrapper(mytui.display_loop)
        
    except CustomExit:
        my_order_book.close()
    except Exception as e:
        print(traceback.format_exc())