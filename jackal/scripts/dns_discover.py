#!/usr/bin/env python3
import argparse
import ipaddress
import re
import socket
import subprocess

import dns.resolver
import psutil
from jackal import HostSearch, RangeSearch
from jackal.utils import print_error, print_notification, print_success


def get_configured_dns():
    """
        Returns the configured DNS servers with the use f nmcli.
    """
    ips = []
    try:
        output = subprocess.check_output(['nmcli', 'device', 'show'])
        output = output.decode('utf-8')

        for line in output.split('\n'):
            if 'DNS' in line:
                pattern = r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}"
                for hit in re.findall(pattern, line):
                    ips.append(hit)
    except FileNotFoundError:
        pass
    return ips


def get_resolv_dns():
    """
        Returns the dns servers configured in /etc/resolv.conf
    """
    result = []
    try:
        for line in open('/etc/resolv.conf', 'r'):
            if line.startswith('search'):
                result.append(line.strip().split(' ')[1])
    except FileNotFoundError:
        pass
    return result


def zone_transfer(address, dns_name):
    """
        Tries to perform a zone transfer.
    """
    ips = []
    try:
        print_notification("Attempting dns zone transfer for {} on {}".format(dns_name, address))
        z = dns.zone.from_xfr(dns.query.xfr(address, dns_name))
    except dns.exception.FormError:
        print_notification("Zone transfer not allowed")
        return ips
    names = z.nodes.keys()
    print_success("Zone transfer successfull for {}, found {} entries".format(address, len(names)))
    for n in names:
        node = z[n]
        data = node.get_rdataset(dns.rdataclass.IN, dns.rdatatype.A)
        if data:
            # TODO add hostnames to entries.
            # hostname = n.to_text()
            for item in data.items:
                address = item.address
                ips.append(address)
    return ips


def resolve_domains(domains, disable_zone=False):
    """
        Resolves the list of domains and returns the ips.
    """
    dnsresolver = dns.resolver.Resolver()

    ips = []

    for domain in domains:
        print_notification("Resolving {}".format(domain))
        try:
            result = dnsresolver.query(domain, 'A')
            for a in result.response.answer[0]:
                ips.append(str(a))
                if not disable_zone:
                    ips.extend(zone_transfer(str(a), domain))
        except dns.resolver.NXDOMAIN as e:
            print_error(e)
    return ips


def parse_ips(ips, netmask, include_public):
    """
        Parses the list of ips, turns these into ranges based on the netmask given.
        Set include_public to True to include public IP adresses.
    """
    hs = HostSearch()
    rs = RangeSearch()
    ranges = []
    ips = list(set(ips))
    included_ips = []
    print_success("Found {} ips".format(len(ips)))
    for ip in ips:
        ip_address = ipaddress.ip_address(ip)
        if include_public or ip_address.is_private:
            # To stop the screen filling with ranges.
            if len(ips) < 15:
                print_success("Found ip: {}".format(ip))
            host = hs.id_to_object(ip)
            host.add_tag('dns_discover')
            host.save()
            r = str(ipaddress.IPv4Network("{}/{}".format(ip, netmask), strict=False))
            ranges.append(r)
            included_ips.append(ip)
        else:
            print_notification("Excluding ip {}".format(ip))

    ranges = list(set(ranges))
    print_success("Found {} ranges".format(len(ranges)))
    for rng in ranges:
        # To stop the screen filling with ranges.
        if len(ranges) < 15:
            print_success("Found range: {}".format(rng))
        r = rs.id_to_object(rng)
        r.add_tag('dns_discover')
        r.save()

    stats = {}
    stats['ips'] = included_ips
    stats['ranges'] = ranges
    return stats


def main():
    netmask = '255.255.255.0'
    interfaces = psutil.net_if_addrs()
    for _, details in interfaces.items():
        for detail in details:
            if detail.family == socket.AF_INET:
                ip_address = ipaddress.ip_address(detail.address)
                if not (ip_address.is_link_local or ip_address.is_loopback):
                    netmask = detail.netmask
                    break

    parser = argparse.ArgumentParser(
        description="Uses the configured DNS servers to estimate ranges.")
    parser.add_argument(
        "--include-public", help="Include public IP addresses", action="store_true")
    parser.add_argument(
        "-nm", "--netmask", help="The netmask to use to create ranges, default: {}".format(netmask), type=str, default=netmask)
    parser.add_argument("--no-zone", help="Disable to attempt to get a zone transfer from the dns server.", action="store_true")
    arguments = parser.parse_args()
    ips = []
    ips.extend(get_configured_dns())
    domains = get_resolv_dns()
    ips.extend(resolve_domains(domains, arguments.no_zone))
    stats = parse_ips(ips, arguments.netmask, arguments.include_public)
    print_notification("Found {} ips and {} ranges".format(
        len(stats['ips']), len(stats['ranges'])))


if __name__ == '__main__':
    main()
