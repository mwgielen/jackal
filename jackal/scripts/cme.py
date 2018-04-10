import sqlite3
import os
from os.path import expanduser, join, exists

from jackal import UserSearch, User, HostSearch, Host, Credential, CredentialSearch, Service, ServiceSearch, Logger
from jackal.utils import print_notification, print_error, print_success


def import_other(database_path):
    print_notification("Not yet implemented")


def add_credential(username, secret, domain, host_ip, cred_type, port, access_level=None, tag='cme_import'):
    credential_search = CredentialSearch(use_pipe=False)
    credential = credential_search.find_object(username=username, secret=secret, domain=domain, host_ip=host_ip)
    if not credential:
        credential = Credential()
        credential.username = username
        credential.secret = secret
        credential.domain = domain
        credential.host_ip = host_ip

    credential.type = cred_type
    credential.port = port
    if access_level:
        credential.access_level = access_level

    credential.add_tag(tag)
    credential.save()


def import_smb(database_path):
    print_notification("Importing SMB database")
    conn = sqlite3.connect(database_path)

    host_search = HostSearch(use_pipe=False)
    host_map = {}

    # Inserting the hosts
    computer_count = 0
    for computer in conn.execute("SELECT id, ip, hostname, domain, os, dc FROM computers"):
        host = host_search.id_to_object(computer[1])
        if computer[2]:
            host.hostname.append(computer[2])
        if computer[4]:
            host.os = computer[4]
        if computer[5]:
            host.domain_controller = computer[5]
        host_map[computer[0]] = computer[1]
        host.add_tag("cme_import")
        host.save()
        computer_count += 1

    # Inserting the retrieved users, services and credentials.
    user_count = 0
    admin_count = 0
    user_search = UserSearch(use_pipe=False)
    for user in conn.execute("SELECT id, domain, username, password, credtype, pillaged_from_computerid FROM users"):
        # Add user
        jackal_user = user_search.id_to_object(user[2])
        if user[1]:
            jackal_user.domain.append(user[1])
        jackal_user.add_tag("cme_import")
        jackal_user.save()
        user_count += 1

        try:
            address = host_map[user[5]]
        except KeyError:
            address = None
        # Add credential
        add_credential(user[2], user[3], user[1], address, user[4], port=445)

        for admin_host in conn.execute("SELECT computerid FROM admin_relations WHERE userid=?", (int(user[0]),)):
            admin_count += 1
            admin_pc = host_map[admin_host[0]]
            add_credential(user[2], user[3], user[1], admin_pc, user[4], port=445, access_level='Administrator')
    conn.close()

    # Log the info
    stats = {}
    stats['hosts'] = computer_count
    stats['users'] = user_count
    stats['admins'] = admin_count
    stats['file'] = database_path
    Logger().log('cme_smb', "Imported CME smb database: {}".format(database_path), stats)


def import_database(database_path):
    mapping = {'smb.db': import_smb, 'ssh.db': import_other, 'winrm.db': import_other, 'http.db': import_other, 'mssql.db': import_other}
    for value in mapping:
        if database_path.endswith(value):
            mapping[value](database_path)


def main():
    print_notification("Importing cme")
    home = expanduser('~')
    cme_workspaces_dir = join(home, '.cme', 'workspaces')
    if exists(cme_workspaces_dir):
        print_success("Found cme directory")
        workspaces = os.listdir(cme_workspaces_dir)
        for workspace in workspaces:
            workspace_path = join(cme_workspaces_dir, workspace)
            databases = os.listdir(workspace_path)
            for database in databases:
                print_notification("Importing {}".format(database))
                database_path = join(workspace_path, database)
                import_database(database_path)


if __name__ == '__main__':
    main()
