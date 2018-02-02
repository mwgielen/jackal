#!/usr/bin/env python3
import argparse

from jackal import User, UserSearch
from jackal.utils import print_json, print_line


def main():
    users = UserSearch()
    arg = argparse.ArgumentParser(parents=[users.argparser], conflict_handler='resolve')
    arg.add_argument('-c', '--count', help="Only show the number of results", action="store_true")
    arguments = arg.parse_args()
    if arguments.count:
        print_line("Number of users: {}".format(users.argument_count()))
    else:
        response = users.get_users()
        for hit in response:
            print_json(hit.to_dict(include_meta=True))

