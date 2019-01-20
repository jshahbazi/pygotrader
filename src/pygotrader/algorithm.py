"""
User-made algorithm

User can create buy, sell, and cancel orders using the order_handler class and following methods:

order_handler.create_buy_order(size,price,product_id,type='market')
order_handler.create_sell_order(size,price,product_id,type='limit')
order_handler.create_cancel_order(order_id)

Order ID's can be obtained from the current user order list contained in ns.my_orders, which is a
dictionary that has the following structure:

ns.my_orders[ORDER_ID] = {'id':ORDER_ID,
                          'product_id':PRODUCT_ID,   #BTC-USD or whatever
                          'side':ORDER_SIDE,         #buy or sell
                          'type':ORDER_TYPE,         #market or limit
                          'price':ORDER_PRICE,
                          'size':ORDER_SIZE,
                          'status':ORDER_STATUS}     #[open, pending, active]
                          
For more info on the Coinbase Pro API: https://docs.pro.coinbase.com/  


The shared namespace, as denoted by the "ns" object passed into the function, contains the 
following variables and data structures:

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
    
"""


from scipy import stats
from pygotrader import order_handler
import datetime


def trading_algorithm(ns, order_handler, asks=None, bids=None, matches=None):
    def display_message(text):
        ns.message = text
        
    #This is a rolling window to allow the algorithm to only view the matches that happened
    #in the last 10 seconds
    rolling_window = 10
    length = len(matches)
    now = datetime.datetime.utcnow()
    i=0
    while i <= (length -1): #TODO speed this while loop up.  Currently averaging around 0.004s
        start = matches[i].time
        if start < (now - datetime.timedelta(seconds=rolling_window)):
             del matches[i]
             i=-1
             length = len(matches)  #New matches may be added while this loop is executing
        else:
            break
        i+=1
    current_matches = matches    
    
    #Run a linear regression on the matches' price and then based on the slope, buy or sell
    #Note that this doesn't turn a profit.  This will lose you money.  But its an example
    #of what you can do.
    list_size = len(current_matches)
    if (list_size <= 2):
        return 0
    x = list(range(0,list_size))
    y = [current_matches[i].price for i in x]
    slope, intercept, r_value, p_value, std_err = stats.linregress(x,y)

    if(slope > 0.1): 
        display_message(f"Slope: {slope} - Buy")
        # order_handler.create_buy_order(size=0.01,price=0.00,product_id='BTC-USD',type='market')
    elif(slope < -0.1):
        display_message(f"Slope: {slope} - Sell")
        # order_handler.create_sell_order(size=0.01,price=0.00,product_id='BTC-USD',type='market')
        