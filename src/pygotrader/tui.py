import curses
import time
from pygotrader import cli

class DisplayData(object):
    """Object to hold data from both shared memory and other classes.  Used for 
    updating the UI
    """
    def __init__(self):
        self.asks = []
        self.bids = []
        self.highest_bid = 0.00
        self.last_match = 0.00  
        self.product = 'BTC-USD'
        self.my_balances = {'USD':0.00,self.product:0.00}
        self.message = ''
        self.my_crypto = ''

class TerminalDisplay(object):
    """The main TUI interface.  Objects are passed here from the main cli 
    function and updated either on their own or through shared memory (the 
    manager namespace).  This is built on the curses library.
    
    Methods of note:
    display_loop: Main display loop that sets up the window and then calls the
    draw method to actually build and draw the screen.  Watches for, and handles, 
    key presses by the user.
    
    draw: Builds the window using the draw_main_window method and then displays it
    
    calculate_data: Pulls data from other objects or the shared memory namespace
    and puts it into a DisplayData object for use by the draw() method. 
    
    keypress: Handles the user keypresses
    
    TODO: 
    - Removed fixed positioning and handle resizing properly
    - Add more user input (such as entering amounts)
    - Add the ability to create and edit trading algorithms on the fly
    """
    
    
    def __init__(self, ns, order_book, authenticated_client, order_handler, debug = False):
        self.ns = ns
        self.order_book = order_book
        self.authenticated_client = authenticated_client
        self.view_mode = False if authenticated_client else True
        self.order_handler = order_handler
        self.debug = debug
        self.user_input = ''
        self.menu_mode = 'normal'
    
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

        display_max_asks=5
        for x in range(0,display_max_asks):
            self.ns.ui_asks.insert(x,{'price':0.00,'depth':0.00})        
        display_max_bids=5
        for x in range(0,display_max_bids):
            self.ns.ui_bids.insert(x,{'price':0.00,'depth':0.00})        

        self.win = curses.newwin(self.height, self.width, 0, 0)

        curses.noecho()
        curses.halfdelay(5)

        user_input = ''
        while True:
            try:
                self.draw()
                user_keypress = self.win.getch()
                #getch() is set to non-blocking via curses.halfdelay, so -1 is value it has when nothing is entered
                if user_keypress == -1:
                    pass
                else:
                    # self.ns.message = str(user_keypress)
                    key = chr(user_keypress)
                    if self.menu_mode == 'normal':
                        self.keypress(key)
                    else:
                        if user_keypress in [10,'\n','\r']: #10 is line-feed
                            # self.ns.message = self.user_input
                            self.keypress(self.user_input)
                            self.user_input = ''
                        elif user_keypress in [127,curses.KEY_BACKSPACE]:
                            self.user_input = self.user_input[:-1]
                        else:
                            self.user_input += key
                time.sleep(0.1)
                self.stdscr.clear()
            except KeyboardInterrupt:
                self.exit()

        
    def calculate_data(self):
        data = DisplayData()
        data.product = self.order_book.products
        data.highest_bid = self.ns.highest_bid
        data.last_match = self.ns.last_match
        data.asks = self.ns.ui_asks
        data.bids = self.ns.ui_bids
        data.my_orders = self.ns.my_orders
        data.message = self.ns.message
        data.my_crypto = data.product.split('-')[0] #This is super hacky. TODO: Fix
        if self.authenticated_client:
            my_accounts = self.authenticated_client.get_accounts()
            for elem in my_accounts:
                if(elem['currency'] == 'USD'):
                    data.my_balances['USD'] = float(elem['balance'])
                if(elem['currency'] == data.my_crypto):
                    data.my_balances[data.product] = float(elem['balance'])
                
        return data
        
    def set_menu_mode(self):
        if self.view_mode:
            self.menu = f"Press key for action - (Q)uit: {self.user_input}"
        else:
            if self.menu_mode == 'normal':
                self.menu = f"Press key for action - (B)uy, (S)ell, (C)ancel, (Q)uit: {self.user_input}"
            elif self.menu_mode == 'buy-amount':
                self.menu = f"Type in amount and press <Enter>: {self.user_input}"
            elif self.menu_mode == 'sell-amount':
                self.menu = f"Type in amount and press <Enter>: {self.user_input}"
            elif self.menu_mode == 'cancel-order':
                self.menu = f"Type in order number and press <Enter> to cancel: {self.user_input}"        
        
    def draw(self):
        self.win.erase()
        #self.win = curses.newwin(self.height, self.width, 0, 0)
        data = self.calculate_data()
        self.set_menu_mode()
        curses.curs_set(0)
        self.draw_main_window(data)
        self.win.refresh()
        curses.curs_set(1)

      
    def draw_main_window(self, data):
        try:
            self.win.addstr(0,0,'Product\t\tBalances\t\t\t\t\t\t\t\t  Ask/Bid     Ask/Bid Depth', curses.A_BOLD)
            self.win.addstr(1,0,f"{data.product}")
            if not self.view_mode:
                self.win.addstr("\t\tUSD:  ")    
                self.win.addstr("{:>10.2f}".format(data.my_balances['USD']), curses.color_pair(1)) 
                self.win.addstr(2, 0, "\t\t{}: ".format('BTC'))
                self.win.addstr("{:>10.9f}".format(data.my_balances[data.product]), curses.color_pair(1))

            self.win.addstr(1, 60, "Highest Bid: {:.2f}".format(data.highest_bid))
            self.win.addstr(2, 60, "Last Match: {:.2f}".format(data.last_match))
    
            max_asks = len(data.asks)
            for idx,ask in enumerate(data.asks):
                self.win.addstr(1+idx,90,"{:.2f}\t{:.2f}".format(data.asks[(max_asks-1)-idx]['price'],data.asks[(max_asks-1)-idx]['depth']), curses.color_pair(3))
    
            # max_bids = len(data.bids)
            for idx,bid in enumerate(data.bids):
                self.win.addstr(6+idx, 90,"{:.2f}\t{:.2f}".format(bid['price'],bid['depth']), curses.color_pair(4))
        
            self.win.addstr(4, 0, 'Orders:', curses.A_BOLD)
            self.win.addstr(5, 0, 'ID  Product  Side  Type    Price    Remaining Size', curses.A_BOLD)
            
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
            
            self.win.addstr(self.height-3, 0, 'Message: {}'.format(data.message))
                  
            status_message=''
            if(status_message):
                self.win.addstr(self.height-2, 0, "{}".format(status_message))
            else:
                self.win.addstr(self.height-2, 0, "{}".format(''))      
            
            self.win.addstr(self.height-1, 0, self.menu)
        except curses.error:
            raise cli.CustomExit

    def keypress(self, input):
        if self.view_mode:
            if input == curses.KEY_EXIT or input == 'q':
                self.exit()
        elif not self.view_mode:
            if self.menu_mode == 'normal':
                if input == 'c':
                    self.menu_mode = 'cancel-order'
                    self.ns.message = 'Cancel has not been implemented yet...'
                    return
                if input == 'b':
                    self.menu_mode = 'buy-amount'
                    return
                if input == 's':
                    self.menu_mode = 'sell-amount'
                    return        
                if input == curses.KEY_EXIT or input == 'q':
                    self.exit()
            elif self.menu_mode == 'buy-amount':
                if input == '':
                    self.menu_mode = 'normal'
                    return
                amount = float(input)
                self.order_handler.create_buy_order(size=amount,price=0.00,product_id=self.order_book.products)
                self.menu_mode = 'normal'
            elif self.menu_mode == 'sell-amount':
                if input == '':
                    self.menu_mode = 'normal'
                    return
                amount = float(input)
                self.order_handler.create_sell_order(size=amount,price=0.00,product_id=self.order_book.products)                
                self.menu_mode = 'normal'
            elif self.menu_mode == 'cancel-order':
                if input == '':
                    self.menu_mode = 'normal'
                    return
                elif input.isdigit():
                    order_number = int(input)
                    self.menu_mode = 'normal'
                else:
                    self.ns.message = 'Bad input'
                    self.menu_mode = 'normal'
                
    def exit(self):
        self.win.erase()
        self.win = curses.newwin(self.height, self.width, 0, 0)            
        self.win.addstr("Quitting...")
        self.win.refresh() 
        curses.endwin()
        raise cli.CustomExit        
