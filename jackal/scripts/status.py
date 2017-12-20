#!/usr/bin/env python3
from jackal.core import ServiceSearch, RangeSearch, HostSearch, config
from jackal.utils import print_notification
from elasticsearch_dsl.connections import connections


def main():
    services = ServiceSearch()
    hosts = HostSearch()
    ranges = RangeSearch()
    print_notification("Connected to: {} [{}]".format(connections.get_connection().info()['cluster_name'], config.get('jackal', 'host')))
    print_notification("Index: {}".format(config.get('jackal', 'index')))
    print_notification("Number of hosts defined: {}".format(hosts.count()))
    print_notification("Number of ranges defined: {}".format(ranges.count()))
    print_notification("Number of services defined: {}".format(services.count()))


if __name__ == '__main__':
    main()