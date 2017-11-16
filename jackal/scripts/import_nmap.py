#!/usr/bin/env python3
from jackal import Core, Host
from jackal.utils import print_notification, print_error, print_success
from libnmap.parser import NmapParser


core = Core(use_pipe=False)

def parse_nmap(input_file):
    parser = NmapParser()
    print_notification("Jackal importing file: {}".format(input_file))
    report = parser.parse_fromfile(input_file)
    print_notification("Number of hosts in the nmap file: {}".format(report.hosts_total))
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
    if imported_hosts == 0:
        print_error("No hosts imported, all hosts' status was unknown or down, only hosts with status 'up' or hostname set are imported.")
    else:
        print_success("Import done, hosts imported: {}".format(imported_hosts))

def main():
    if core.arguments.file:
        parse_nmap(core.arguments.file)

if __name__ == '__main__':
    main()
