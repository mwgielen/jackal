#!/usr/bin/env python3
import argparse

from libnmap.parser import NmapParser
from libnmap.process import NmapProcess

from jackal import HostDoc, HostSearch, RangeSearch
from jackal.utils import print_notification, print_success, print_error


def all_hosts(**kwargs):
    """
        Returns true for all nmap hosts
    """
    return True


def import_nmap(result, tag, check_function=all_hosts):
    """
        Imports the given nmap result.
    """
    hs = HostSearch(arguments=False)
    parser = NmapParser()
    report = parser.parse_fromstring(result)
    imports = 0
    for nmap_host in report.hosts:
        if check_function(nmap_host):
            imports += 1
            host = HostDoc()
            host.address = nmap_host.address
            host.add_tag(tag)
            if nmap_host.os_fingerprinted:
                host.os = nmap_host.os_fingerprint
            if nmap_host.hostnames:
                host.hostname = nmap_host.hostnames
            hs.merge(host)
    if imports:
        print_success("Imported {} hosts, with tag {}".format(imports, tag))
    else:
        print_error("No hosts found")


def include_hostnames(nmap_host):
    """
        Function to filter out hosts with hostnames
    """
    if nmap_host.hostnames:
        return True
    return False


def include_pinged_hosts(nmap_host):
    """
        Includes only hosts that have the status 'up'
    """
    if nmap_host.status == 'up':
        return True
    return False


def nmap(nmap_args, ips):
    """
        Start an nmap process with the given args on the given ips.
    """
    print_notification("Running nmap with args: {} on {} range(s)".format(nmap_args, len(ips)))
    nm = NmapProcess(targets=ips, options=nmap_args)
    print_notification("Invoking sudo")
    nm.sudo_run()
    return nm.stdout


def nmap_discover():
    """
        This function retrieves ranges from jackal
        Uses two functions of nmap to find hosts:
            ping:   icmp / arp pinging of targets
            lookup: reverse dns lookup
    """
    rs = RangeSearch()
    rs_parser = rs.argparser
    arg = argparse.ArgumentParser(parents=[rs_parser], conflict_handler='resolve')
    arg.add_argument('type', metavar='type', \
        help='The type of nmap scan to do, choose from ping or lookup', \
        type=str, choices=['ping', 'lookup'])
    arguments, nmap_args = arg.parse_known_args()

    tag = None
    if arguments.type == 'ping':
        tag = 'nmap_ping'
        nmap_args.append('-sn')
        check_function = include_pinged_hosts
    elif arguments.type == 'lookup':
        tag = 'nmap_lookup'
        nmap_args.append('-sL')
        check_function = include_hostnames

    if arguments.tags or rs.is_pipe:
        ranges = rs.get_ranges()
    else:
        ranges = rs.search(tags='!{}'.format(tag))

    ips = []
    for r in ranges:
        ips.append(r.range)
        r.add_tag(tag)
        rs.merge(r)

    result = nmap(" ".join(nmap_args), ips)
    import_nmap(result, tag, check_function)


if __name__ == '__main__':
    nmap_discover()
