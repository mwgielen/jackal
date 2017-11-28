#!/usr/bin/env python3
import sys
from os import isatty
from jackal.utils import print_line
import json


def main():
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
