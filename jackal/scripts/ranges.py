#!/usr/bin/env python3
"""
Script to list all of the ranges
"""
from jackal import RangeSearch
from jackal.utils import print_json, print_line


def main():
    r = RangeSearch()
    arguments = r.core_parser.parse_args()
    if arguments.count:
        print_line("Number of ranges: {}".format(r.argument_count()))
    else:
        response = r.get_ranges()
        for hit in response:
            print_json(hit.to_dict(include_meta=True))


if __name__ == '__main__':
    main()
