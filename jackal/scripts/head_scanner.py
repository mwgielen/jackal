#!/usr/bin/env python3
import grequests
import urllib3
from gevent.pool import Pool
from jackal import Credential, Logger, ServiceSearch
from jackal.utils import print_error, print_notification, print_success


def check_service(service):
    """
        Connect to a service to see if it is a http or https server.
    """
    # Try HTTP
    result = grequests.map([grequests.head('http://{}:{}'.format(service.address, service.port), timeout=1)])[0]
    service.add_tag('header_scan')
    if result:
        print_success("Found http service on {}:{}".format(service.address, service.port))
        service.add_tag('http')
        try:
            service.banner = result.headers['Server']
        except KeyError:
            pass
    else:
        # Try HTTPS
        result = grequests.map([grequests.head('https://{}:{}'.format(service.address, service.port), verify=False, timeout=3)])[0]
        if result:
            service.add_tag('https')
            print_success("Found https service on {}:{}".format(service.address, service.port))
            try:
                service.banner = result.headers['Server']
            except KeyError:
                pass

    service.save()

def main():
    """
        Retrieves services starts check_service in a gevent pool of 100.
    """
    search = ServiceSearch()
    services = search.get_services(up=True, tags=['!header_scan'])
    print_notification("Scanning {} services".format(len(services)))

    # Disable the insecure request warning
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    pool = Pool(100)
    count = 0
    for service in services:
        count += 1
        if count % 50 == 0:
            print_notification("Checking {}/{} services".format(count, len(services)))
        pool.spawn(check_service, service)

    pool.join()


if __name__ == '__main__':
    main()
