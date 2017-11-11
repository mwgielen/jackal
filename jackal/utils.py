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
    sys.stdout.write(text)
    if not text.endswith('\n'):
        sys.stdout.write('\n')


def print_json(data):
    """
        Print the given data to stdout.
    """
    sys.stdout.write(json.dumps(data, default=datetime_handler))
    sys.stdout.write('\n')
