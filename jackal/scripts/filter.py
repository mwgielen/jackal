#!/usr/bin/env python3
import sys
from os import isatty
from jackal.utils import print_line
import json


def filter():
    is_pipe = not isatty(sys.stdin.fileno())

    if is_pipe:
        if len(sys.argv) > 1:
            find = sys.argv[1]
            for line in sys.stdin:
                line = json.loads(line)
                result = line.get(find, '')
                if isinstance(result, list):
                    result = '[' + ', '.join([str(x) for x in result]) + ']'
                print_line(result)
        else:
            for line in sys.stdin:
                print_line(line)


def format():
    is_pipe = not isatty(sys.stdin.fileno())
    style = "{address:15} {port:7} {protocol:5} {service:15} {state:10} {banner}"
    if len(sys.argv) > 1:
        style = sys.argv[1]
    if is_pipe:
        for line in sys.stdin:
            line = json.loads(line)
            print_line(style.format(**line))