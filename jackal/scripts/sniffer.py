#!/usr/bin/ev python3
import ipaddress
import logging
import sys
from socket import AddressFamily

from jackal import HostDoc, HostSearch, RangeDoc, RangeSearch
from jackal.utils import print_error, print_notification, print_success

logging.getLogger("scapy.runtime").setLevel(logging.ERROR)

try:
    from scapy.all import ARP, TCP, UDP, sniff
except ImportError:
    print_error("This tool requires scapy")
    sys.exit(1)


class Sniffer(object):
    """
        Sniffer class
    """

    def __init__(self, netmask='255.255.255.0', include_public=False, own_ip=None):
        self.ip_list = set()
        self.ip_ranges = set()
        self.rs = RangeSearch()
        self.hs = HostSearch()
        self.netmask = netmask
        self.include_public = include_public
        if own_ip:
            self.ip_list.add(own_ip)


    def callback(self, pkt):
        """
            Callback for the scapy sniffer
        """
        if ARP in pkt:
            self.parse_ip(pkt.sprintf("%ARP.psrc%"))
        if TCP in pkt or UDP in pkt:
            self.parse_ip(pkt.sprintf("%IP.src%"))
            self.parse_ip(pkt.sprintf("%IP.dst%"))


    def parse_ip(self, ip):
        """
            Parses an ip to extract the range.
            Calls new_ip and new_range when a new ip is found.
            Excludes ranges that are multicast and loopback.
        """
        if not ip in self.ip_list:
            try:
                ip_address = ipaddress.ip_address(ip)
                use = not (ip_address.is_multicast or ip_address.is_unspecified or ip_address.is_reserved or ip_address.is_loopback or ip_address.is_link_local)
                if use and (self.include_public or ip_address.is_private):
                    self.new_ip(ip)
                    network = ipaddress.IPv4Network("{}/{}".format(ip,
                        self.netmask), strict=False)
                    self.new_range(str(network))
            except ValueError:
                pass


    def new_ip(self, ip):
        """
            Function called when a new IP address was seen
        """
        if not ip in self.ip_list:
            self.ip_list.add(ip)
            doc = HostDoc(address=ip)
            doc.add_tag('sniffer')
            self.hs.merge(doc)
            print_success("New ip address: {}".format(ip))


    def new_range(self, ip_range):
        """
            Function called when a new range was seen
        """
        if not ip_range in self.ip_ranges:
            self.ip_ranges.add(ip_range)
            doc = RangeDoc(range=ip_range)
            doc.add_tag('sniffer')
            self.rs.merge(doc)
            print_success("New ip range: {}".format(ip_range))


    def start(self):
        """
            Starts the sniffing
        """
        print_notification("Starting sniffer")
        print_notification("Press ctrl-c to stop sniffing")
        try:
            sniff(prn=self.callback, store=0)
        except PermissionError:
            print_error("Please run this tool as root")


def main():
    netmask = '255.255.255.0'
    own_ip = None
    try:
        import psutil
        interfaces = psutil.net_if_addrs()
        for name, details in interfaces.items():
            for detail in details:
                if detail.family == AddressFamily.AF_INET:
                    ip_address = ipaddress.ip_address(detail.address)
                    if not ip_address.is_link_local:
                        netmask = detail.netmask
                        own_ip = str(ip_address)
    except ImportError:
        pass

    sniffer = Sniffer(netmask=netmask, own_ip=own_ip)
    sniffer.start()


if __name__ == '__main__':
    main()
