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
        self.win.addstr(0,0,"Running...")
        self.win.refresh()        

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
