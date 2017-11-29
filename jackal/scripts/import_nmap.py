#!/usr/bin/env python3
import sys
import libnmap
from jackal.utils import import_nmap, print_notification, print_error, print_success


def main():
    for arg in sys.argv[1:]:
        print_notification("Importing nmap file: {}".format(arg))
        try:
            hosts_imported = import_nmap(arg, 'nmap_import')
            print_success("Hosts imported: {}".format(hosts_imported))
        except libnmap.parser.NmapParserException:
            print_error("File could not be parsed: {}".format(arg))


if __name__ == '__main__':
    main()
