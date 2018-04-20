import argparse
import json
import logging
import sys
from os import isatty

import urllib3
from elasticsearch import NotFoundError, ConnectionError, TransportError
from elasticsearch_dsl.connections import connections
from jackal.config import Config
from jackal.documents import Host, Range, Service, User, Credential, JackalDoc, Log
from jackal.utils import print_error

# Disable warnings for now.
urllib3.disable_warnings()

# Disable logging
logging.getLogger("urllib3").setLevel(logging.CRITICAL)
logging.getLogger("elasticsearch").setLevel(logging.CRITICAL)

def create_connection(conf):
    """
        Creates a connection based upon the given configuration object.
    """
    host_config = {}
    host_config['hosts'] = [conf.get('jackal', 'host')]
    if int(conf.get('jackal', 'use_ssl')):
        host_config['use_ssl'] = True
    if conf.get('jackal', 'ca_certs'):
        host_config['ca_certs'] = conf.get('jackal', 'ca_certs')
    if int(conf.get('jackal', 'client_certs')):
        host_config['client_cert'] = conf.get('jackal', 'client_cert')
        host_config['client_key'] = conf.get('jackal', 'client_key')

    # Disable hostname checking for now.
    host_config['ssl_assert_hostname'] = False

    connections.create_connection(**host_config)

config = Config()

create_connection(config)

class CoreSearch(object):
    """
        Provides abstract class to implement new document manager
    """

    def __init__(self, use_pipe=True, *args, **kwargs):
        self.is_pipe = not isatty(sys.stdin.fileno())
        self.use_pipe = use_pipe
        self.object_type = JackalDoc


    def search(self, number=None, *args, **kwargs):
        """
            Searches the elasticsearch instance to retrieve the requested documents.
        """
        search = self.create_search(*args, **kwargs)
        try:
            if number:
                response = search[0:number]
            else:
                args, _ = self.core_parser.parse_known_args()
                if args.number:
                    response = search[0:args.number]
                else:
                    response = search.scan()

            return [hit for hit in response]
        except NotFoundError:
            print_error("The index was not found, have you initialized the index?")
            return []
        except (ConnectionError, TransportError):
            print_error("Cannot connect to elasticsearch")
            return []


    def argument_search(self):
        """
            Uses the command line arguments to fill the search function and call it.
        """
        arguments, _ = self.argparser.parse_known_args()
        return self.search(**vars(arguments))


    def count(self, *args, **kwargs):
        """
            Returns the number of results after filtering with the given arguments.
        """
        search = self.create_search(*args, **kwargs)
        try:
            return search.count()
        except NotFoundError:
            print_error("The index was not found, have you initialized the index?")
        except (ConnectionError, TransportError):
            print_error("Cannot connect to elasticsearch")


    def argument_count(self):
        """
            Uses the command line arguments to fill the count function and call it.
        """
        arguments, _ = self.argparser.parse_known_args()
        return self.count(**vars(arguments))


    def create_search(self, *args, **kwargs):
        """
            Creates an search object from the given arguments.
        """
        raise NotImplementedError('')


    def id_to_object(self, line):
        """
            From an id return a valid object.
        """
        raise NotImplementedError('')


    def object_to_id(self, obj):
        """
            From the object, return the id.
        """
        raise NotImplementedError('')


    def get_pipe(self, object_type):
        """
            Returns a generator that maps the input of the pipe to an elasticsearch object.
            Will call id_to_object if it cannot serialize the data from json.
        """
        for line in sys.stdin:
            try:
                data = json.loads(line.strip())
                obj = object_type(**data)
                yield obj
            except ValueError:
                yield self.id_to_object(line.strip())


    @property
    def core_parser(self):
        core_parser = argparse.ArgumentParser(add_help=True)
        core_parser.add_argument('-t', '--tag', type=str, help="Tag(s) to search for, use (!) for not search", dest='tags', nargs='+', default=[])
        core_parser.add_argument('-n', '--number', type=int, help="Limit the results to this number", default=None)
        return core_parser

    @property
    def argparser(self):
        raise NotImplementedError('Argparse is not implemented')


class RangeSearch(CoreSearch):


    def __init__(self, *args, **kwargs):
        super(RangeSearch, self).__init__(*args, **kwargs)
        self.object_type = Range


    def create_search(self, tags=[], *args, **kwargs):
        search = Range.search()
        for tag in tags:
            if tag[0] == '!':
                search = search.exclude("term", tags=tag[1:])
            else:
                search = search.filter("term", tags=tag)

        # TODO implement range filter.
        return search

    def get_ranges(self, *args, **kwargs):
        arguments, _ = self.argparser.parse_known_args()
        if self.is_pipe and self.use_pipe:
            return self.get_pipe(Range)
        elif arguments.range or arguments.tags:
            return self.argument_search()
        else:
            return self.search(*args, **kwargs)

    def id_to_object(self, line):
        """
            Resolves an ip adres to a range object, creating it if it doesn't exists.
        """
        result = Range.get(line, ignore=404)
        if not result:
            result = Range(range=line)
            result.save()
        return result

    def object_to_id(self, obj):
        """
            Returns the 'range' value of the given object if it exists, else returns None
        """
        try:
            return obj.range
        except AttributeError:
            return None

    @property
    def argparser(self):
        """
            Argparser option with search functionality specific for ranges.
        """
        core_parser = self.core_parser
        core_parser.add_argument('-r', '--range', type=str, help="The range to search for use")
        return core_parser


class HostSearch(CoreSearch):

    def __init__(self, *args, **kwargs):
        super(HostSearch, self).__init__(*args, **kwargs)
        self.object_type = Host


    def create_search(self, tags=[], up=False, ports=[], search=[], domain='', *args, **kwargs):
        s = Host.search()
        for tag in tags:
            if tag[0] == '!':
                s = s.exclude("term", tags=tag[1:])
            else:
                s = s.filter("term", tags=tag)
        if up:
            s = s.filter("term", status='up')
        for port in ports:
            s = s.filter("match", open_ports=port)
        for search_argument in search:
            s = s.query("query_string", query='*{}*'.format(search_argument), analyze_wildcard=True)
        if kwargs.get('range'):
            s = s.filter('term', address=kwargs.get('range'))
        if domain:
            s = s.query('query_string', query="hostname: *.{}".format(domain), analyze_wildcard=True)

        return s

    def id_to_object(self, line):
        host = Host.get(line, ignore=404)
        if not host:
            host = Host(address=line)
            host.save()
        return host

    def object_to_id(self, obj):
        """
            Returns the 'Address' value of the given object if it exists, else returns None
        """
        try:
            return obj.address
        except AttributeError:
            return None

    def get_hosts(self, *args, **kwargs):
        arguments, _ = self.argparser.parse_known_args()
        if self.is_pipe and self.use_pipe:
            return self.get_pipe(Host)
        elif arguments.range or arguments.tags or arguments.search or arguments.ports or arguments.up or arguments.domain:
            return self.argument_search()
        else:
            return self.search(*args, **kwargs)

    @property
    def argparser(self):
        """
            Argparser option with search functionality specific for hosts.
        """
        core_parser = self.core_parser
        core_parser.add_argument('-s', '--search', type=str, help="Search string to use", nargs="+", default=[])
        core_parser.add_argument('-p', '--ports', type=str, help="Ports to include", nargs="+", default=[])
        core_parser.add_argument('-u', '--up', help="Only include hosts that are up", action="store_true")
        core_parser.add_argument('-r', '--range', type=str, help="The CIDR range to include hosts from")
        core_parser.add_argument('-d', '--domain', type=str, help="The domain to filter on")
        return core_parser


class ServiceSearch(CoreSearch):

    def __init__(self, *args, **kwargs):
        super(ServiceSearch, self).__init__(*args, **kwargs)
        self.object_type = Service


    def create_search(self, tags=[], up=False, ports=[], search=[], *args, **kwargs):
        s = Service.search()
        for tag in tags:
            if tag[0] == '!':
                s = s.exclude("term", tags=tag[1:])
            else:
                s = s.filter("term", tags=tag)
        if up:
            s = s.filter("term", state='open')
        for port in ports:
            s = s.filter("match", port=port)
        for search_argument in search:
            s = s.query("query_string", query='*{}*'.format(search_argument), analyze_wildcard=True)
        if kwargs.get('range'):
            s = s.filter('term', address=kwargs.get('range'))
        return s

    def get_services(self, *args, **kwargs):
        arguments, _ = self.argparser.parse_known_args()
        if self.is_pipe and self.use_pipe:
            return self.get_pipe(Service)
        elif arguments.range or arguments.tags or arguments.search or arguments.ports or arguments.up:
            return self.argument_search()
        else:
            return self.search(*args, **kwargs)

    def id_to_object(self, line):
        # Dont know how to solve this yet.
        return None


    def find_object(self, address, port, protocol='tcp', state=None):
        """
        """
        search = Service.search()
        search = search.filter("term", address=address)
        if protocol:
            search = search.filter("term", protocol=protocol)
        search = search.filter("term", port=port)
        if state:
            search = search.filter("term", state=state)
        if search.count():
            result = search[0].execute()[0]
            return result
        else:
            return None


    def object_to_id(self, obj):
        """
            Searches elasticsearch for objects with the same address, protocol, port and state.
        """
        search = Service.search()
        search = search.filter("term", address=obj.address)
        search = search.filter("term", protocol=obj.protocol)
        search = search.filter("term", port=obj.port)
        search = search.filter("term", state=obj.state)
        if search.count():
            result = search[0].execute()[0]
            return result.meta.id
        else:
            return None

    @property
    def argparser(self):
        """
            Argparser option with search functionality specific for hosts.
        """
        core_parser = self.core_parser
        core_parser.add_argument('-s', '--search', type=str, help="Search string to use", nargs="+", default=[])
        core_parser.add_argument('-p', '--ports', type=str, help="Ports to include", nargs="+", default=[])
        core_parser.add_argument('-u', '--up', help="Only ports that are open", action="store_true")
        core_parser.add_argument('-r', '--range', type=str, help="The range / host to use")
        return core_parser


class UserSearch(CoreSearch):
    """
        Class to provide search functionality for users.
        Two search attributes are implemented:
            - Search
            - Group
    """

    def __init__(self, *args, **kwargs):
        super(UserSearch, self).__init__(*args, **kwargs)
        self.object_type = User


    def create_search(self, group='', tags=[], search=[], domain='', *args, **kwargs):
        """
        """
        user_search = User.search()
        for tag in tags:
            if tag[0] == '!':
                user_search = user_search.exclude("term", tags=tag[1:])
            else:
                user_search = user_search.filter("term", tags=tag)
        if group:
            user_search = user_search.filter("term", groups=group)
        if domain:
            user_search = user_search.filter("term", domain=domain)
        for search_argument in search:
            user_search = user_search.query("query_string", query='*{}*'.format(search_argument), analyze_wildcard=True)
        return user_search


    def id_to_object(self, line):
        """
            Resolves the given id to a user object, if it doesn't exists it will be created.
        """
        user = User.get(line, ignore=404)
        if not user:
            user = User(username=line)
            user.save()
        return user


    def object_to_id(self, obj):
        """
            Returns the 'username' value of the given object if it exists, else returns None
        """
        try:
            return obj.username
        except AttributeError:
            return None

    def get_users(self, *args, **kwargs):
        """
            Retrieves the users from elastic.
        """
        arguments, _ = self.argparser.parse_known_args()
        if self.is_pipe and self.use_pipe:
            return self.get_pipe(self.object_type)
        elif arguments.tags or arguments.group or arguments.search or arguments.domain:
            return self.argument_search()
        else:
            return self.search(*args, **kwargs)

    @property
    def argparser(self):
        core_parser = self.core_parser
        core_parser.add_argument('-s', '--search', type=str, help="Search string to use", nargs='+', default=[])
        core_parser.add_argument('-g', '--group', type=str, help="Group to include", default='')
        core_parser.add_argument('-d', '--domain', type=str, help="Domain to include", default='')
        return core_parser


class CredentialSearch(CoreSearch):
    """
        Class to provide search functionality for credentials.
        Two search attributes are implemented:
            - Search
            - Type
    """

    def __init__(self, *args, **kwargs):
        super(CredentialSearch, self).__init__(*args, **kwargs)
        self.object_type = Credential


    def create_search(self, group='', tags=[], search=[], password='', cracked=False, type='', domain='', *args, **kwargs):
        """
        """
        # print(password)
        s = Credential.search()
        for tag in tags:
            if tag[0] == '!':
                s = s.exclude("term", tags=tag[1:])
            else:
                s = s.filter("term", tags=tag)
        if group:
            s = s.filter("term", groups=group)
        if type:
            s = s.filter("term", type=type)
        if password:
            s = s.filter("term", secret=password)
        if cracked:
            s = s.filter("term", cracked=True)
        if kwargs.get('range', ''):
            s = s.filter("term", host_ip=kwargs.get('range'))
        if domain:
            s = s.filter("term", domain=domain)
        for search_argument in search:
            s = s.query("query_string", query='*{}*'.format(search_argument), analyze_wildcard=True)
        return s



    def id_to_object(self, line):
        """
            Resolves the given id to a credential object, if it doesn't exists it will be created.
        """
        cred = Credential.get(line)
        return cred


    def find_object(self, username, secret, domain=None, host_ip=None, service_id=None):
        """
            Searches elasticsearch for objects with the same username, password, optional domain, host_ip and service_id.
        """
        # Not sure yet if this is advisable... Older passwords can be overwritten...
        search = Credential.search()
        search = search.filter("term", username=username)
        search = search.filter("term", secret=secret)
        if domain:
            search = search.filter("term", domain=domain)
        else:
            search = search.exclude("exists", field="domain")
        if host_ip:
            search = search.filter("term", host_ip=host_ip)
        else:
            search = search.exclude("exists", field="host_ip")
        if service_id:
            search = search.filter("term", service_id=service_id)
        else:
            search = search.exclude("exists", field="service_id")
        if search.count():
            result = search[0].execute()[0]
            return result
        else:
            return None


    def object_to_id(self, obj):
        """
            Searches elasticsearch for objects with the same username, password, optional domain, host_ip and service_id.
        """
        # Not sure yet if this is advisable... Older passwords can be overwritten...
        search = Credential.search()
        search = search.filter("term", username=obj.username)
        search = search.filter("term", secret=obj.secret)
        if obj.domain:
            search = search.filter("term", domain=obj.domain)
        else:
            search = search.exclude("exists", field="domain")
        if obj.host_ip:
            search = search.filter("term", host_ip=obj.host_ip)
        else:
            search = search.exclude("exists", field="host_ip")
        if obj.service_id:
            search = search.filter("term", service_id=obj.service_id)
        else:
            search = search.exclude("exists", field="service_id")
        if search.count():
            result = search[0].execute()[0]
            return result.meta.id
        else:
            return None


    def get_credentials(self, *args, **kwargs):
        """
            Retrieves the users from elastic.
        """
        arguments, _ = self.argparser.parse_known_args()
        if self.is_pipe and self.use_pipe:
            return self.get_pipe(self.object_type)
        elif arguments.tags or arguments.type or arguments.search or arguments.password or arguments.cracked or arguments.range or arguments.domain:
            return self.argument_search()
        else:
            return self.search(*args, **kwargs)

    @property
    def argparser(self):
        core_parser = self.core_parser
        core_parser.add_argument('-s', '--search', type=str, help="Search string to use", nargs='+', default=[])
        core_parser.add_argument('--type', type=str, help="Type of credentials to include")
        core_parser.add_argument('-p', '--password', type=str, help="Password to search for")
        core_parser.add_argument('--cracked', help="Only include hashes / passwords that were cracked", action="store_true")
        core_parser.add_argument('-r', '--range', type=str, help="Range/IP to find results")
        core_parser.add_argument('-d', '--domain', type=str, help="Domain to include")
        return core_parser


class Logger(CoreSearch):
    """
    """
    def __init__(self, *args, **kwargs):
        super(Logger, self).__init__(*args, **kwargs)
        self.object_type = Log
        self.use_pipe = False


    def log(self, tool='', description='', stats={}):
        entry = Log(tool=tool, description=description, stats=stats)
        entry.save()


    def create_search(self, *args, **kwargs):
        return Log.search()


class DocMapper(object):
    """
        Class that will convert objects from the input pipe to a corresponding doctype.
        Only works for json input type
    """

    object_mapping = {'ranges': Range, 'hosts': Host, 'services': Service, 'users': User , 'creds': Credential}

    def __init__(self):
        self.is_pipe = not isatty(sys.stdin.fileno())

    def line_to_object(self, line):
        data = json.loads(line.strip())
        index_name = data['_index']
        object_type = self.object_mapping[index_name.split('-')[-1]]
        obj = object_type(**data)
        return obj

    def get_pipe(self):
        """
            Returns a list that maps the input of the pipe to an elasticsearch object.
            Will call id_to_object if it cannot serialize the data from json.
        """
        lines = []
        for line in sys.stdin:
            try:
                lines.append(self.line_to_object(line.strip()))
            except ValueError:
                pass
            except KeyError:
                pass
        return lines
