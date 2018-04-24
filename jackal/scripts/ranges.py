#!/usr/bin/env python3
"""
Script to list all of the ranges
"""
import argparse

from jackal import RangeSearch, Host, Range
from jackal.utils import print_json, print_line, print_error, print_notification, print_success


def main():
    rs = RangeSearch()
    arg = argparse.ArgumentParser(parents=[rs.argparser], conflict_handler='resolve')
    arg.add_argument('-c', '--count', help="Only show the number of results", action="store_true")
    arg.add_argument('-a', '--add', help="Add a new range", action="store_true")
    arguments = arg.parse_args()
    if arguments.add:
        print_notification("Adding new range")
        range_str = input("What range do you want to add? ")
        r = rs.id_to_object(range_str)
        print_success("Added a new range:")
        print_json(r.to_dict(include_meta=True))
    elif arguments.count:
        print_line("Number of ranges: {}".format(rs.argument_count()))
    else:
        response = rs.get_ranges()
        for hit in response:
            print_json(hit.to_dict(include_meta=True))

def overview():
    """
        Creates a overview of the hosts per range.
    """
    range_search = RangeSearch()
    ranges = range_search.get_ranges()
    if ranges:
        formatted_ranges = []
        tags_lookup = {}
        for r in ranges:
            formatted_ranges.append({'mask': r.range})
            tags_lookup[r.range] = r.tags
        search = Host.search()
        search = search.filter('term', status='up')
        search.aggs.bucket('hosts', 'ip_range', field='address', ranges=formatted_ranges)
        response = search.execute()
        print_line("{0:<18} {1:<6} {2}".format("Range", "Count", "Tags"))
        print_line("-" * 60)
        for entry in response.aggregations.hosts.buckets:
            print_line("{0:<18} {1:<6} {2}".format(entry.key, entry.doc_count, tags_lookup[entry.key]))
    else:
        print_error("No ranges defined.")




if __name__ == '__main__':
    overview()
