#!/usr/bin/env python3
from jackal.core import Services, Ranges, Hosts, config
from jackal.utils import print_notification
from elasticsearch_dsl.connections import connections


def main():
    services = Services()
    hosts = Hosts()
    ranges = Ranges()
    print_notification("Connected to: {} [{}]".format(connections.get_connection().info()['cluster_name'], config.host))
    print_notification("Index: {}".format(config.index))
    print_notification("Number of hosts defined: {}".format(services.count()))
    print_notification("Number of ranges defined: {}".format(hosts.count()))
    print_notification("Number of services defined: {}".format(ranges.count()))


if __name__ == '__main__':
    main()