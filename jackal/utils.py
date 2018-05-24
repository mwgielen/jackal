"""
    Provides some utility functions to aid printing for usage with pipes.
"""
import datetime
import json
import sys
import string
import curses
from math import ceil
import signal
import psutil
import socket
import ipaddress

def datetime_handler(x):
    if isinstance(x, datetime.datetime):
        return x.isoformat()
    raise TypeError("Unknown type")


def print_line(text):
    """
        Print the given line to stdout
    """
    try:
        signal.signal(signal.SIGPIPE, signal.SIG_DFL)
    except ValueError:
        pass

    try:
        sys.stdout.write(text)
        if not text.endswith('\n'):
            sys.stdout.write('\n')
        sys.stdout.flush()
    except IOError:
        sys.exit(0)


def print_json(data):
    """
        Print the given data to stdout.
    """
    print_line(json.dumps(data, default=datetime_handler))


def print_notification(string):
    """
        Prints a grey [*] before the message
    """
    print_line('\033[94m[*]\033[0m {}'.format(string))


def print_success(string):
    """
        Prints a green [+] before the message
    """
    print_line('\033[92m[+]\033[0m {}'.format(string))


def print_error(string):
    """
        Prints a red [!] before the message
    """
    print_line('\033[91m[!]\033[0m {}'.format(string))


# from https://gist.github.com/navarroj/7689682
class PartialFormatter(string.Formatter):
    def __init__(self, missing='~'):
        self.missing = missing

    def get_field(self, field_name, args, kwargs):
        # Handle missing fields
        try:
            return super().get_field(field_name, args, kwargs)
        except (KeyError, AttributeError):
            return None, field_name

    def format_field(self, value, spec):
        if value is None:
            return self.missing
        else:
            return super().format_field(value, spec)

def draw_interface(objects, callback, callback_text):
    """
        Draws a ncurses interface. Based on the given object list, every object should have a "string" key, this is whats displayed on the screen, callback is called with the selected object.
        Rest of the code is modified from:
        https://stackoverflow.com/a/30834868
    """
    screen = curses.initscr()
    height, width = screen.getmaxyx()
    curses.noecho()
    curses.cbreak()
    curses.start_color()
    screen.keypad( 1 )
    curses.init_pair(1,curses.COLOR_BLACK, curses.COLOR_CYAN)
    highlightText = curses.color_pair( 1 )
    normalText = curses.A_NORMAL
    screen.border( 0 )
    curses.curs_set( 0 )
    max_row = height - 15 # max number of rows
    box = curses.newwin( max_row + 2, int(width - 2), 1, 1 )
    box.box()
    fmt = PartialFormatter()

    row_num = len( objects )

    pages = int( ceil( row_num / max_row ) )
    position = 1
    page = 1
    for i in range( 1, max_row + 1 ):
        if row_num == 0:
            box.addstr( 1, 1, "There aren't strings", highlightText )
        else:
            if (i == position):
                box.addstr( i, 2, str( i ) + " - " + objects[ i - 1 ]['string'], highlightText )
            else:
                box.addstr( i, 2, str( i ) + " - " + objects[ i - 1 ]['string'], normalText )
            if i == row_num:
                break

    screen.refresh()
    box.refresh()

    x = screen.getch()
    while x != 27:
        if x == curses.KEY_DOWN:
            if page == 1:
                if position < i:
                    position = position + 1
                else:
                    if pages > 1:
                        page = page + 1
                        position = 1 + ( max_row * ( page - 1 ) )
            elif page == pages:
                if position < row_num:
                    position = position + 1
            else:
                if position < max_row + ( max_row * ( page - 1 ) ):
                    position = position + 1
                else:
                    page = page + 1
                    position = 1 + ( max_row * ( page - 1 ) )
        if x == curses.KEY_UP:
            if page == 1:
                if position > 1:
                    position = position - 1
            else:
                if position > ( 1 + ( max_row * ( page - 1 ) ) ):
                    position = position - 1
                else:
                    page = page - 1
                    position = max_row + ( max_row * ( page - 1 ) )

        screen.erase()
        if x == ord( "\n" ) and row_num != 0:
            screen.erase()
            screen.border( 0 )
            service = objects[position -1]
            text = fmt.format(callback_text, **service)
            screen.addstr( max_row + 4, 3, text)
            text  = callback(service)
            count = 0
            for line in text:
                screen.addstr( max_row + 5 + count, 3, line)
                count += 1

        box.erase()
        screen.border( 0 )
        box.border( 0 )

        for i in range( 1 + ( max_row * ( page - 1 ) ), max_row + 1 + ( max_row * ( page - 1 ) ) ):
            if row_num == 0:
                box.addstr( 1, 1, "There aren't strings",  highlightText )
            else:
                if ( i + ( max_row * ( page - 1 ) ) == position + ( max_row * ( page - 1 ) ) ):
                    box.addstr( i - ( max_row * ( page - 1 ) ), 2, str( i ) + " - " + objects[ i - 1 ]['string'], highlightText )
                else:
                    box.addstr( i - ( max_row * ( page - 1 ) ), 2, str( i ) + " - " + objects[ i - 1 ]['string'], normalText )
                if i == row_num:
                    break

        screen.refresh()
        box.refresh()
        x = screen.getch()

    curses.endwin()
    exit()

def get_own_ip():
    """
        Gets the IP from the inet interfaces.
    """
    own_ip = None
    interfaces = psutil.net_if_addrs()
    for _, details in interfaces.items():
        for detail in details:
            if detail.family == socket.AF_INET:
                ip_address = ipaddress.ip_address(detail.address)
                if not (ip_address.is_link_local or ip_address.is_loopback):
                    own_ip = str(ip_address)
                    break
    return own_ip

