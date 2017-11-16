"""
    Provides some utility functions to aid printing for usage with pipes.
"""
import datetime
import json
import sys
from libnmap.parser import NmapParser
from jackal import Host, Core

def datetime_handler(x):
    if isinstance(x, datetime.datetime):
        return x.isoformat()
    raise TypeError("Unknown type")


def print_line(text):
    """
        Print the given line to stdout
    """
    try:
        sys.stdout.write(text)
        if not text.endswith('\n'):
            sys.stdout.write('\n')
        sys.stdout.flush()
    except IOError:
        pass


def print_json(data):
    """
        Print the given data to stdout.
    """
    print_line(json.dumps(data, default=datetime_handler))


def print_notification(string):
    """
        Prints a grey [*] before the message
    """
    print_line('\033[94m[*]\033[0m {}'.format(string))


def print_success(string):
    """
        Prints a green [+] before the message
    """
    print_line('\033[92m[+]\033[0m {}'.format(string))


def print_error(string):
    """
        Prints a red [!] before the message
    """
    print_line('\033[91m[!]\033[0m {}'.format(string))

def import_nmap(input_file):
    """
        Import the given nmap file, returns the number of imported hosts.
    """
    core = Core()
    parser = NmapParser()
    report = parser.parse_fromfile(input_file)

    imported_hosts = 0
    for nmap_host in report.hosts:
        if nmap_host.status == 'up' or nmap_host.hostnames:
            imported_hosts += 1
            host = Host()
            host.address = nmap_host.address
            host.tags = ['nmap', nmap_host.status]
            if nmap_host.os_fingerprinted:
                host.os = nmap_host.os_fingerprint
            host.hostname = nmap_host.hostnames
            for service in nmap_host.services:
                host.services.append(service.get_dict())
            core.merge_host(host)
    return imported_hosts
