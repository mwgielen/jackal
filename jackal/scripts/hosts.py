#!/usr/bin/env python3
"""
Script to list all of the ranges
"""
import argparse

from jackal import HostSearch, Host
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


def overview():
    """
        Prints an overview of the tags of the hosts.
    """
    doc = Host()
    search = doc.search()
    search.aggs.bucket('tag_count', 'terms', field='tags', order={'_count': 'desc'}, size=100)
    response = search.execute()
    print_line("{0:<25} {1}".format('Tag', 'Count'))
    print_line("-" * 30)
    for entry in response.aggregations.tag_count.buckets:
        print_line("{0:<25} {1}".format(entry.key, entry.doc_count))

if __name__ == '__main__':
    main()
