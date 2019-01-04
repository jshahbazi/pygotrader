import json, os, signal, time, traceback
import curses
import cbpro
import multiprocessing
from pygotrader import arguments,config, order_handler, pygo_order_book, tui

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
    ns.message = ''
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
        
        if args.secrets:
            my_config.load_secrets(args.secrets)
            my_authenticated_client = my_config.get_coinbase_authenticated_client()
        else:
            my_authenticated_client = None
            ns.message = 'Running in view mode'

        my_order_book = pygo_order_book.PygoOrderBook(ns,product_id=my_config.product)
        my_order_book.start()
        
        my_order_handler = order_handler.OrderHandler(my_authenticated_client,ns)
        my_order_handler.start()

        mytui = tui.TerminalDisplay(ns, my_order_book, my_authenticated_client)
        curses.wrapper(mytui.display_loop)
    
        
    except CustomExit:
        my_order_book.close()
        my_order_handler.close()
        
    except Exception as e:
        print(traceback.format_exc())