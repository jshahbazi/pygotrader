from cbpro.order_book import OrderBook
from sortedcontainers import SortedDict
from decimal import Decimal
import time
import datetime as dt
from threading import Thread
import json
import multiprocessing

class ExchangeMessage(object):
    """Turns an exchange message into an object so that it can be used 
    for trading algorithms
    """
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
        print_out = f"ExchangeMessageObject: {self.sequence} {self.side} {self.product_id} {self.size} @ {self.price}"
        return print_out
        
        

class PygoOrderBook(OrderBook):
    """Extension of the OrderBook class and grandparent WebsocketClient class
    
    Most of the functionality of the OrderBook class is fine, but some things 
    need to be replaced or added in the following areas:
    - Checking orders from the exchange for user's
    - Handling matches (completed buys/sells)
    - Calculating order depth per price
    - Updating the _listen method since that's the core of the receive loop
    - Adding functionality to handle orders placed by user
    
    TODO:
    - Replace OrderBook's use of websocket-client with websockets
    - Figure out a better way to share ExchangeMessage objects between processes/threads
    """
    def __init__(self, ns, product_id='BTC-USD', log_to=None, url='wss://ws-feed.pro.coinbase.com'):
        super().__init__(product_id=product_id)
        self.url = url
        self.ns = ns
        self.has_started = False

    def on_message(self, message):
        super().on_message(message)
        self.handle_my_order(message) 
        self.ns.highest_bid = self.get_bid()
        
    def match(self, order):
        super().match(order)
        message_object = ExchangeMessage(order)
        self.ns.exchange_order_matches.append(message_object)
        self.ns.last_match = message_object.price

    def calculate_order_depth(self,max_asks=10,max_bids=10):
        for x in range(0,max_asks):
            price = self._asks.iloc[x]
            depth = sum(a['size'] for a in self._asks[price])
            self.ns.ui_asks[x] = {'price':price,'depth':depth}

        i=0
        for bid in reversed(self._bids):
            if i == max_bids:
                break
            price = bid
            depth = sum(b['size'] for b in self._bids[bid])
            self.ns.ui_bids[i] = {'price':price,'depth':depth}
            i=i+1

        
    def _listen(self):
        """
        Overriding the grandparent's (WebsocketClient) listen method
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

    def on_open(self):
        super()
        self.has_started = True

    def add_my_order(self, order_id, order):
        self.ns.my_orders.update({order_id:order})

    def remove_my_order(self, order_id):
        try:
            del self.ns.my_orders[order_id]
        except ValueError:
            pass
        
    def lookup_my_order(self, order_id):
        if order_id in self.ns.my_orders:
            return True
        else:
            return False
            
    def update_my_order(self, order_id, order):
        self.ns.my_orders.update({order_id:order})

    def get_my_order(self, order_id):
        return self.ns.my_orders[order_id]
        
    def convert_message_to_order(self, message):
        order = {
            'order_id': message.get('order_id') or message.get('id') or message.get('maker_order_id') ,
            'status': message.get('status'),
            'side': message['side'],
            'price': message['price'],
            'size': message.get('size') or message.get('remaining_size')
        }
        return order
        

    def get_my_current_orders(self, authenticated_client):
        all_my_orders = (authenticated_client.get_orders(product_id=self.product_id,status=["open"]))[0]
        for idx,order in enumerate(all_my_orders):
            order_id = order['id'] 
            current_order = {}
            current_order['order_id'] = order['id']
            current_order['status'] = 'open'
            current_order['price'] = order['price']
            current_order['side'] = order['side']
            current_order['size'] = order['size']
            self.add_my_order(order['id'],current_order) 
                    
                    
    def handle_my_order(self, message):
        if('order_id' in message):
            order_id =  message["order_id"]
        elif('maker_order_id' in message):
            order_id =  message["maker_order_id"]
        else:
            return        
                
        
        if(self.lookup_my_order(order_id)):
            myorder = self.convert_message_to_order(message)
            msg_type = message['type']

            if msg_type == 'open':
                self.add_my_order(order_id, myorder)
                
            elif msg_type == 'done' and message['reason'] == 'filled':
                myorder['status'] = 'filled'
                self.update_my_order(order_id, myorder)
                
            elif msg_type == 'done' and message['reason'] == 'canceled':
                myorder['status'] = 'canceled'
                self.update_my_order(order_id, myorder)
                
            elif msg_type == 'match':
                #subtract size
                temp_order = self.get_my_order(order_id)
                current_size = Decimal(temp_order['size'])
                updated_size = Decimal(myorder['size'])
                new_size = current_size - updated_size
                if(new_size == Decimal(0.00)):
                    temp_order['status'] = 'done'
                else:
                    temp_order['status'] = 'open'
                temp_order['remaining_size'] = str(new_size)
                self.update_my_order(order_id, temp_order)
                
            else: # msg_type == 'change':
                # with open('orderupdater_output.txt','a+') as f:
                #     f.write(json.dumps(message, indent=1) + "\n")
                pass