#!/usr/bin/env python3
import sys
from os import isatty
import json

is_pipe = not isatty(sys.stdin.fileno())

if is_pipe:
    if len(sys.argv) > 1:
        find = sys.argv[1]
        for line in sys.stdin:
            line = json.loads(line)
            print(line.get(find, ''))
    else:
        for line in sys.stdin:
            sys.stdout.write(line)
