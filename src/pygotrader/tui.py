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
        self.order_display_start = 0

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
        # curses.noecho()
        self.stdscr.keypad(1)  #needed for special characters such as KEY_UP
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
                time.sleep(self.refresh_time)
            except KeyboardInterrupt:
                self.exit()

######################################################
# Display Handling


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
            self.menu = f"Press key for action - (B)uy, (S)ell, (L)imit order, (C)ancel, (A)utomated trading, (Q)uit: {self.input_command}"
        elif self.mode == 'limit_order':
            self.menu = f"Press key for action (or ESC to return) - Create (B)uy limit order, (S)ell limit order: {self.input_command}"
        elif self.mode == 'buy_market' or self.mode == 'sell_market':
            self.menu = f"Type in amount and press <Enter>: {self.input_command}"
        elif self.mode == 'buy_amount' or self.mode == 'sell_amount':
            self.menu = f"Type in amount and press <Enter>: {self.input_command}"
        elif self.mode == 'buy_price' or self.mode == 'sell_price':
            self.menu = f"Type in price and press <Enter>: {self.input_command}"
        elif self.mode == 'cancel_order':
            self.menu = f"Type in order number and press <Enter> to cancel: {self.input_command}"         
        else:
            self.menu = f"Press key for action - (B)uy, (S)ell, (L)imit order, (C)ancel, (A)utomated trading, (Q)uit: {self.input_command}"
        
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
        # so we do a deep copy and turn it into a list to get an iterator from that
        # See https://bugs.python.org/issue6766
        temp_dict = {}
        copy.deepcopy(self.ns.my_orders, temp_dict)
        orders = list(temp_dict.values())[0] #ignore extra Manager dict data
        self.my_orders = [orders[order] for order in orders]
        ############
        self.message = self.ns.message
        self.my_crypto = self.product.split('-')[0] #This is super hacky. TODO: Fix
        if self.authenticated_client:
            my_accounts = self.authenticated_client.get_accounts()
            for elem in my_accounts:
                if(elem['currency'] == 'USD'):
                    self.my_balances['USD'] = float(elem['balance'])
                if(elem['currency'] == self.my_crypto):
                    self.my_balances[self.product] = float(elem['balance'])


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
                self.win.addstr(4, 0, 'Orders: [▲ and ▼ to scroll]', curses.A_BOLD)
                self.win.addstr(5, 0, 'ID  Product  Side  Type    Price    Remaining Size   Status', curses.A_BOLD)
            
            if self.height > 6:
                if self.my_orders:
                    order_set = self.my_orders[self.order_display_start:]
                    for idx,order in enumerate(order_set):
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
            


######################################################
# Input Handling
#
# Mode flowchart:
#
# normal -> buy_market -> normal
# normal -> sell_market -> normal
# normal -> limit_order -> buy_amount -> buy_price -> normal
# normal -> limit_order -> sell_amount -> sell_price -> normal
# normal -> cancel_order -> normal
# view (can't change mode)

        
    def input_handler(self):
        try:
            key_integer = self.win.getch()
        except curses.error:
            return
        

        if key_integer == -1:
            return
        else:
            key_char = (chr(key_integer)).lower() #chr() can't handle -1, so this needs to be after the -1 check
        
        #Curses sends this key when resizing the window
        if key_integer == curses.KEY_RESIZE:
            self.calculate_size()
            if self.debug:
                self.ns.message = f"{self.height},{self.width}"
            return

              
        if self.mode == 'normal' or self.mode == 'limit_order':
            if key_integer == 27:  #ESC key
                self.change_mode("normal")
                return
            #curses.KEY_UP and curses.KEY_DOWN don't work, so AND together values.
            elif key_integer == (27 and 91 and 65):    #Up arrow key
                if self.order_display_start > 0:
                    self.order_display_start -= 1
                return
            elif key_integer == (27 and 65 and 66):  #Down arrow key
                if len(self.my_orders) > self.order_display_start:
                    self.order_display_start += 1     
                return              
            else:
                self.menu_choice_handler(key_char)
        elif self.mode == 'view':
            if key_char != 'q':  #View mode shouldn't have any other option
                return
            else:
                self.menu_choice_handler(key_char)
        elif self.mode in ['buy_market','sell_market', \
                           'buy_amount','buy_price', \
                           'sell_amount','sell_price','cancel_order']:
            if key_integer == 27:  #ESC key
                self.change_mode("normal")
                return                               
            if key_integer in [10,'\n','\r']: #10 is line-feed
                self.input_actions(self.input_command)
                self.input_command = ''
            elif key_integer in [127,curses.KEY_BACKSPACE]:
                self.input_command = self.input_command[:-1]
            else:
                self.input_command += key_char

    def menu_choice_handler(self, input):
        if self.mode == 'normal':
            if input == 'b':
                self.change_mode('buy_market')
            elif input == 's':
                self.change_mode('sell_market')
            elif input == 'l':
                self.change_mode('limit_order')            
            elif input == 'c':
                self.change_mode('cancel_order')
            elif input == 'a':
                self.toggle_automated_trading()           
            elif input == 'q' or input == curses.KEY_EXIT:
                self.exit()
        elif self.mode == 'limit_order':
            if input == 'b':
                self.change_mode('buy_amount')
            elif input == 's':
                self.change_mode('sell_amount')
        elif self.mode == 'view':
            if input == 'q' or input == curses.KEY_EXIT:
                self.exit()

    def change_mode(self,change_to):
        if change_to == 'normal' or change_to == 'view':
            self.mode = change_to
            self.refresh_time = 0.03
        elif change_to in ['buy_amount','sell_amount', \
                           'buy_price','sell_price', \
                           'limit_order','cancel_order', \
                           'buy_market','sell_market']:
            self.mode = change_to
            self.refresh_time = 0.01
        else:
            self.ns.message = 'Unknown mode'



    def input_actions(self, input):
        if input == '':
            self.change_mode('normal')
            return

        try:        
            if self.mode == 'buy_market':
                    amount = float(input)
                    self.order_handler.create_buy_order(size=amount,price=0.00,product_id=self.order_book.products)
                    self.change_mode('normal')
            elif self.mode == 'sell_market':
                    amount = float(input)
                    self.order_handler.create_sell_order(size=amount,price=0.00,product_id=self.order_book.products)
                    self.change_mode('normal')
            elif self.mode == 'buy_amount':
                    self.temp_input_amount = float(input)
                    self.change_mode('buy_price')
            elif self.mode == 'buy_price':
                    price = float(input)
                    self.order_handler.create_buy_order(size=self.temp_input_amount,price=price,product_id=self.order_book.products,type='limit')
                    self.temp_input_amount = 0.00
                    self.change_mode('normal')
            elif self.mode == 'sell_amount':
                    self.temp_input_amount = float(input)
                    self.change_mode('sell_price')                    
            elif self.mode == 'sell_price':
                    price = float(input)
                    self.order_handler.create_sell_order(size=self.temp_input_amount,price=price,product_id=self.order_book.products,type='limit')
                    self.temp_input_amount = 0.00
                    self.change_mode('normal')
            elif self.mode == 'cancel_order':
                    order_number = int(input)
                    if order_number < (len(self.my_orders) - self.order_display_start) and order_number > 0:
                        order_id = self.my_orders[self.order_display_start + order_number - 1]['id']
                        self.order_handler.create_cancel_order(order_id)
                    else:
                        self.ns.message = 'Order number does not exist'
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