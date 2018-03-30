#!/usr/bin/env python3
import sys

from elasticsearch import ConnectionError, TransportError
from elasticsearch_dsl.connections import connections
from jackal.core import HostSearch, RangeSearch, ServiceSearch, UserSearch, CredentialSearch, config
from jackal.utils import print_error, print_notification
from jackal.documents import Host, Range, Service, User, Credential, Log


def main():
    services = ServiceSearch()
    hosts = HostSearch()
    ranges = RangeSearch()
    users = UserSearch()
    creds = CredentialSearch()
    try:
        print_notification("Connected to: {} [{}]".format(connections.get_connection().info()['cluster_name'], config.get('jackal', 'host')))
    except (ConnectionError, TransportError) as e:
        print_error("Cannot connect to the elasticsearch instance")
        print_error(e)
        sys.exit(1)

    print_notification("Index: {}".format(config.get('jackal', 'index')))
    host_count = hosts.count()
    if not host_count is None:
        print_notification("Number of hosts defined: {}".format(hosts.count()))
        print_notification("Number of ranges defined: {}".format(ranges.count()))
        print_notification("Number of services defined: {}".format(services.count()))
        print_notification("Number of users defined: {}".format(users.count()))
        print_notification("Number of credentials defined: {}".format(creds.count()))


def initialize_indices():
    """
        Initializes the indices
    """
    Host.init()
    Range.init()
    Service.init()
    User.init()
    Credential.init()
    Log.init()


if __name__ == '__main__':
    main()
