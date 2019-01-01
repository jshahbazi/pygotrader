import json, os, signal, traceback
import curses
import cbpro
import multiprocessing
from pygotrader import arguments,config, pygo_order_book, tui

class CustomExit(Exception):
    #custom class to handle catching signals
    pass    
    
def signal_handler(signum, frame):
    print('Caught signal %d' % signum)
    raise CustomExit

def pause():
    program_pause = input("Press the <ENTER> key to continue...")
    
def create_namespace(my_manager,max_asks=5,max_bids=5):
    ns = my_manager.Namespace()
    ns.exchange_order_matches = my_manager.list()
    ns.my_orders = my_manager.dict()
    ns.last_match = 0.00
    ns.highest_bid = 0.00
    ns.lowest_ask = 0.00
    ns.asks = my_manager.list()
    for x in range(0,max_asks):
        ns.asks.insert(x,{'price':0.00,'depth':0.00})
    ns.bids = my_manager.list()
    for x in range(0,max_bids):
        ns.bids.insert(x,{'price':0.00,'depth':0.00})
    return ns



def main():

    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)
    
    my_manager = multiprocessing.Manager()
    ns = create_namespace(my_manager)
    
    try:
    
        argument_parser = arguments.create_parser()
        args = argument_parser.parse_args()
        
        my_config = config.MyConfig(exchange=args.exchange,product=args.product)
        my_config.load_secrets(args.secrets)
        authenticated_client = my_config.get_coinbase_authenticated_client()
        
        my_orders = authenticated_client.get_orders()
        my_accounts = authenticated_client.get_accounts()

        my_order_book = pygo_order_book.PygoOrderBook(ns,product_id=my_config.product)
        my_order_book.start()
        
        mytui = tui.TerminalDisplay(ns, my_order_book)
        curses.wrapper(mytui.display_loop)
        
    except CustomExit:
        my_order_book.close()
        
    except Exception as e:
        print(traceback.format_exc())