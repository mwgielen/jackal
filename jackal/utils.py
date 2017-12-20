"""
    Provides some utility functions to aid printing for usage with pipes.
"""
import datetime
import json
import sys
from libnmap.parser import NmapParser
from jackal import HostSearch, ServiceSearch
from jackal import HostDoc, ServiceDoc

def datetime_handler(x):
    if isinstance(x, datetime.datetime):
        return x.isoformat()
    raise TypeError("Unknown type")


def print_line(text):
    import signal
    signal.signal(signal.SIGPIPE, signal.SIG_DFL)
    """
        Print the given line to stdout
    """
    try:
        sys.stdout.write(text)
        if not text.endswith('\n'):
            sys.stdout.write('\n')
        sys.stdout.flush()
    except IOError:
        sys.exit(0)


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

def import_nmap(input_file, tag):
    """
        Import the given nmap file, returns the number of imported hosts.
    """
    core = HostSearch(arguments=False)
    parser = NmapParser()
    report = parser.parse_fromfile(input_file)

    imported_hosts = 0
    for nmap_host in report.hosts:
        imported_hosts += 1
        host = HostDoc()
        host.address = nmap_host.address
        host.tags = [tag, nmap_host.status]
        if nmap_host.os_fingerprinted:
            host.os = nmap_host.os_fingerprint
        host.hostname = nmap_host.hostnames

        for service in nmap_host.services:
            serv = ServiceDoc(** service.get_dict())
            serv.address = nmap_host.address
            serv.save()
            if service.state == 'open':
                host.open_ports.append(service.port)
            if service.state == 'closed':
                host.closed_ports.append(service.port)
            if service.state == 'filtered':
                host.filtered_ports.append(service.port)

        core.merge(host)

    return imported_hosts
