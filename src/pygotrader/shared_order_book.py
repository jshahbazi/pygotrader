from cbpro.order_book import OrderBook
from sortedcontainers import SortedDict
from decimal import Decimal
import pickle
import time
import datetime as dt

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
        
        

class SharedOrderBook(OrderBook):
    def __init__(self, ns, product_id='BTC-USD', log_to=None):
        super(SharedOrderBook, self).__init__(product_id=product_id)
        self._ns = ns
        
    def on_message(self, message):
        if self._log_to:
            pickle.dump(message, self._log_to)

        sequence = message.get('sequence', -1)
        if self._sequence == -1:
            self.reset_book()
            return
        if sequence <= self._sequence:
            # ignore older messages (e.g. before order book initialization from getProductOrderBook)
            return
        elif sequence > self._sequence + 1:
            self.on_sequence_gap(self._sequence, sequence)
            return

        msg_type = message['type']
        if msg_type == 'open':
            self.add(message)
        elif msg_type == 'done' and 'price' in message:
            self.remove(message)
        elif msg_type == 'match':
            self.match(message)
            self._current_ticker = message
        elif msg_type == 'change':
            self.change(message)

        self._sequence = sequence
        self._ns.highest_bid = self.get_bid()
        
    def match(self, order):
        size = Decimal(order['size'])
        price = Decimal(order['price'])
        
        message_object = ExchangeMessage(order)
        self._ns.exchange_order_matches.append(message_object)
        
        with open('debug.txt','a+') as f:
            f.write(f"Order Matches List - order_book - {message_object}\n")        

        if order['side'] == 'buy':
            bids = self.get_bids(price)
            if not bids:
                return
            assert bids[0]['id'] == order['maker_order_id']
            if bids[0]['size'] == size:
                self.set_bids(price, bids[1:])
            else:
                bids[0]['size'] -= size
                self.set_bids(price, bids)
        else:
            asks = self.get_asks(price)
            if not asks:
                return
            assert asks[0]['id'] == order['maker_order_id']
            if asks[0]['size'] == size:
                self.set_asks(price, asks[1:])
            else:
                asks[0]['size'] -= size
                self.set_asks(price, asks)
                
        self._ns.last_match = price