import curses
import time
from pygotrader import cli

class DisplayData(object):
    def __init__(self):
        self.asks = []
        self.bids = []
        self.highest_bid = 0.00
        self.last_match = 0.00  

class TerminalDisplay(object):
    
    def __init__(self, ns, order_book, authenticated_client):
        self.ns = ns
        self.order_book = order_book
        self.authenticated_client = authenticated_client
    
    def display_loop(self, stdscr):
        self.stdscr = stdscr
        self.height,self.width = stdscr.getmaxyx()
        self.stdscr.clear()
        self.stdscr.refresh()
        
        curses.use_default_colors()
        curses.start_color()
        curses.init_pair(1, curses.COLOR_GREEN, curses.COLOR_BLACK)
        curses.init_pair(2, curses.COLOR_RED, curses.COLOR_BLACK)
        curses.init_pair(3, curses.COLOR_YELLOW, curses.COLOR_BLACK)
        curses.init_pair(4, curses.COLOR_CYAN, curses.COLOR_BLACK)

        self.win = curses.newwin(self.height, self.width, 0, 0)
        # self.stdscr.nodelay(0)
        # start_time = time.time()
        curses.halfdelay(5)
        while True:
            try:
                # now = time.time()
                # if((now - start_time) > 5.0):
                #     templist = self.ns.exchange_order_matches
                #     with open('debug.txt','a+') as f:
                #         f.write(f"Order Matches List - {len(templist)}\n")
                self.draw()
                user_entered_command = self.win.getch()
                self.keypress(user_entered_command)
                time.sleep(0.1)
                self.stdscr.clear()
            except KeyboardInterrupt:
                self.exit()

        
    def calculate_data(self):
        data = DisplayData()
        data.product = self.order_book.products
        data.highest_bid = self.ns.highest_bid
        data.last_match = self.ns.last_match
        data.asks = self.ns.asks
        data.bids = self.ns.bids
        data.my_orders = self.ns.my_orders
        data.my_balances = {'USD':0.00,data.product:0.00}
        
        my_accounts = self.authenticated_client.get_accounts()
        for elem in my_accounts:
            if(elem['currency'] == 'USD'):
                data.my_balances['USD'] = float(elem['balance'])
            if(elem['currency'] == data.product):
                data.my_balances[data.product] = float(elem['balance'])
                
        return data
        
    def draw(self):
        self.win.erase()
        self.win = curses.newwin(self.height, self.width, 0, 0)
        data = self.calculate_data()
        self.draw_main_window(data)
        self.win.refresh()

      
    def draw_main_window(self, data, debug=False):
        self.win.addstr(0,0,'Product\t\tBalances\t\t\t\t\t\t\t\t  Ask/Bid     Ask/Bid Depth', curses.A_BOLD)
        self.win.addstr(1,0,f"{data.product}")
        self.win.addstr("\t\tUSD:  ")    
        self.win.addstr("{:>10.2f}".format(data.my_balances['USD']), curses.color_pair(1)) 
        self.win.addstr(2, 0, "\t\t{}: ".format('BTC'))
        self.win.addstr("{:>10.9f}".format(data.my_balances[data.product]), curses.color_pair(1))
        
        if debug:
            self.win.addstr(3, 0, "Bought: {}".format('STUB'))
            self.win.addstr(4, 0, "Sold: {}".format('STUB'))
            self.win.addstr(5, 0, "buy_signal: {}".format('STUB'))
            self.win.addstr(6, 0, "sell_signal: {}".format('STUB'))
            self.win.addstr(3, 60, "Signal: {}".format('STUB'))
            
        self.win.addstr(1, 60, "Highest Bid: {:.2f}".format(data.highest_bid))
        self.win.addstr(2, 60, "Last Match: {:.2f}".format(data.last_match))

        max_asks = len(data.asks)
        for idx,ask in enumerate(data.asks):
            self.win.addstr(1+idx,90,"{:.2f}\t{:.2f}".format(data.asks[(max_asks-1)-idx]['price'],data.asks[(max_asks-1)-idx]['depth']), curses.color_pair(3))

        # max_bids = len(data.bids)
        for idx,bid in enumerate(data.bids):
            self.win.addstr(6+idx, 90,"{:.2f}\t{:.2f}".format(bid['price'],bid['depth']), curses.color_pair(4))
    
        self.win.addstr(8, 0, 'Orders:', curses.A_BOLD)
        self.win.addstr(9, 0, 'ID  Product  Side  Type    Price    Remaining Size', curses.A_BOLD)
        
        if data.my_orders:
            for idx,order in enumerate(data.my_orders):
                if(idx <= 4):
                    if('product_id' in order):
                        self.win.addstr(10+idx, 0, "[{}] {}  ".format(idx+1,order['product_id']))
                        if(order['side'] == 'buy'):
                            self.win.addstr("{}".format(order['side']), curses.color_pair(1))
                        else:
                            self.win.addstr("{}".format(order['side']), curses.color_pair(2))
                        self.win.addstr("  {}   {:.2f}    {:.9f}".format(order['type'],float(order['price']),float(order['size'])))
        
        self.win.addstr(self.height-3, 0, 'Message: {}'.format('STUB'))
              
        status_message=''
        if(status_message):
            self.win.addstr(self.height-2, 0, "{}".format(status_message))
        else:
            self.win.addstr(self.height-2, 0, "{}".format(''))      
            
        self.win.addstr(self.height-1, 0, "Press key for action - (B)uy, (S)ell, (C)ancel, c(L)ear, (F)lip, (Q)uit:")  
        

    def keypress(self, char):
        if char == curses.KEY_EXIT or char == ord('q'):
            self.exit()
            
        if char == ord('b'):
            self.draw()
            return

    def exit(self):
        self.win.erase()
        self.win = curses.newwin(self.height, self.width, 0, 0)            
        self.win.addstr("Quitting...")
        self.win.refresh() 
        curses.endwin()
        raise cli.CustomExit        
