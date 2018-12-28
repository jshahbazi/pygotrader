import signal
import curses
import os
import cbpro
import traceback
from pygotrader import arguments,config, order_book, tui

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
    
        argument_parser = arguments.create_parser()
        args = argument_parser.parse_args()
        
        my_config = config.MyConfig(exchange=args.exchange,product=args.product)
        
        my_order_book = order_book.OrderBook(product_id=my_config.product)
        my_order_book.start()
        
        mytui = tui.TerminalDisplay()
        curses.wrapper(mytui.display_loop)
        
    except CustomExit:
        my_order_book.close()
        
    except Exception as e:
        print(traceback.format_exc())