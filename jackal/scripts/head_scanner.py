#!/usr/bin/env python3
import requests
import urllib3
from requests.exceptions import ConnectionError, ConnectTimeout, ReadTimeout
from gevent.pool import Pool
from gevent import monkey
from jackal import Credential, Logger, ServiceSearch
from jackal.utils import print_error, print_notification, print_success
from OpenSSL.SSL import Error

monkey.patch_socket()

def check_service(service):
    """
        Connect to a service to see if it is a http or https server.
    """
    # Try HTTP
    service.add_tag('header_scan')
    http = False
    try:
        result = requests.head('http://{}:{}'.format(service.address, service.port), timeout=1)
        print_success("Found http service on {}:{}".format(service.address, service.port))
        service.add_tag('http')
        http = True
        try:
            service.banner = result.headers['Server']
        except KeyError:
            pass
    except (ConnectionError, ConnectTimeout, ReadTimeout, Error):
        pass

    if not http:
        # Try HTTPS
        try:
            result = requests.head('https://{}:{}'.format(service.address, service.port), verify=False, timeout=3)
            service.add_tag('https')
            print_success("Found https service on {}:{}".format(service.address, service.port))
            try:
                service.banner = result.headers['Server']
            except KeyError:
                pass
        except (ConnectionError, ConnectTimeout, ReadTimeout, Error):
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
