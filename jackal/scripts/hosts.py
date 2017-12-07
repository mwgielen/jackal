#!/usr/bin/env python3
"""
Script to list all of the ranges
"""
import sys

from jackal import Core, Host
from jackal.utils import print_json, print_line


def main():
    core = Core()
    response = core.get_hosts()
    if isinstance(response, int):
        print_line("Number of hosts: {}".format(response))
    else:
        for hit in response:
            hit = hit.to_dict(include_meta=True)
            source = hit.pop('_source')
            print_json({**hit, **source})


if __name__ == '__main__':
    main()
