import curses, math, time
from pygotrader import cli

class Menu(object):
    """The main TUI interface.  Objects are passed here from the main cli 
    function and updated either on their own or through shared memory (the 
    manager namespace).  This is built on the python curses library.
    
    The menu goes through several modes depending on the current state.  normal
    and view modes only accept single character inputs for menu choices.  The
    other modes accept strings, such as amounts and prices.  Window update speed 
    is increased when the user is expected to type in more than a single character.
    
    Methods of note:
    main_loop: Main display loop that sets up the window and then calls the
    draw method to actually build and draw the screen.  Watches for, and handles, 
    key presses by the user.
    
    draw: Builds the window using the draw_main_window method and then displays it
    
    assemble_menu_information: Pulls data from other objects or the shared memory namespace
    for use by the draw_main_window() method. 
    
    get_input: gathers the input as the user is typing
    
    handle_input: calls on proper functions with the user input after the user hits 
    enter
    
    Note: don't use stdscr.clear() as it will cause flicker.  Use stdscr.erase()
    
    TODO: 
    - Handle horizontal resizing properly
    - Add the ability to create and edit trading algorithms on the fly
    """
    
    def __init__(self,ns, order_book, authenticated_client, order_handler, debug = False):
        self.ns = ns
        self.order_book = order_book
        self.authenticated_client = authenticated_client
        self.order_handler = order_handler
        self.debug = debug        
        self.mode = 'view'
        self.input_menu = ''
        self.asks = []
        self.bids = []
        self.highest_bid = 0.00
        self.last_match = 0.00  
        self.product = 'BTC-USD'
        self.my_balances = {'USD':0.00,self.product:0.00}
        self.message = ''
        self.my_crypto = ''
        self.my_orders = []
        self.win = None
        self.input_command = ''
        self.refresh_time = 0.1
        self.askbid_spread_size = 5
        self.stdscr = None
        self.height = 0
        self.width = 0

    def start(self, stdscr):
        if self.authenticated_client:
            self.change_mode('normal')
        self.initialize_curses(stdscr)
        self.win = curses.newwin(self.height, self.width, 0, 0)
        self.main_loop()
        
    def exit(self):
        self.win.erase()
        self.win.refresh()  
        curses.endwin()
        raise cli.CustomExit         
        
    def initialize_curses(self, stdscr):
        self.stdscr = stdscr
        self.calculate_size()
        self.stdscr.erase()
        self.stdscr.refresh()
        curses.use_default_colors()
        curses.start_color()
        curses.init_pair(1, curses.COLOR_GREEN, curses.COLOR_BLACK)
        curses.init_pair(2, curses.COLOR_RED, curses.COLOR_BLACK)
        curses.init_pair(3, curses.COLOR_YELLOW, curses.COLOR_BLACK)
        curses.init_pair(4, curses.COLOR_CYAN, curses.COLOR_BLACK)
        curses.noecho()
        curses.halfdelay(5)        

    def main_loop(self):
        while True:
            try:
                self.draw()
                self.get_input()
                time.sleep(self.refresh_time)
            except KeyboardInterrupt:
                self.exit()

    def draw(self):
        self.win.erase()
        self.assemble_menu_information()
        self.format_menu()
        curses.curs_set(0)
        self.draw_main_window()
        self.win.refresh()
        curses.curs_set(1)
        
    def calculate_size(self):
        self.height,self.width = self.stdscr.getmaxyx()
        self.askbid_spread_size = min(10,math.floor((0.8 * self.height) / 2.0))

    def assemble_menu_information(self):
        self.product = self.order_book.products
        self.highest_bid = self.ns.highest_bid
        self.last_match = self.ns.last_match
        self.asks = self.ns.ui_asks
        self.bids = self.ns.ui_bids
        self.my_orders = self.ns.my_orders
        self.message = self.ns.message
        self.my_crypto = self.product.split('-')[0] #This is super hacky. TODO: Fix
        if self.authenticated_client:
            my_accounts = self.authenticated_client.get_accounts()
            for elem in my_accounts:
                if(elem['currency'] == 'USD'):
                    self.my_balances['USD'] = float(elem['balance'])
                if(elem['currency'] == self.my_crypto):
                    self.my_balances[self.product] = float(elem['balance'])

    def format_menu(self):
        if self.mode == 'view':
            self.menu = f"Press key for action - (Q)uit: {self.input_command}"
        elif self.mode == 'normal':
            self.menu = f"Press key for action - (B)uy, (S)ell, (C)ancel, (Q)uit: {self.input_command}"
        elif self.mode == 'buy_amount':
            self.menu = f"Type in amount and press <Enter>: {self.input_command}"
        elif self.mode == 'sell_amount':
            self.menu = f"Type in amount and press <Enter>: {self.input_command}"
        elif self.mode == 'cancel_order':
            self.menu = f"Type in order number and press <Enter> to cancel: {self.input_command}" 
                
    def get_input(self):
        keypress = self.win.getch()
        if keypress == -1:
            return
        
        if keypress == curses.KEY_RESIZE:
            self.calculate_size()

        key = chr(keypress)        
        if self.mode in ['normal','view']:
            self.menu_choice(key)
        elif self.mode in ['buy_amount','sell_amount','cancel_order']:
            if keypress in [10,'\n','\r']: #10 is line-feed
                self.handle_input(self.input_command)
                self.input_command = ''
            elif keypress in [127,curses.KEY_BACKSPACE]:
                self.input_command = self.input_command[:-1]
            else:
                self.input_command += key

    def change_mode(self,mode):
        if mode == 'normal':
            self.mode = 'normal'
            self.refresh_time = 0.1
        elif mode == 'view':
            self.mode = 'view'
            self.refresh_time = 0.1            
        elif mode == 'buy_amount':
            self.mode = 'buy_amount'
            self.refresh_time = 0.05
        elif mode == 'sell_amount':
            self.mode = 'sell_amount'
            self.refresh_time = 0.05
        elif mode == 'cancel_order':
            self.mode = 'cancel_order'
            self.refresh_time = 0.05

    def menu_choice(self, input):
        if input == 'b':
            self.change_mode('buy_amount')
        elif input == 'c':
            self.change_mode('cancel_order')
            self.ns.message = 'Cancel has not been implemented yet...'
        elif input == 's':
            self.change_mode('sell_amount')
        elif input == 'q' or input == curses.KEY_EXIT:
            self.exit()


    def handle_input(self, input):
        if input == '':
            self.change_mode('normal')
            return

        try:        
            if self.mode == 'buy_amount':
                    amount = float(input)
                    self.order_handler.create_buy_order(size=amount,price=0.00,product_id=self.order_book.products)
            elif self.mode == 'sell_amount':
                    amount = float(input)
                    self.order_handler.create_sell_order(size=amount,price=0.00,product_id=self.order_book.products)                
            elif self.mode == 'cancel_order':
                    order_number = int(input)
        except ValueError:
            self.ns.message = 'Bad input'
        self.change_mode('normal')
                
                
    def draw_main_window(self):
        try:
            if self.height > 3:
                self.win.addstr(0,0,'Product\t\tBalances\t\t\t\t\t\t\t\t  Ask/Bid     Ask/Bid Depth', curses.A_BOLD)
                self.win.addstr(1,0,f"{self.product}")
                if self.mode != 'view':
                    self.win.addstr("\t\tUSD:  ")    
                    self.win.addstr("{:>10.2f}".format(self.my_balances['USD']), curses.color_pair(1)) 
                    self.win.addstr(2, 0, "\t\t{}: ".format('BTC'))
                    self.win.addstr("{:>10.9f}".format(self.my_balances[self.product]), curses.color_pair(1))
    
                self.win.addstr(1, 60, "Highest Bid: {:.2f}".format(self.highest_bid))
                self.win.addstr(2, 60, "Last Match: {:.2f}".format(self.last_match))

            if self.height > (self.askbid_spread_size * 2 + 1):
                max_asks = self.askbid_spread_size
                for idx,ask in enumerate(self.asks):
                    if idx == max_asks:
                        break                    
                    self.win.addstr(1+idx,90,"{:.2f}\t{:.2f}".format(self.asks[(max_asks-1)-idx]['price'],self.asks[(max_asks-1)-idx]['depth']), curses.color_pair(3))
        
                max_bids = self.askbid_spread_size
                for idx,bid in enumerate(self.bids):
                    if idx == max_bids:
                        break
                    index = 1 + self.askbid_spread_size + idx
                    self.win.addstr(index, 90,"{:.2f}\t{:.2f}".format(bid['price'],bid['depth']), curses.color_pair(4))
            
                if self.my_orders:
                    for idx,order in enumerate(self.my_orders):
                        if(idx <= 4):
                            if('product_id' in order):
                                self.win.addstr(10+idx, 0, "[{}] {}  ".format(idx+1,order['product_id']))
                                if(order['side'] == 'buy'):
                                    self.win.addstr("{}".format(order['side']), curses.color_pair(1))
                                else:
                                    self.win.addstr("{}".format(order['side']), curses.color_pair(2))
                                self.win.addstr("  {}   {:.2f}    {:.9f}".format(order['type'],float(order['price']),float(order['size'])))

            if self.height > 5:
                self.win.addstr(4, 0, 'Orders:', curses.A_BOLD)
                self.win.addstr(5, 0, 'ID  Product  Side  Type    Price    Remaining Size', curses.A_BOLD)
            
            if self.height > 6:
                self.win.addstr(self.height-3, 0, 'Message: {}'.format(self.message))

            self.win.addstr(self.height-1, 0, self.menu)
        except curses.error:
            raise cli.CustomExit