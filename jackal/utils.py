"""
    Provides some utility functions to aid printing for usage with pipes.
"""
import datetime
import json
import sys


def datetime_handler(x):
    if isinstance(x, datetime.datetime):
        return x.isoformat()
    raise TypeError("Unknown type")


def print_line(text):
    """
        Print the given line to stdout
    """
    try:
        sys.stdout.write(text)
        if not text.endswith('\n'):
            sys.stdout.write('\n')
        sys.stdout.flush()
    except IOError:
        pass


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
