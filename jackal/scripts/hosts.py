#!/usr/bin/env python3
"""
Script to list all of the ranges
"""
import sys

from jackal import Hosts
from jackal.utils import print_json, print_line


def main():
    hosts = Hosts()
    arguments = hosts.core_parser.parse_args()
    if arguments.count:
        print_line("Number of hosts: {}".format(hosts.argument_count()))
    else:
        response = hosts.get_hosts()
        for hit in response:
            hit = hit.to_dict(include_meta=True)
            source = hit.pop('_source')
            print_json({**hit, **source})


if __name__ == '__main__':
    main()
