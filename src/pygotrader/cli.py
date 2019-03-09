import json, os, signal, time, traceback,shutil
import curses
import cbpro
import multiprocessing
from pygotrader import arguments,config, order_handler, pygo_order_book, tui, algorithm_handler
from pkg_resources import Requirement, resource_filename

#from profiling.tracing import TracingProfiler

class CustomExit(Exception):
    """Custom class to exit program"""
    pass    
    
def signal_handler(signum, frame):
    """Wrapper to handle break signals from the user"""
    # print('Caught signal %d' % signum)
    raise CustomExit

def pause():
    """Lazy wrapper for a cli pause
    ¯\_(ツ)_/¯
    """
    program_pause = input("Press the <ENTER> key to continue...")
    
def create_namespace(my_manager):
    """Initialize and construct the shared namespace
    
    As mentioned elsewhere, lists and dicts need to be created from the Manager
    class otherwise updates to them won't propagate.  Remember, this is more of a 
    helper class, not one to do serious work with.  Operations can be expensive.
    And custom classes can't be used.
    
    Order format for placement into the buy and sell order queue lists:
    {'order':'buy','type':'market','product':'BTC','size':0.1,'price':1.00}
    
    Order format for placement into the cancel order queue lists:
    {'order':'cancel','order_id':1111111}    
    """
    ns = my_manager.Namespace()
    ns.exchange_order_matches = my_manager.list()
    ns.buy_order_queue = my_manager.list()
    ns.sell_order_queue = my_manager.list()
    ns.cancel_order_queue = my_manager.list()
    ns.my_orders = my_manager.dict()
    ns.last_match = 0.00
    ns.highest_bid = 0.00
    ns.lowest_ask = 0.00
    ns.message = ''
    ns.ui_asks = my_manager.list()
    ns.ui_bids = my_manager.list()
    for x in range(0,10):
        ns.ui_asks.insert(x,{'price':0.00,'depth':0.00})  
        ns.ui_bids.insert(x,{'price':0.00,'depth':0.00})       
    return ns



def main():
    """Entry point for the program
    
    Create the objects that are going to run the various parts of the programs.
    Threads/processes are not directly created here.  That's been left for the
    individual classes.
    
    Variables of note:
    ns - a multiprocessing.Manager.namespace that is for sharing data between 
    threads and processes
    
    Objects of note:
    MyConfig - loads and stores arguments passed in as well as user config 
    information stored in outside files
    PygoOrderBook - the order book that uses a websocket to pull data from the
    exchange.  Does not actually place orders.
    AuthenticatedClient - this has the secrets for the user loaded from the 
    external config files.  This is the class that actually places orders that 
    organized and called by the OrderHandler class.  
    OrderHandler - separate-running process to place and cancel orders through
    functions in the AuthenticatedClient class. 
    
    TODO:
     - Add the ability to create external config class via an install function 
     or some kind of config function within the tui or cli
     - Add the ability to export data in real-time to database
    """
    
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)
    
    """
    The multiprocessing Manager namespace seems like the easiest/least-risky
    way of sharing data across processes.  However, it requires use of dicts
    and lists from the Manager class.  
    Important notes:
    1) Operations on this data structure can be expensive.  Reads are cheap, and 
        simple writes aren't too bad, but for example, deleting a
        Manager.list() data structure and creating a new one can take a few
        hundredths of a second.  Its better to do work on a local data structure
        and then copy it over to the shared namespace.
    2) Namespaces don't work with deep data structures, i.e. a custom class
        You can do a dict inside a list, or vice-versa, but that's about it
    """
    my_manager = multiprocessing.Manager()
    ns = create_namespace(my_manager)
    view_mode = True
    
    try:
        
        # profiler = TracingProfiler()
        # profiler.start()
        
        
    
        argument_parser = arguments.create_parser()
        args = argument_parser.parse_args()
        if args.config:
            view_mode = False


        my_config = config.MyConfig(exchange=args.exchange,product=args.product)

        if not view_mode:
            my_config.load_config(args.config)
            my_authenticated_client = my_config.get_coinbase_authenticated_client()
            
            if not os.path.exists(args.algorithm_file):
                filename = resource_filename(Requirement.parse("pygotrader"),"pygotrader/algorithm.py")
                print(f"Copying sample algorithm file to ./algorithm.py...")
                shutil.copyfile(filename,"./algorithm.py")
                time.sleep(2)       
                
            my_order_handler = order_handler.OrderHandler(my_authenticated_client,ns)
            my_order_handler.start()                
        else:
            my_authenticated_client = None
            my_order_handler = None
            ns.message = 'Running in view mode'

        my_order_book = pygo_order_book.PygoOrderBook(ns,product_id=my_config.product, url=my_config.websocket_url)
        my_order_book.start()
        

        while not my_order_book.has_started:
            time.sleep(0.1)

        mytui = tui.Menu(ns, my_order_book, my_authenticated_client, my_order_handler, algorithm_file=args.algorithm_file)
        curses.wrapper(mytui.start)

        
    except CustomExit:
        my_order_book.close()
        if not view_mode:
            my_order_handler.close()
        # profiler.stop()
        # profiler.run_viewer()
        
    except Exception as e:
        print(traceback.format_exc())
        
        
        
if __name__ == "__main__":
    main()