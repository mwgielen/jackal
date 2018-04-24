#!/usr/bin/env python3
import argparse
import os
import subprocess
import sys
import datetime

from jackal import HostSearch, RangeSearch, Service, ServiceSearch, Logger
from jackal.config import Config
from jackal.utils import print_error, print_notification, print_success
from libnmap.parser import NmapParser, NmapParserException


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
                stats = import_nmap(f.read(), 'nmap_import', check_function=all_hosts, import_services=True)
            stats['file'] = arg
            Logger().log('import_nmap', 'Imported nmap file', stats=stats)
        except NmapParserException:
            print_error("File could not be parsed: {}".format(arg))
        except FileNotFoundError:
            pass


def import_nmap(result, tag, check_function=all_hosts, import_services=False):
    """
        Imports the given nmap result.
    """
    host_search = HostSearch(arguments=False)
    service_search = ServiceSearch()
    parser = NmapParser()
    report = parser.parse_fromstring(result)
    imported_hosts = 0
    imported_services = 0
    for nmap_host in report.hosts:
        if check_function(nmap_host):
            imported_hosts += 1
            host = host_search.id_to_object(nmap_host.address)
            host.status = nmap_host.status
            if nmap_host.os_fingerprinted:
                host.os = nmap_host.os_fingerprint
            if nmap_host.hostnames:
                host.hostname.extend(nmap_host.hostnames)
            if import_services:
                for service in nmap_host.services:
                    imported_services += 1
                    serv = Service(**service.get_dict())
                    serv.address = nmap_host.address
                    service_id = service_search.object_to_id(serv)
                    if service_id:
                        # Existing object, save the banner and script results.
                        serv_old = Service.get(service_id)
                        if service.banner:
                            serv_old.banner = service.banner
                        # TODO implement
                        # if service.script_results:
                            # serv_old.script_results.extend(service.script_results)
                        serv_old.save()
                    else:
                        # New object
                        serv.address = nmap_host.address
                        serv.save()
                    if service.state == 'open':
                        host.open_ports.append(service.port)
                    if service.state == 'closed':
                        host.closed_ports.append(service.port)
                    if service.state == 'filtered':
                        host.filtered_ports.append(service.port)
            host.save()
    if imported_hosts:
        print_success("Imported {} hosts, with tag {}".format(imported_hosts, tag))
    else:
        print_error("No hosts found")
    return {'hosts': imported_hosts, 'services': imported_services}


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
    config = Config()
    arguments = ['nmap']
    arguments.extend(ips)
    arguments.extend(nmap_args)
    output_file = ''
    now = datetime.datetime.now()
    if not '-oA' in nmap_args:
        output_name = 'nmap_jackal_{}'.format(now.strftime("%Y-%m-%d %H:%M"))
        path_name = os.path.join(config.get('nmap', 'directory'), output_name)
        print_notification("Writing output of nmap to {}".format(path_name))
        if not os.path.exists(config.get('nmap', 'directory')):
            os.makedirs(config.get('nmap', 'directory'))
        output_file = path_name + '.xml'
        arguments.extend(['-oA', path_name])
    else:
        output_file = nmap_args[nmap_args.index('-oA') + 1] + '.xml'

    print_notification("Starting nmap")
    subprocess.call(arguments)

    with open(output_file, 'r') as f:
        return f.read()


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
        nmap_args.append('-n')
        check_function = include_up_hosts
    elif arguments.type == 'lookup':
        tag = 'nmap_lookup'
        nmap_args.append('-sL')
        check_function = include_hostnames

    ranges = rs.get_ranges(tags=['!{}'.format(tag)])
    ranges = [r for r in ranges]
    ips = []
    for r in ranges:
        ips.append(r.range)

    print_notification("Running nmap with args: {} on {} range(s)".format(nmap_args, len(ips)))
    result = nmap(nmap_args, ips)
    stats = import_nmap(result, tag, check_function)
    stats['scanned_ranges'] = len(ips)

    Logger().log('nmap_discover', "Nmap discover with args: {} on {} range(s)".format(nmap_args, len(ips)), stats)

    for r in ranges:
        r.add_tag(tag)
        r.save()


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
    tags = ["!nmap_" + tag  for tag in tags]

    hosts = hs.get_hosts(tags=tags)
    hosts = [host for host in hosts]

    # Create the nmap arguments
    nmap_args = []
    nmap_args.extend(extra_nmap_args)
    nmap_args.extend(options[arguments.type].split(' '))

    # Run nmap
    print_notification("Running nmap with args: {} on {} hosts(s)".format(nmap_args, len(hosts)))
    if len(hosts):
        result = nmap(nmap_args, [str(h.address) for h in hosts])
        # Import the nmap result
        for host in hosts:
            host.add_tag("nmap_{}".format(arguments.type))
            host.save()
        print_notification("Nmap done, importing results")
        stats = import_nmap(result, "nmap_{}".format(arguments.type), check_function=all_hosts, import_services=True)
        stats['scanned_hosts'] = len(hosts)
        stats['type'] = arguments.type

        Logger().log('nmap_scan', "Performed nmap {} scan on {} hosts".format(arguments.type, len(hosts)), stats)
    else:
        print_notification("No hosts found")


def nmap_smb_vulnscan():
    """
        Scans available smb services in the database for smb signing and ms17-010.
    """
    service_search = ServiceSearch()
    services = service_search.get_services(ports=['445'], tags=['!smb_vulnscan'], up=True)
    services = [service for service in services]
    service_dict = {}
    for service in services:
        service_dict[str(service.address)] = service

    nmap_args = "-Pn -n --disable-arp-ping --script smb-security-mode.nse,smb-vuln-ms17-010.nse -p 445".split(" ")

    if services:
        result = nmap(nmap_args, [str(s.address) for s in services])
        parser = NmapParser()
        report = parser.parse_fromstring(result)
        smb_signing = 0
        ms17 = 0
        for nmap_host in report.hosts:
            for script_result in nmap_host.scripts_results:
                script_result = script_result.get('elements', {})
                service = service_dict[str(nmap_host.address)]
                service.add_tag('smb_vulnscan')
                if script_result.get('message_signing', '') == 'disabled':
                    print_success("({}) SMB Signing disabled".format(nmap_host.address))
                    service.add_tag('smb_signing_disabled')
                    smb_signing += 1
                if script_result.get('CVE-2017-0143', {}).get('state', '') == 'VULNERABLE':
                    print_success("({}) Vulnerable for MS17-010".format(nmap_host.address))
                    service.add_tag('MS17-010')
                    ms17 += 1
                service.update(tags=service.tags)

        print_notification("Done")
        stats = {'smb_signing': smb_signing, 'MS17_010': ms17, 'scanned_services': len(services)}

        Logger().log('smb_vulnscan', 'Scanned {} smb services for vulnerabilities'.format(len(services)), stats)
    else:
        print_notification("No services found to scan.")


if __name__ == '__main__':
    nmap_scan()
