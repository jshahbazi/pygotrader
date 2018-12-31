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

class ExchangeMessage(object):
    def __init__(self, msg):
        self.sequence = msg["sequence"] if 'sequence' in msg else ""
        self.time = dt.datetime.strptime(msg["timestamp"], '%Y-%m-%dT%H:%M:%S.%fZ') \
            if 'timestamp' in msg else dt.datetime.strptime(msg["time"], '%Y-%m-%dT%H:%M:%S.%fZ')
        self.type = msg["type"]
        self.product_id = msg["product_id"]
        self.order_id = msg["order_id"] if 'order_id' in msg else None
        self.price = float(msg["price"]) if 'price' in msg else None
        self.side = msg["side"] if 'side' in msg else ""
        self.remaining_size = msg["remaining_size"] if 'remaining_size' in msg else None
        self.size = msg["size"] if 'size' in msg else None

    def __str__(self):
        print_out = f"{self.sequence}"
        return print_out
        
        

class PygoOrderBook(OrderBook):
    def __init__(self, ns, product_id='BTC-USD', log_to=None):
        super().__init__(product_id=product_id)
        self.ns = ns

    def on_message(self, message):
        super().on_message(message)
        self.ns.highest_bid = self.get_bid()
        
    def match(self, order):
        super().match(order)
        message_object = ExchangeMessage(order)
        self.ns.exchange_order_matches.append(message_object)   

    def calculate_order_depth(self,max_asks=5,max_bids=5):
        for x in range(0,max_asks):
            price = self._asks.iloc[x]
            depth = sum(a['size'] for a in self._asks[price])
            self.ns.asks[x] = {'price':price,'depth':depth}

        i=0
        for bid in reversed(self._bids):
            if i == max_bids:
                break
            price = bid
            depth = sum(b['size'] for b in self._bids[bid])
            self.ns.bids[i] = {'price':price,'depth':depth}
            i=i+1

        
    def _listen(self):
        """
        Overriding the parent's parent (WebsocketClient) listen method
        in order to calculate the order depth and copy the data to the 
        shared namespace for the TUI to display
        """
        self.keepalive.start()
        start_time = time.time()
        while not self.shutdown_event.is_set():
            try:
                now = time.time()
                if((now - start_time) > 0.5):
                    self.calculate_order_depth()
                    start_time = now
                data = self.ws.recv()
                msg = json.loads(data)
            except ValueError as e:
                self.on_error(e)
            except Exception as e:
                self.on_error(e)
            else:
                self.on_message(msg)        