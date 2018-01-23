#!/usr/bin/env python3
import argparse
import sys

from libnmap.parser import NmapParser, NmapParserException
from libnmap.process import NmapProcess

from jackal import HostDoc, HostSearch, RangeSearch, ServiceDoc, ServiceSearch
from jackal.utils import print_error, print_notification, print_success
from jackal.config import Config


def all_hosts(*args, **kwargs):
    """
        Returns true for all nmap hosts
    """
    return True

def import_file():
    for arg in sys.argv[1:]:
        print_notification("Importing nmap file: {}".format(arg))
        try:
            with open(arg, 'r') as f:
                import_nmap(f.read(), 'nmap_import', check_function=all_hosts, import_services=True)
        except NmapParserException:
            print_error("File could not be parsed: {}".format(arg))
        except FileNotFoundError:
            pass


def import_nmap(result, tag, check_function=all_hosts, import_services=False):
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
            host.status = nmap_host.status
            if nmap_host.os_fingerprinted:
                host.os = nmap_host.os_fingerprint
            if nmap_host.hostnames:
                host.hostname = nmap_host.hostnames
            if import_services:
                for service in nmap_host.services:
                    serv = ServiceDoc(**service.get_dict())
                    serv.address = nmap_host.address
                    serv.save()
                    if service.state == 'open':
                        host.open_ports.append(service.port)
                    if service.state == 'closed':
                        host.closed_ports.append(service.port)
                    if service.state == 'filtered':
                        host.filtered_ports.append(service.port)
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


def include_up_hosts(nmap_host):
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
        check_function = include_up_hosts
    elif arguments.type == 'lookup':
        tag = 'nmap_lookup'
        nmap_args.append('-sL')
        check_function = include_hostnames

    ranges = rs.get_ranges(tags='!{}'.format(tag))
    ranges = [r for r in ranges]
    ips = []
    for r in ranges:
        ips.append(r.range)

    nmap_args= " ".join(nmap_args)
    print_notification("Running nmap with args: {} on {} range(s)".format(nmap_args, len(ips)))
    result = nmap(nmap_args, ips)
    import_nmap(result, tag, check_function)

    for r in ranges:
        ips.append(r.range)
        r.add_tag(tag)
        rs.merge(r)


def nmap_scan():
    """
        Scans the given hosts with nmap.
    """
    # Create the search and config objects
    hs = HostSearch()
    config = Config()

    # Static options to be able to figure out what options to use depending on the input the user gives.
    nmap_types = ['top10', 'top100', 'custom', 'top1000', 'all']
    options = {'top10':'--top-ports 10', 'top100':'--top-ports 100', 'custom': config.get('nmap', 'options'), 'top1000': '--top-ports 1000', 'all': '-p-'}

    # Create an argument parser
    hs_parser = hs.argparser
    argparser = argparse.ArgumentParser(parents=[hs_parser], conflict_handler='resolve', \
    description="Scans hosts from the database using nmap, any arguments that are not in the help are passed to nmap")
    argparser.add_argument('type', metavar='type', \
        help='The number of ports to scan: top10, top100, custom, top1000 (default) or all', \
        type=str, choices=nmap_types, default='top1000', const='top1000', nargs='?')
    arguments, extra_nmap_args = argparser.parse_known_args()

    # Fix the tags for the search
    tags = nmap_types[nmap_types.index(arguments.type):]
    tags = "!nmap_" + ",!nmap_".join(tags)

    hosts = hs.get_hosts(tags=tags)

    # Create the nmap arguments
    nmap_args = []
    nmap_args.extend(extra_nmap_args)
    nmap_args.append(options[arguments.type])
    nmap_args = " ".join(nmap_args)

    # Run nmap
    print_notification("Running nmap with args: {} on {} hosts(s)".format(nmap_args, len(hosts)))
    result = nmap(nmap_args, [h.address for h in hosts])
    # Import the nmap result
    import_nmap(result, "nmap_{}".format(arguments.type), check_function=all_hosts, import_services=True)


def nmap_smb_vulnscan():
    """
        Scans available smb services in the database for smb signing and ms17-010.
    """
    service_search = ServiceSearch()
    services = service_search.get_services(ports='445', tags='!smb_vulnscan', up=True)
    service_dict = {}
    for service in services:
        service_dict[service.address] = service

    nmap_args = "-Pn -n --disable_arp_ping --script smb-security-mode.nse,smb-vuln-ms17-010.nse -p 445"

    if services:
        result = nmap(nmap_args, [s.address for s in services])
        parser = NmapParser()
        report = parser.parse_fromstring(result)
        for nmap_host in report.hosts:
            for script_result in nmap_host.scripts_results:
                script_result = script_result.get('elements', {})
                service = service_dict[nmap_host.address]
                service.add_tag('smb_vulnscan')
                if script_result.get('message_signing', '') == 'disabled':
                    print_success("({}) SMB Signing disabled".format(nmap_host.address))
                    service.add_tag('smb_signing_disabled')
                if script_result.get('CVE-2017-0143', {}).get('state', '') == 'VULNERABLE':
                    print_success("({}) Vulnerable for MS17-010".format(nmap_host.address))
                    service.add_tag('MS17-010')
                service.update(tags=service.tags)
    else:
        print_notification("No services found to scan.")


if __name__ == '__main__':
    nmap_scan()
