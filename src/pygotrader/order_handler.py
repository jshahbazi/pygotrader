from cbpro.order_book import OrderBook
from sortedcontainers import SortedDict
from decimal import Decimal
import pickle
import time
import datetime as dt
from itertools import islice
from threading import Thread
import json
import multiprocessing

class OrderHandler(object):
    """Handles making orders to an exchange and makes sure they're placed or
    canceled.
    
    
    """
    def __init__(self, authenticated_client, multiprocessing_namespace,debug=False):
        self.authenticated_client = authenticated_client
        self.ns = multiprocessing_namespace
        self.shutdown_event = multiprocessing.Event()
        self.debug = debug
        self.buy = multiprocessing.Event()
        self.sell = multiprocessing.Event()
        self.cancel = multiprocessing.Event()
        self.order_timeout = 5.0
    
    def main_loop(self):
        def _buy_loop():
            while not self.shutdown_event.is_set():
                self.buy.wait()                
                self.ns.message = "Buy!"
                self.buy.clear()

        def _sell_loop():
            while not self.shutdown_event.is_set():
                self.sell.wait()                
                self.ns.message = "Sell!"
                self.sell.clear()

        def _cancel_loop():
            while not self.shutdown_event.is_set():
                self.cancel.wait()                
                self.ns.message = "Cancel!"
                self.cancel.clear()
                
        self.buy_thread = Thread(target=_buy_loop)
        self.buy_thread.start()
        self.sell_thread = Thread(target=_sell_loop)
        self.sell_thread.start()
        self.cancel_thread = Thread(target=_cancel_loop)
        self.cancel_thread.start()
        
        self.shutdown_event.wait()
        

    def start(self):
        self.process = multiprocessing.Process(target=self.main_loop)
        self.process.start()
        
    def close(self):
        self.shutdown_event.set()
        self.process.join()        
        
    def buy_order(self,size,price,product_id):
        result = self.place_order(size=size,price=price,side='buy',product_id=product_id)
        return result
    
    def sell_order(self,size,price,product_id):
        result = self.place_order(size=size,price=price,side='sell',product_id=product_id)
        return result
        
    def place_order(self,size,price,side,product_id):
        start_time = time.time()
        while True:
            now = time.time()
            if((now - start_time) > self.order_timeout):
                return False
                
            # my_order = self.authenticated_client.place_order(type='limit',post_only=True,size=size, price=price, side=side, product_id=product_id)
            my_order = self.authenticated_client.place_order(product_id=product_id,side=side,order_type='market',size=size,)
            
            if('id' in my_order):
                order_id = my_order['id']
                return [order_id, my_order]
            else:
                if self.debug:
                    with open('debug.txt','a+') as f:
                        f.write(f"place_order: {my_order} - side: {side} size: {size} price: {price}\n")                
                time.sleep(1)
                
    def cancel(self,order_id):
        try:
            canceled_order = self.authenticated_client.cancel_order(order_id)
            if(canceled_order == order_id):
                return True, "Order Cancelled"
            else:
                return False, canceled_order
        except Exception as e:
            if self.debug:
                with open('debug.txt','a+') as f:
                    f.write(f"Cancel Order Error - Order: {order_id}\nError: {traceback.format_exc()}\n")
            return False         
            
    def get_order(self, order_timeout):
        for i in range(0,10):
            try:
                my_order = self.authenticated_client.get_order(order_id)
                return my_order
            except requests.exceptions.HTTPError:
                time.sleep(1)
                continue
                
        raise ValueError("(OrderHandler.get_order) Unknown error: Order ID not being returned.")        