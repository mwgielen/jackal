#!/usr/bin/env python3
from jackal import Services, ServiceDoc
from jackal.utils import print_line, print_json


def main():
    services = Services()
    arguments = services.core_parser.parse_args()
    if arguments.count:
        print_line("Number of services: {}".format(services.argument_count()))
    else:
        response = services.get_services()
        for hit in response:
            print_json(hit.to_dict())


def overview():
    """
        Function to create an overview of the services.
        Will print a list of ports found an the number of times the port was seen.
    """
    search = ServiceDoc.search()
    search = search.filter("term", state='open')
    search.aggs.bucket('port_count', 'terms', field='port', order={'_count': 'desc'}, size=100) \
        .metric('unique_count', 'cardinality', field='address')
    response = search.execute()
    print_line("Port     Count")
    print_line("---------------")
    for entry in response.aggregations.port_count.buckets:
        print_line("{0:<7}  {1}".format(entry.key, entry.unique_count.value))


if __name__ == '__main__':
    main()
