#!/usr/bin/env python3
"""
Script to list all of the ranges
"""
import argparse

from jackal import RangeSearch
from jackal.utils import print_json, print_line


def main():
    rs = RangeSearch()
    arg = argparse.ArgumentParser(parents=[rs.argparser], conflict_handler='resolve')
    arg.add_argument('-c', '--count', help="Only show the number of results", action="store_true")
    arguments = arg.parse_args()
    if arguments.count:
        print_line("Number of ranges: {}".format(rs.argument_count()))
    else:
        response = rs.get_ranges()
        for hit in response:
            print_json(hit.to_dict(include_meta=True))


if __name__ == '__main__':
    main()
