from cbpro.order_book import OrderBook
from sortedcontainers import SortedDict
from decimal import Decimal
import datetime, json, os, time, traceback
from threading import Thread
import multiprocessing
from scipy import stats
from importlib import reload
from pygotrader import algorithm

class AlgorithmHandler(object):
    """
    This class handles user-created algorithms used for trading.  It will reload
    the algorithm file (which is named algorithm.py by default) in real-time 
    (well, after a slight lag of 10 seconds by default) by checking on a change 
    in the modified time of the file. If there is an error, it will sleep for 30 seconds
    to allow the user to fix the error, and then it will attempt to reload it again.
    
    The algorithm file needs to have a function called trading_algorithm(), which 
    is called below by the main_loop() function.  The user is allowed to code 
    anything with any library, but they are only given the asks, bids, and matches 
    from the order book and websocket feed.
    """
    
    def __init__(self,ns, authenticated_client, order_handler, algorithm_file='./algorithm.py', debug = False):
        self.ns = ns
        self.authenticated_client = authenticated_client
        self.order_handler = order_handler
        self.debug = debug 
        self.shutdown_event = multiprocessing.Event()       
        self.event = multiprocessing.Event()
        self.algorithm_file = algorithm_file
        self.algorithm_reload_time = 10
        self.algorithm_run_rate = 0.1

    def start(self):
        self.process = multiprocessing.Process(target=self.main_loop, args=(self.ns,self.shutdown_event))
        self.process.start()

    def close(self):
        self.shutdown_event.set()
        self.process.join()

    def main_loop(self, ns, event):
        algo_last_modified = os.stat(self.algorithm_file).st_mtime
        now = datetime.datetime.utcnow()
        timer = now
        
        while not self.shutdown_event.is_set():
            now = datetime.datetime.utcnow()
            if ((now - timer) > datetime.timedelta(seconds=self.algorithm_reload_time)):
                timer = now
                algo_current_modified = os.stat(self.algorithm_file).st_mtime
                if algo_current_modified != algo_last_modified:
                    reload(algorithm)
                    algo_last_modified = algo_current_modified
                    reload_time = datetime.datetime.utcnow() - now
                    self.ns.message = f"Algorithm reloaded in {reload_time.total_seconds()} seconds"

            try:
                algorithm.trading_algorithm(ns=self.ns,order_handler=self.order_handler,matches=self.ns.exchange_order_matches)  #user made algorithm
                time.sleep(self.algorithm_run_rate)
            except Exception as e:
                self.ns.message = f"Error in {self.algorithm_file}.  Please see algorithm_error.txt for more details."
                with open("algorithm_error.txt","w") as f:
                    f.write(traceback.format_exc())
                time.sleep(30)
            
            time.sleep(0.1)
