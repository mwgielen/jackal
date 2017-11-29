#!/usr/bin/env python3
from jackal import Core
from jackal.utils import print_line, print_json


def main():
    core = Core()
    response = core.get_services()
    if isinstance(response, int):
        print_line("Number of services: {}".format(response))
    else:
        for hit in response:
            print_json(hit.to_dict())


if __name__ == '__main__':
    main()
