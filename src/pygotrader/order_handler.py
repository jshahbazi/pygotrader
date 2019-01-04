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
    def __init__(self, authenticated_client, multiprocessing_namespace,debug=False):
        self.authenticated_client = authenticated_client
        self.ns = multiprocessing_namespace
        self.shutdown_event = multiprocessing.Event()
        self.debug = debug
    
    def main_loop(self):
        while not self.shutdown_event.is_set():
            time.sleep(1)
            
    def start(self):
        self.process = multiprocessing.Process(target=self.main_loop)
        self.process.start()
        
    def close(self):
        self.shutdown_event.set()
        self.process.join()        
    
    # def buy(self,size,price,side,product_id):
    #     while True:
    #         my_order = self.authenticated_client.place_order(type='limit',post_only=True,size=size, price=price, side=side, product_id=product_id)
    #         if('id' in my_order):
    #             order_id = my_order['id']
    #             return order_id, my_order
    #         else:
    #             if self.debug:
    #                 with open('debug.txt','a+') as f:
    #                     f.write(f"place_order: {my_order} - side: {side} size: {size} price: {price}\n")                
    #             time.sleep(1)