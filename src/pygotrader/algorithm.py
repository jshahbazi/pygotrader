"""
User-made algorithm

User can create buy and sell orders using the order_handler class and following methods:

order_handler.create_buy_order(size,price,product_id,type='market')
order_handler.create_sell_order(size,price,product_id,type='limit')

TODO: 
- More user-friendly way of interacting with message window and shared namespace data
"""


from scipy import stats
from pygotrader import order_handler
import datetime


def trading_algorithm(ns, order_handler, asks=None, bids=None, matches=None):
    def display_message(text):
        ns.message = text
        
    
    rolling_window = 10

    length = len(matches)
    now = datetime.datetime.utcnow()
    i=0
    while i <= (length -1): #TODO speed this while loop up.  Currently averaging around 0.004s
        start = matches[i].time
        if start < (now - datetime.timedelta(seconds=rolling_window)):
             del matches[i]
             i=-1
             length = len(matches)
        else:
            break
        i+=1
    current_matches = matches    
    
    
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
        