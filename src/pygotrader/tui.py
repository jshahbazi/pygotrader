import curses
import time
from pygotrader import cli


class TerminalDisplay(object):
    
    def __init__(self):
        pass
    
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
        self.stdscr.nodelay(0)
        
        self.draw()
        while True:
            try:
                user_entered_command = self.win.getch()
                self.keypress(user_entered_command)
            except KeyboardInterrupt:
                self.exit()

    def draw(self):
        self.win.erase()
        self.win = curses.newwin(self.height, self.width, 0, 0)
        self.draw_main_window()
        self.win.refresh()
        
        
    def draw_main_window(self):
        # self.win.addstr(0,0,"Running...")
        self.win.addstr(0,0,'Product\t\tBalances\t\t\t\t\t\t\t\t  Ask/Bid     Ask/Bid Depth', curses.A_BOLD)
        self.win.addstr(1,0,"BTC-USD")
        self.win.addstr("\t\tUSD:  ")    
        self.win.addstr("{:>10.2f}".format(0.00), curses.color_pair(1)) 
        self.win.addstr(2, 0, "\t\t{}: ".format('BTC'))
        self.win.addstr("{:>10.9f}".format(0.00), curses.color_pair(1))
        
        self.win.addstr(3, 0, "Bought: {}".format('Yes'))
        self.win.addstr(4, 0, "Sold: {}".format('No'))
        self.win.addstr(5, 0, "buy_signal: {}".format('Yes'))
        self.win.addstr(6, 0, "sell_signal: {}".format('No'))

        self.win.addstr(3, 60, "Signal: {}".format('Buy'))
        self.win.addstr(4, 60, "Profit: {:.2f}".format(1.00))
        
        # self.win.addstr(1,90,"{:.2f}\t{:.2f}".format(data['asks'][4]['price'],data['asks'][4]['depth']), curses.color_pair(3))
        # self.win.addstr(2,90,"{:.2f}\t{:.2f}".format(data['asks'][3]['price'],data['asks'][3]['depth']), curses.color_pair(3))
        # self.win.addstr(3,90,"{:.2f}\t{:.2f}".format(data['asks'][2]['price'],data['asks'][2]['depth']), curses.color_pair(3))
        # self.win.addstr(4,90,"{:.2f}\t{:.2f}".format(data['asks'][1]['price'],data['asks'][1]['depth']), curses.color_pair(3))
        # self.win.addstr(5,90,"{:.2f}\t{:.2f}".format(data['asks'][0]['price'],data['asks'][0]['depth']), curses.color_pair(3))
        
        # for idx,bid in enumerate(data['bids']):
        #     self.win.addstr(6+idx, 90,"{:.2f}\t{:.2f}".format(bid['price'],bid['depth']), curses.color_pair(4))
    
        self.win.addstr(8, 0, 'Orders:', curses.A_BOLD)
        self.win.addstr(9, 0, 'ID  Product  Side  Type    Price    Remaining Size', curses.A_BOLD)
        # for idx,order in enumerate(my_orders):
        #     if(idx <= 4):
        #         if('product_id' in order):
        #             self.win.addstr(10+idx, 0, "[{}] {}  ".format(idx+1,order['product_id']))
        #             if(order['side'] == 'buy'):
        #                 self.win.addstr("{}".format(order['side']), curses.color_pair(1))
        #             else:
        #                 self.win.addstr("{}".format(order['side']), curses.color_pair(2))
        #             self.win.addstr("  {}   {:.2f}    {:.9f}".format(order['type'],float(order['price']),float(order['size'])))
        
        self.win.addstr(self.height-3, 0, 'Message: {}'.format('Running...'))
              
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
