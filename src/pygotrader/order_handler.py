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

def debug_write(text, debug_file='debug.txt'):
    """Helper function to keep code clean"""
    with open(debug_file,'a+') as f:
        f.write(f"{text}\n")    

class OrderHandler(object):
    """Handles making orders to an exchange and makes sure they're placed or
    canceled.
    
    Important methods:
    main_loop: A separate process that launches child threads to handle buy, sell,
    and cancel orders, and waits for a shutdown event.  The child threads each wait
    for specific events before doing their work.
    
    place_order: Places orders via the authenticated_client.  
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
                try:
                    buy_order = self.ns.buy_order_queue.pop()
                    result, order_id, order = self.place_order(size=buy_order['size'],
                                                               price=buy_order['price'],
                                                               side=buy_order['order'],
                                                               product_id=buy_order['product'],
                                                               type=buy_order['type'])
                    if result:
                        self.ns.message = f"Buy order placed: {order_id}"
                    else:
                        self.ns.message = f"Buy order failed"
                except (ValueError,IndexError):
                    self.ns.message = "No buy order found in the queue..."
                    pass
                self.buy.clear()

        def _sell_loop():
            while not self.shutdown_event.is_set():
                self.sell.wait()                
                try:
                    sell_order = self.ns.sell_order_queue.pop()
                    result, order_id, order = self.place_order(size=sell_order['size'],
                                                               price=sell_order['price'],
                                                               side=sell_order['order'],
                                                               product_id=sell_order['product'],
                                                               type=sell_order['type'])                    
                    if result:
                        self.ns.message = f"Sell order placed: {order_id}"
                    else:
                        self.ns.message = f"Sell order failed"
                except (ValueError,IndexError):
                    self.ns.message = "No sell order found in the queue..."
                    pass
                self.sell.clear()

        def _cancel_loop():
            while not self.shutdown_event.is_set():
                self.cancel.wait()                
                try:
                    cancel = self.ns.cancel_order_queue.pop()
                    self.ns.message = f"Cancelling order {cancel['order_id']}"
                    result, extended_result = self.cancel_order(cancel['order_id'])
                    if result:
                        self.ns.message = ''
                    else:
                        self.ns.message = f"Cancel failed: {extended_result}"
                except (ValueError,IndexError):
                    self.ns.message = "No cancel order found in the queue..."
                    pass
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
        
    def create_buy_order(self,size,price,product_id,type='market'):
        """Place an order on the queue for the _buy_loop thread in the main loop to consume"""
        if type == 'market':
            self.ns.buy_order_queue.append({'order':'buy','type':'market','product':product_id,'size':size,'price':price})
        elif type == 'limit':
            self.ns.buy_order_queue.append({'order':'buy','type':'limit','product':product_id,'size':size,'price':price})
        else:
            self.ns.message = "Error in buy order type"
            return
        self.buy.set()

    def create_sell_order(self,size,price,product_id,type='market'):
        """Place an order on the queue for the _sell_loop thread in the main loop to consume"""
        if type == 'market':
            self.ns.sell_order_queue.append({'order':'sell','type':'market','product':product_id,'size':size,'price':price})
        elif type == 'limit':
            self.ns.sell_order_queue.append({'order':'sell','type':'limit','product':product_id,'size':size,'price':price})
        else:
            self.ns.message = "Error in sell order type"
            return
        self.sell.set()
                
    def create_cancel_order(self,order_id):
        """Place an order on the queue for the _cancel_loop thread in the main loop to consume"""
        self.ns.cancel_order_queue.append({'order':'cancel','order_id':order_id})
        self.cancel.set()       

    def place_order(self,size,price,side,product_id,type='market'):
        """This method actually places the order via the authenticated_client
        
        Will timeout if the order doesn't happen
        """
        start_time = time.time()
        while True:
            now = time.time()
            if((now - start_time) > self.order_timeout):
                return False
                
            if type == 'market':                
                my_order = self.authenticated_client.place_order(product_id=product_id,side=side,order_type=type,size=size)
            elif type == 'limit':
                my_order = self.authenticated_client.place_order(product_id=product_id,side=side,order_type=type,size=size,post_only=True,price=price)
            else:
                self.ns.message = f"Order type unknown: {type}"
                return False
            
            if('id' in my_order):
                order_id = my_order['id']
                return True, order_id, my_order
            else:
                if self.debug:
                    debug_write("place_order: {my_order} - side: {side} size: {size} price: {price} type: {type}")
                time.sleep(1)
            
    def get_order(self, order_timeout):
        for i in range(0,10):
            try:
                my_order = self.authenticated_client.get_order(order_id)
                return my_order
            except requests.exceptions.HTTPError:
                time.sleep(1)
                continue
                
        raise ValueError("(OrderHandler.get_order) Unknown error: Order ID not being returned.")