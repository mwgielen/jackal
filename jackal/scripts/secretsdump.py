from jackal import Credential, CredentialSearch, UserSearch
from jackal.utils import print_error, print_notification, print_success
import argparse
import re
import os

def parse_file(filename):
    cs = CredentialSearch()
    us = UserSearch()
    print_notification("Processing {}".format(filename))
    if not os.path.isfile(filename):
        print_error("Given path is not a file, skipping...")
        return

    pattern = r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}"
    result = re.findall(pattern, filename)
    ip = ''
    if len(result):
        ip = result[0]
        print_notification("Host IP seems to be {}".format(ip))
    else:
        print_error("IP could not be obtained from the filename, skipping...")
        return

    with open(filename, 'r') as f:
        data = f.readlines()

    data = [d.strip() for d in data]

    count = 0
    print_notification("Importing {} credentials".format(len(data)))
    for line in data:
        s = line.split(':')
        if len(s) == 7:
            username = s[0]

            jackal_user = us.id_to_object(username)
            jackal_user.add_tag("secretsdump_import")
            jackal_user.save()

            lm = s[2]
            nt = s[3]
            secret = lm + ":" + nt
            credential = cs.find_object(username=username, secret=secret, host_ip=ip)
            if not credential:
                credential = Credential(secret=secret, username=username, type='ntlm', host_ip=ip, port=445)

            credential.add_tag("secretsdump_import")
            credential.save()
            count += 1
        else:
            print_error("Malformed data:")
            print_error(line)

    if count > 0:
        print_success("{} credentials imported".format(count))
    else:
        print_error("No credentials imported")


def import_secretsdump():
    parser = argparse.ArgumentParser(
        description="Imports secretsdump files.")
    parser.add_argument("files", nargs='+',
                        help="The secretsdump files to import")
    arguments = parser.parse_args()
    print_notification("Importing {} files".format(len(arguments.files)))
    for f in arguments.files:
        parse_file(f)


if __name__ == '__main__':
    import_secretsdump()
