#!/usr/bin/env python3
"""
Script to list all of the ranges
"""
import argparse

from jackal import HostSearch
from jackal.utils import print_json, print_line


def main():
    hs = HostSearch()
    arg = argparse.ArgumentParser(parents=[hs.argparser], conflict_handler='resolve')
    arg.add_argument('-c', '--count', help="Only show the number of results", action="store_true")
    arguments = arg.parse_args()

    if arguments.count:
        print_line("Number of hosts: {}".format(hs.argument_count()))
    else:
        response = hs.get_hosts()
        for hit in response:
            print_json(hit.to_dict(include_meta=True))


if __name__ == '__main__':
    main()
