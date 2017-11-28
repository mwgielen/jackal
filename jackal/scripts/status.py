#!/usr/bin/env python3
from jackal.core import Core, config
from jackal.utils import print_notification
from elasticsearch_dsl.connections import connections


def main():
    core = Core(use_pipe=False)
    print_notification("Connected to: {} [{}]".format(connections.get_connection().info()['cluster_name'], config.host))
    print_notification("Index: {}".format(config.index))
    print_notification("Number of hosts defined: {}".format(core.total_hosts))
    print_notification("Number of ranges defined: {}".format(core.total_ranges))
    print_notification("Number of services defined: {}".format(core.total_services))


if __name__ == '__main__':
    main()