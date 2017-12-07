#!/usr/bin/env python3
from jackal import Core, Service
from jackal.utils import print_line, print_json


def main():
    core = Core()
    response = core.get_services()
    if isinstance(response, int):
        print_line("Number of services: {}".format(response))
    else:
        for hit in response:
            hit = hit.to_dict(include_meta=True)
            source = hit.pop('_source')
            print_json({**hit, **source})


def overview():
    """
        Function to create an overview of the services.
        Will print a list of ports found an the number of times the port was seen.
    """
    search = Service.search()
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
