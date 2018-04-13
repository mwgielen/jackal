#!/usr/bin/env python3
import argparse
import json
import sys
import ipaddress

import dns.resolver
from jackal import HostSearch, UserSearch, Logger
from jackal.documents import User
from jackal.utils import print_notification, print_success


def get_field(obj, field):
    try:
        return obj['attributes'][field][0]
    except KeyError:
        return ""


def resolve_ip(dns_name):
    dnsresolver = dns.resolver.Resolver()
    try:
        result = dnsresolver.query(dns_name, 'A')
        return str(result.response.answer[0][0])
    except dns.resolver.NXDOMAIN:
        return ''
    except dns.resolver.Timeout:
        return ''


class Computer(object):
    """
        Computer object, represents a ldap computer
    """

    def __init__(self, dns_hostname, description='', os='', ip='', group_id=0):
        self.dns_hostname = dns_hostname
        self.description = description
        self.os = os
        self.ip = ip
        self.group_id = group_id

    @property
    def dc(self):
        return self.group_id == 516 or self.group_id == 512


def parse_single_computer(entry):
    """
        Parse the entry into a computer object.
    """
    computer = Computer(dns_hostname=get_field(entry, 'dNSHostName'), description=get_field(
        entry, 'description'), os=get_field(entry, 'operatingSystem'), group_id=get_field(entry, 'primaryGroupID'))
    try:
        ip = str(ipaddress.ip_address(get_field(entry, 'IPv4')))
    except ValueError:
        ip = ''

    if ip:
        computer.ip = ip
    elif computer.dns_hostname:
        computer.ip = resolve_ip(computer.dns_hostname)
    return computer


def parse_domain_computers(filename):
    """
        Parse the file and extract the computers, import the computers that resolve into jackal.
    """
    with open(filename) as f:
        data = json.loads(f.read())
    hs = HostSearch()
    count = 0
    entry_count = 0
    print_notification("Parsing {} entries".format(len(data)))
    for system in data:
        entry_count += 1
        parsed = parse_single_computer(system)
        if parsed.ip:
            host = hs.id_to_object(parsed.ip)
            host.description.append(parsed.description)
            host.hostname.append(parsed.dns_hostname)
            if parsed.os:
                host.os = parsed.os
            host.domain_controller = parsed.dc
            host.add_tag('domaindump')
            host.save()
            count += 1
        sys.stdout.write('\r')
        sys.stdout.write(
            "[{}/{}] {} resolved".format(entry_count, len(data), count))
        sys.stdout.flush()
    sys.stdout.write('\r')
    return count


# from https://blogs.technet.microsoft.com/askpfeplat/2014/01/15/understanding-the-useraccountcontrol-attribute-in-active-directory/
uac_flags = {'ACCOUNT_DISABLED':                0x00000002,
             'HOMEDIR_REQUIRED':                0x00000008,
             'LOCKOUT':                         0x00000010,
             'PASSWD_NOTREQD':                  0x00000020,
             'PASSWD_CANT_CHANGE':              0x00000040,
             'ENCRYPTED_TEXT_PASSWORD_ALLOWED': 0x00000080,
             'NORMAL_ACCOUNT':                  0x00000200,
             'INTERDOMAIN_TRUST_ACCOUNT':       0x00000800,
             'WORKSTATION_ACCOUNT':             0x00001000,
             'SERVER_TRUST_ACCOUNT':            0x00002000,
             'DONT_EXPIRE_PASSWD':              0x00010000,
             'SMARTCARD_REQUIRED':              0x00040000,
             'TRUSTED_FOR_DELEGATION':          0x00080000,
             'NOT_DELEGATED':                   0x00100000,
             'USE_DES_KEY_ONLY':                0x00200000,
             'DONT_REQUIRE_PREAUTH':            0x00400000,
             'PASSWORD_EXPIRED':                0x00800000,
             'TRUSTED_TO_AUTHENTICATE_FOR_DELEGATION': \
                                                0x01000000,
             'NO_AUTH_DATA_REQUIRED':           0x02000000,
             'PARTIAL_SECRETS_ACCOUNT':         0x04000000,
            }


def parse_user(entry, domain_groups):
    """
        Parses a single entry from the domaindump
    """
    result = {}
    distinguished_name = get_field(entry, 'distinguishedName')
    result['domain'] = ".".join(distinguished_name.split(',DC=')[1:])
    result['name'] = get_field(entry, 'name')
    result['username'] = get_field(entry, 'sAMAccountName')
    result['description'] = get_field(entry, 'description')
    result['sid'] = get_field(entry, 'objectSid').split('-')[-1]

    primary_group = get_field(entry, 'primaryGroupID')
    member_of = entry['attributes'].get('memberOf', [])
    groups = []
    for member in member_of:
        for e in member.split(','):
            if e.startswith('CN='):
                groups.append(e[3:])
    groups.append(domain_groups.get(primary_group, ''))
    result['groups'] = groups

    uac = int(get_field(entry, 'userAccountControl'))
    flags = []
    for flag, value in uac_flags.items():
        if uac & value:
            flags.append(flag)
    result['flags'] = flags
    return result


def parse_domain_users(domain_users_file, domain_groups_file):
    """
        Parses the domain users and groups files.
    """
    with open(domain_users_file) as f:
        users = json.loads(f.read())

    domain_groups = {}
    if domain_groups_file:
        with open(domain_groups_file) as f:
            groups = json.loads(f.read())
            for group in groups:
                sid = get_field(group, 'objectSid')
                domain_groups[int(sid.split('-')[-1])] = get_field(group, 'cn')

    user_search = UserSearch()
    count = 0
    total = len(users)
    print_notification("Importing {} users".format(total))
    for entry in users:
        result = parse_user(entry, domain_groups)
        user = user_search.id_to_object(result['username'])
        user.name = result['name']
        user.domain.append(result['domain'])
        user.description = result['description']
        user.groups.extend(result['groups'])
        user.flags.extend(result['flags'])
        user.sid = result['sid']
        user.add_tag("domaindump")
        user.save()
        count += 1
        sys.stdout.write('\r')
        sys.stdout.write("[{}/{}]".format(count, total))
        sys.stdout.flush()
    sys.stdout.write('\r')
    return count


def import_domaindump():
    """
        Parses ldapdomaindump files and stores hosts and users in elasticsearch.
    """
    parser = argparse.ArgumentParser(
        description="Imports users, groups and computers result files from the ldapdomaindump tool, will resolve the names from domain_computers output for IPs")
    parser.add_argument("files", nargs='+',
                        help="The domaindump files to import")
    arguments = parser.parse_args()
    domain_users_file = ''
    domain_groups_file = ''
    computer_count = 0
    user_count = 0
    stats = {}
    for filename in arguments.files:
        if filename.endswith('domain_computers.json'):
            print_notification('Parsing domain computers')
            computer_count = parse_domain_computers(filename)
            if computer_count:
                stats['hosts'] = computer_count
                print_success("{} hosts imported".format(computer_count))
        elif filename.endswith('domain_users.json'):
            domain_users_file = filename
        elif filename.endswith('domain_groups.json'):
            domain_groups_file = filename
    if domain_users_file:
        print_notification("Parsing domain users")
        user_count = parse_domain_users(domain_users_file, domain_groups_file)
        if user_count:
            print_success("{} users imported".format(user_count))
            stats['users'] = user_count
    Logger().log("import_domaindump", 'Imported domaindump, found {} user, {} systems'.format(user_count, computer_count), stats)


if __name__ == '__main__':
    import_domaindump()
