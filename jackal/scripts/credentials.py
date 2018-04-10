from jackal import CredentialSearch, Credential
from jackal.utils import print_json, print_line

import argparse

def main():
    """
        Main credentials tool
    """
    cred_search = CredentialSearch()
    arg = argparse.ArgumentParser(parents=[cred_search.argparser], conflict_handler='resolve')
    arg.add_argument('-c', '--count', help="Only show the number of results", action="store_true")
    arguments = arg.parse_args()

    if arguments.count:
        print_line("Number of credentials: {}".format(cred_search.argument_count()))
    else:
        response = cred_search.get_credentials()
        for hit in response:
            print_json(hit.to_dict(include_meta=True))


def overview():
    """
        Provides an overview of the duplicate credentials.
    """
    search = Credential.search()
    search.aggs.bucket('password_count', 'terms', field='secret', order={'_count': 'desc'}, size=10)\
        .metric('username_count', 'cardinality', field='username') \
        .metric('top_hits', 'top_hits', docvalue_fields=['username'], size=100)
    response = search.execute()
    print_line("{0:65} {1:5} {2:5} {3}".format("Secret", "Count", "Users", "Usernames"))
    print_line("-"*100)
    for entry in response.aggregations.password_count.buckets:
        usernames = []
        for creds in entry.top_hits:
            usernames.append(creds.username[0])
        usernames = list(set(usernames))
        print_line("{0:65} {1:5} {2:5} {3}".format(entry.key, entry.doc_count, entry.username_count.value, usernames))


if __name__ == '__main__':
    overview()
