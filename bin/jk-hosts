#!/usr/bin/env python3
"""
Script to list all of the ranges
"""
import sys

from jackal import Core, Host
from jackal.utils import print_json, print_line


core = Core()

def main():
    response = core.get_hosts()
    if isinstance(response, int):
        print_line("Number of hosts: {}".format(response))
    else:
        for hit in response:
            print_json(hit.to_dict())


if __name__ == '__main__':
    main()
