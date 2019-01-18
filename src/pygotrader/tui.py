import curses, math, time, copy
from pygotrader import cli, order_handler, algorithm_handler

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
    
    input_handler: gathers the input as the user is typing
    
    input_actions: calls on proper functions with the user input after the user hits 
    enter
    
    Note: don't use stdscr.clear() as it will cause flicker.  Use stdscr.erase()
    
    TODO: 
    - Handle horizontal resizing properly
    """
    
    def __init__(self,ns, order_book, authenticated_client, order_handler, algorithm_file, debug = False):
        self.ns = ns
        self.order_book = order_book
        self.authenticated_client = authenticated_client
        self.order_handler = order_handler
        self.algorithm_handler = None
        self.algorithm_file = algorithm_file
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
        self.refresh_time = 0.03
        self.askbid_spread_size = 5
        self.stdscr = None
        self.height = 0
        self.width = 0
        self.temp_input_amount = 0.00

    def start(self, stdscr):
        if self.authenticated_client:
            self.change_mode('normal')
        self.initialize_curses(stdscr)
        self.win = curses.newwin(self.height, self.width, 0, 0)
        self.main_loop()
        
    def exit(self):
        if self.algorithm_handler != None:
            self.algorithm_handler.close()
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
        curses.init_pair(1, curses.COLOR_GREEN, -1)
        curses.init_pair(2, curses.COLOR_RED, -1)
        curses.init_pair(3, curses.COLOR_YELLOW, -1)
        curses.init_pair(4, curses.COLOR_CYAN, -1)
        curses.noecho()
        curses.halfdelay(5)        

    def check_order_book(self):
        if(not self.order_book):
            self.win.erase()
            self.win.addstr(self.height-3, 0, 'Message: OrderBook has failed to connect...')
            time.sleep(3)
            self.exit()     

    def main_loop(self):
        while True:
            try:
                self.check_order_book()
                self.draw()
                self.input_handler()
                # self.ns.message = self.mode
                time.sleep(self.refresh_time)
            except KeyboardInterrupt:
                self.exit()

    def draw(self):
        self.win.erase()
        self.assemble_menu_information()
        self.display_menu()
        curses.curs_set(0)
        self.draw_main_window()
        self.win.refresh()
        curses.curs_set(1)
        
    def display_menu(self):
        if self.mode == 'view':
            self.menu = f"Press key for action - (Q)uit: {self.input_command}"
        elif self.mode == 'normal':
            self.menu = f"Press key for action - (B)uy, (S)ell, (C)ancel, (A)utomated trading, (Q)uit: {self.input_command}"
        elif self.mode == 'buy_amount':
            self.menu = f"Type in amount and press <Enter>: {self.input_command}"
        elif self.mode == 'buy_price':
            self.menu = f"Type in price and press <Enter>: {self.input_command}"
        elif self.mode == 'sell_amount':
            self.menu = f"Type in amount and press <Enter>: {self.input_command}"
        elif self.mode == 'cancel_order':
            self.menu = f"Type in order number and press <Enter> to cancel: {self.input_command}"         
        else:
            self.menu = f"Press key for action - (B)uy, (S)ell, (C)ancel, (A)utomated trading, (Q)uit: {self.input_command}"
        
    def calculate_size(self):
        self.height,self.width = self.stdscr.getmaxyx()
        self.askbid_spread_size = min(10,math.floor((0.8 * self.height) / 2.0))

    def assemble_menu_information(self):
        self.product = self.order_book.products
        self.highest_bid = self.ns.highest_bid
        self.last_match = self.ns.last_match
        self.asks = self.ns.ui_asks
        self.bids = self.ns.ui_bids
        
        # This is hacky because Manager dictionaries are buggy
        # and you can't get an iterator directly from them,
        # so we do a deep copy to get an iterator from that
        # See https://bugs.python.org/issue6766
        temp_dict = {}
        copy.deepcopy(self.ns.my_orders, temp_dict)
        orders = list(temp_dict.values())[0] #ignore extra Manager dict data
        self.my_orders = [orders[order] for order in orders]
        ############
        # self.open_orders = [self.my_orders[order] for order in self.my_orders if self.my_orders[order]['status'] == 'open']
        # self.closed_orders = [self.my_orders[order] for order in self.my_orders if self.my_orders[order]['status'] == 'closed']
        # self.ordered_orders = open_orders + closed_orders
        # for item in open_orders:
        #     with open('debug.txt','a+') as f:
        #         f.write(str(item))
        #         f.write('\n')
        
        self.message = self.ns.message
        self.my_crypto = self.product.split('-')[0] #This is super hacky. TODO: Fix
        if self.authenticated_client:
            my_accounts = self.authenticated_client.get_accounts()
            for elem in my_accounts:
                if(elem['currency'] == 'USD'):
                    self.my_balances['USD'] = float(elem['balance'])
                if(elem['currency'] == self.my_crypto):
                    self.my_balances[self.product] = float(elem['balance'])

    def input_handler(self):
        key_integer = self.win.getch()
        if key_integer == -1:
            return
        
        #Curses sends this key when resizing the window
        if key_integer == curses.KEY_RESIZE:
            self.calculate_size()
            if debug:
                self.ns.message = f"{self.height},{self.width}"

        key_char = (chr(key_integer)).lower() #can't handle -1, needs to be here      
        if self.mode == 'normal':
            self.menu_choice_handler(key_char)
        elif self.mode == 'view':
            if key_char != 'q':
                return
            self.menu_choice_handler(key_char)
        elif self.mode in ['buy_amount','buy_price','sell_amount','cancel_order']:
            if key_integer in [10,'\n','\r']: #10 is line-feed
                self.input_actions(self.input_command)
                self.input_command = ''
            elif key_integer in [127,curses.KEY_BACKSPACE]:
                self.input_command = self.input_command[:-1]
            else:
                self.input_command += key_char

    def menu_choice_handler(self, input):
        if input == 'b':
            self.change_mode('buy_amount')
        elif input == 'c':
            self.change_mode('cancel_order')
        elif input == 's':
            self.change_mode('sell_amount')
        elif input == 'a':
            self.toggle_automated_trading()           
        elif input == 'q' or input == curses.KEY_EXIT:
            self.exit()

    def change_mode(self,change_to):
        if change_to == 'normal':
            self.mode = 'normal'
            self.refresh_time = 0.03
        elif change_to == 'view':
            self.mode = 'view'
            self.refresh_time = 0.03           
        elif change_to == 'buy_amount':
            self.mode = 'buy_amount'
            self.refresh_time = 0.01
        elif change_to == 'buy_price':
            self.mode = 'buy_price'
            self.refresh_time = 0.01
        elif change_to == 'sell_amount':
            self.mode = 'sell_amount'
            self.refresh_time = 0.01
        elif change_to == 'cancel_order':
            self.mode = 'cancel_order'
            self.refresh_time = 0.01
        else:
            self.ns.message = 'Unknown mode'



    def input_actions(self, input):
        if input == '':
            self.change_mode('normal')
            return

        try:        
            if self.mode == 'buy_amount':
                    self.temp_input_amount = float(input)
                    self.change_mode('buy_price')
            elif self.mode == 'buy_price':
                    price = float(input)
                    self.order_handler.create_buy_order(size=self.temp_input_amount,price=price,product_id=self.order_book.products)
                    self.temp_input_amount = 0.00
                    self.change_mode('normal')
            elif self.mode == 'sell_amount':
                    self.temp_input_amount = float(input)
                    self.order_handler.create_sell_order(size=self.temp_input_amount,price=0.00,product_id=self.order_book.products)                
                    self.change_mode('normal')
            elif self.mode == 'cancel_order':
                    order_number = int(input)
                    order_id = self.my_orders[order_number - 1]['id']
                    self.order_handler.create_cancel_order(order_id)
                    self.change_mode('normal')
        except ValueError:
            self.ns.message = 'Bad input'
            self.change_mode('normal')

    def toggle_automated_trading(self):
        if self.algorithm_handler == None:
            self.algorithm_handler = algorithm_handler.AlgorithmHandler(self.ns, self.authenticated_client, self.order_handler, algorithm_file=self.algorithm_file)
            self.algorithm_handler.start()
        else:
            self.algorithm_handler.close()
            self.algorithm_handler = None
            
    def draw_main_window(self):
        try:
            if self.width >= 85:
                width_multiplier = 0.5
            else:
                width_multiplier = 0.4
            live_data_start_col = int(width_multiplier*self.width)
            askbid_start_col = live_data_start_col + 25
            
            if self.height > 3:
                self.win.addstr(0,0,'Product\t\tBalances', curses.A_BOLD)
                self.win.addstr(0,askbid_start_col,'Ask/Bid    Ask/Bid Depth', curses.A_BOLD)
                self.win.addstr(1,0,f"{self.product}")
                if self.mode != 'view':
                    self.win.addstr("\t\tUSD:  ")    
                    self.win.addstr("{:>10.2f}".format(self.my_balances['USD']), curses.color_pair(1)) 
                    self.win.addstr(2, 0, "\t\t{}: ".format('BTC'))
                    self.win.addstr("{:>10.9f}".format(self.my_balances[self.product]), curses.color_pair(1))
        
                self.win.addstr(1, live_data_start_col, "Last Match: {:.2f}".format(self.last_match))
                self.win.addstr(2, live_data_start_col, "Highest Bid: {:.2f}".format(self.highest_bid))
                
            if self.height > (self.askbid_spread_size * 2 + 1):
                max_asks = self.askbid_spread_size
                for idx,ask in enumerate(self.asks):
                    if idx == max_asks:
                        break                    
                    self.win.addstr(1+idx,askbid_start_col,"{:.2f}      {:.2f}".format(self.asks[(max_asks-1)-idx]['price'],self.asks[(max_asks-1)-idx]['depth']), curses.color_pair(3))
        
                max_bids = self.askbid_spread_size
                for idx,bid in enumerate(self.bids):
                    if idx == max_bids:
                        break
                    index = 1 + self.askbid_spread_size + idx
                    self.win.addstr(index,askbid_start_col,"{:.2f}      {:.2f}".format(bid['price'],bid['depth']), curses.color_pair(4))
            
            if self.height > 5:
                self.win.addstr(4, 0, 'Orders:', curses.A_BOLD)
                self.win.addstr(5, 0, 'ID  Product  Side  Type    Price    Remaining Size   Status', curses.A_BOLD)
            
            if self.height > 6:
                if self.my_orders:
                    for idx,order in enumerate(self.my_orders):
                        if(self.height > 6 + idx + 1):
                            self.win.addstr(6+idx, 0, "[{}] {}  ".format(idx+1,order['product_id']))
                            if(order['side'] == 'buy'):
                                self.win.addstr("{}".format(order['side']), curses.color_pair(1))
                            elif(order['side'] == 'sell'):
                                self.win.addstr("{}".format(order['side']), curses.color_pair(2))
                            self.win.addstr(6+idx, 19,"{}".format(order['type']))
                            self.win.addstr(6+idx, 27, "{:.2f}".format(float(order['price'])))
                            self.win.addstr(6+idx, 36, "{:.9f}".format(float(order['size'])))
                            self.win.addstr(6+idx, 53, "{}".format(order['status']), curses.color_pair(1))
                else:
                    self.win.addstr(6, 0, "No orders", curses.color_pair(4))
                    
                self.win.addstr(self.height-3, 0, 'Message: {}'.format(self.message))
                if self.algorithm_handler != None:
                    self.win.addstr(self.height-2, 0, 'Automated trading enabled', curses.A_STANDOUT)
            self.win.addstr(self.height-1, 0, self.menu)
        except curses.error:
            raise cli.CustomExit