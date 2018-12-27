from argparse import Action, ArgumentParser
import signal
import curses
import os
from pygotrader import tui


exchange_choices = ['coinbase']

class ExchangeArgumentAction(Action):
    def __call__(self, parser, namespace, values, option_string=None):
        exchange = values
        if exchange.lower() not in exchange_choices:
            parser.error("Unknown exchange")
        namespace.exchange = exchange.lower()

class SecretsArgumentAction(Action):
    def __call__(self, parser, namespace, values, option_string=None):
        secrets_file_name = values
        if os.path.isfile(secrets_file_name):
            pass
        else:
            parser.error("Secrets file does not exist")

def create_parser():
    parser = ArgumentParser(description="")
    exchange_arg_help = f"Exchange to connect to.  Currently supported exchanges: {exchange_choices}"
    parser.add_argument("--exchange", 
        help=exchange_arg_help,
        metavar=("EXCHANGE"),
        action=ExchangeArgumentAction,
        required=True)
    parser.add_argument("--secrets", 
        help="File that contains API secrets required to connect to your exchange",
        metavar=("SECRETS_FILE"),
        action=SecretsArgumentAction,
        required=True)        
    return parser
    
class CustomExit(Exception):
    #custom class to handle catching signals
    pass    
    
def signal_handler(signum, frame):
    print('Caught signal %d' % signum)
    raise CustomExit

def main():
    
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)
    
    try:
    
        args = create_parser().parse_args()
        
        if args.exchange == 'coinbase':
            mytui = tui.TerminalDisplay()
            curses.wrapper(mytui.display_loop)
        else:
            pass
        
    except CustomExit:
        #TODO handle threads exiting here
        pass
    
    print(f"Exiting...")