from cbpro.order_book import OrderBook
from decimal import Decimal
import time
from itertools import islice
from threading import Thread
import json, os
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
    cancel orders, and get lists of existing orders, and waits for a shutdown event.  
    The child threads each wait for specific events before doing their work.
    
    place_order: Places orders via the authenticated_client. This method is used by various
    buy, sell, cancel child threads to place an order after it is pulled off their queue.
    
    create_buy_order: create_sell_order: Methods to create orders to put onto the order queue, that 
    are then pulled off by the child threads, which use place_order() to actually place the order.
    By default they are market orders, but when specified they can be limit orders.
    
    load_my_orders: Gets all the user's orders from the authenticated_client
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
                        self.ns.message = f"Buy order {order_id}: {order['status'].upper()}"
                        self.load_my_orders()
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
                        self.ns.message = f"Sell order {order_id}: {order['status'].upper()}"
                        self.load_my_orders()
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
                        self.ns.message = extended_result
                        self.load_my_orders()
                    else:
                        self.ns.message = f"Cancel failed: {extended_result}"
                except (ValueError,IndexError):
                    self.ns.message = "No cancel order found in the queue..."
                    pass
                self.cancel.clear()
                
        def _order_checker():
            while not self.shutdown_event.is_set():
                self.load_my_orders()
                time.sleep(10)

        self.order_checker_thread = Thread(target=_order_checker)
        self.order_checker_thread.start()
        self.buy_thread = Thread(target=_buy_loop)
        self.buy_thread.start()
        self.sell_thread = Thread(target=_sell_loop)
        self.sell_thread.start()
        self.cancel_thread = Thread(target=_cancel_loop)
        self.cancel_thread.start()
        
        self.shutdown_event.wait()
        
    def load_my_orders(self):
        my_orders = self.authenticated_client.get_orders()
        temp_dict ={}
        for order in my_orders:
            temp_dict[order['id']] = {'id':order['id'],
                                            'product_id':order['product_id'],
                                            'side':order['side'],
                                            'type':order['type'],
                                            'price':order['price'],
                                            'size':order['size'],
                                            'status':order['status']}
        self.ns.my_orders = temp_dict
            
    # def track_my_orders(self):
    #     # temp_dict = {}
    #     # copy.deepcopy(self.ns.my_orders, temp_dict)
    #     # orders = list(temp_dict.values())[0] #ignore extra Manager dict data
    #     # my_orders = [orders[order] for order in orders]
    #     my_orders = self.authenticated_client.get_orders()
    #     # print(my_orders)
    #     for order in my_orders:
    #         result = self.get_order(order,10)
    #         self.ns.message = result['status'] if result else "Nope"
        

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
            
    def cancel_order(self,order_id):
        canceled_order = self.authenticated_client.cancel_order(order_id)
        if order_id in canceled_order:
            return True, "Order Canceled."
        else:
            return False, f"Unable to cancel order: {canceled_order}."
            
    # def get_order(self, order, order_timeout):
    #     order_id = order['id']
    #     self.ns.message = order_id
    #     # time.sleep(2)
    #     # start = time.time()
    #     # now = time.time()
    #     # while now < start + order_timeout: 
    #         # try:
    #     my_order = self.authenticated_client.get_order(order_id)
    #     return my_order
    #         # except requests.exceptions.HTTPError:
    #             # time.sleep(1)
    #             # continue
                
    #     # raise ValueError("(OrderHandler.get_order) Unknown error: Order ID not being returned.")