import argparse
import json
import sys
from os import isatty

from elasticsearch_dsl.connections import connections

from jackal.config import Config
from jackal.documents import RangeDoc, HostDoc, ServiceDoc


config = Config()

connections.create_connection(hosts=[config.get('jackal', 'host')], timeout=20)


class CoreSearch(object):
    """
        Provides abstract class to implement new document manager
    """

    def __init__(self, use_pipe=True, *args, **kwargs):
        self.is_pipe = not isatty(sys.stdin.fileno())
        self.use_pipe = use_pipe


    def search(self, number=None, *args, **kwargs):
        search = self.create_search(*args, **kwargs)
        if number:
            response = search[0:number]
        else:
            response = search.scan()

        for hit in response:
            yield hit

    def argument_search(self):
        """
            Uses the command line arguments to fill the search function and call it.
        """
        arguments, unknown = self.argparser.parse_known_args()
        return self.search(**vars(arguments))


    def count(self, *args, **kwargs):
        """
            Returns the number of results after filtering with the given arguments.
        """
        search = self.create_search(*args, **kwargs)
        return search.count()


    def argument_count(self):
        """
            Uses the command line arguments to fill the count function and call it.
        """
        arguments, unknown = self.argparser.parse_known_args()
        return self.count(**vars(arguments))


    def create_search(self, *args, **kwargs):
        """
            Creates an search object from the given arguments.
        """
        raise NotImplementedError('')


    def merge(self, obj):
        """
            Function to merge the object with the object in the elasticsearch database.
        """
        raise NotImplementedError('')

    # def get(self, arguments=True, *args, **kwargs):
    #     """
    #         Retrieves the objects from either the pipe or from elasticsearch.
    #         If no pipe is available this function will call search or argument search depending on the arguments flag.
    #     """
    #     raise NotImplementedError('')

    def id_to_object(self, line):
        """
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


    @staticmethod
    def _merge(new, object_type, id_value):
        """
            Merge
            new: object to be merged.
            object_type: type of the to be merged object
            id_value: name of the value in new that is the id of the object.
        """
        elastic_object = object_type.get(getattr(new, id_value), ignore=404)
        if elastic_object:
            update = {}
            old = elastic_object.to_dict()
            new = new.to_dict()
            for key in new:
                if not key == id_value:
                    value = old.get(key, [])
                    try:
                        value.extend(new[key])
                        update[key] = list(set(value))
                    except TypeError:
                        update[key] = value
                    except AttributeError:
                        update[key] = value
            elastic_object.update(**update)
        else:
            new.save()

    @property
    def core_parser(self):
        core_parser = argparse.ArgumentParser(add_help=True)
        core_parser.add_argument('-r', '--range', type=str, help="The range / host to use")
        core_parser.add_argument('-t', '--tag', type=str, help="Tag(s) to search for, use (!) for not search, comma (,) to seperate tags", dest='tags')
        return core_parser

    @property
    def argparser(self):
        raise NotImplementedError('Argparse is not implemented')


class RangeSearch(CoreSearch):


    def __init__(self, *args, **kwargs):
        super(RangeSearch, self).__init__(*args, **kwargs)


    def merge(self, r):
        super(RangeSearch, self)._merge(r, RangeDoc, 'range')


    def create_search(self, tags='', *args, **kwargs):
        search = RangeDoc.search()
        if tags:
            for tag in tags.split(','):
                if tag[0] == '!':
                    search = search.exclude("term", tags=tag[1:])
                else:
                    search = search.filter("term", tags=tag)
        return search

    def get_ranges(self, arguments=True, *args, **kwargs):
        if self.is_pipe:
            return self.get_pipe(RangeDoc)
        elif arguments:
            return self.argument_search()
        else:
            return self.search(*args, **kwargs)

    def id_to_object(self, line):
        """
            Resolves an ip adres to a range object, creating it if it doesn't exists.
        """
        result = RangeDoc.get(line, ignore=404)
        if not result:
            result = RangeDoc(range=line)
            result.save()
        return result

    @property
    def argparser(self):
        """
            Argparser option with search functionality specific for ranges.
        """
        return self.core_parser


class HostSearch(CoreSearch):

    def __init__(self, *args, **kwargs):
        super(HostSearch, self).__init__(*args, **kwargs)


    def merge(self, obj):
        super(HostSearch, self)._merge(obj, HostDoc, 'address')


    def create_search(self, tags='', up=False, ports='', search='', *args, **kwargs):
        s = HostDoc.search()
        if tags:
            for tag in tags.split(','):
                if tag[0] == '!':
                    s = s.exclude("term", tags=tag[1:])
                else:
                    s = s.filter("term", tags=tag)
        if up:
            s = s.filter("term", tags='up')
        if ports:
            for port in ports.split(','):
                s = s.filter("match", open_ports=port)
        if search:
            for search_argument in search.split(','):
                s = s.query("query_string", query='*{}*'.format(search_argument), analyze_wildcard=True)
        if kwargs.get('range'):
            s = s.filter('term', address=kwargs.get('range'))
        return s

    def id_to_object(self, line):
        host = HostDoc.get(line, ignore=404)
        if not host:
            host = HostDoc(address=line)
            host.save()
        return host

    def get_hosts(self, arguments=True, *args, **kwargs):
        if self.is_pipe:
            return self.get_pipe(HostDoc)
        elif arguments:
            return self.argument_search()
        else:
            return self.search(*args, **kwargs)

    @property
    def argparser(self):
        """
            Argparser option with search functionality specific for hosts.
        """
        core_parser = self.core_parser
        core_parser.add_argument('-S', '--search', type=str, help="Search string to use")
        core_parser.add_argument('-p', '--ports', type=str, help="Ports to include")
        core_parser.add_argument('-u', '--up', help="Only hosts / ports that are open / up", action="store_true")
        return core_parser


class ServiceSearch(CoreSearch):

    def __init__(self, *args, **kwargs):
        super(ServiceSearch, self).__init__(*args, **kwargs)


    def merge(self, obj):
        # TODO fixme
        raise NotImplementedError('You should not try to merge services I guess')
        # super(ServiceCore, self)._merge(obj, Service, '')


    def create_search(self, tags='', up=False, ports='', search='', *args, **kwargs):
        s = ServiceDoc.search()
        if tags:
            for tag in tags.split(','):
                if tag[0] == '!':
                    s = s.exclude("term", tags=tag[1:])
                else:
                    s = s.filter("term", tags=tag)
        if up:
            s = s.filter("term", state='open')
        if ports:
            for port in ports.split(','):
                s = s.filter("match", port=port)
        if search:
            for search_argument in search.split(','):
                s = s.query("query_string", query='*{}*'.format(search_argument), analyze_wildcard=True)
        if kwargs.get('range'):
            s = s.filter('term', address=kwargs.get('range'))
        return s

    def get_services(self, arguments=True, *args, **kwargs):
        if self.is_pipe:
            return self.get_pipe(ServiceDoc)
        elif arguments:
            return self.argument_search()
        else:
            return self.search(*args, **kwargs)

    def id_to_object(self, line):
        # Dont know how to solve this yet.
        return None

    @property
    def argparser(self):
        """
            Argparser option with search functionality specific for hosts.
        """
        core_parser = self.core_parser
        core_parser.add_argument('-S', '--search', type=str, help="Search string to use")
        core_parser.add_argument('-p', '--ports', type=str, help="Ports to include")
        core_parser.add_argument('-u', '--up', help="Only hosts / ports that are open / up", action="store_true")
        return core_parser


class DocMapper(object):
    """
        Class that will convert objects from the input pipe to a corresponding doctype.
        Only works for json input type
    """

    object_mapping = {'range_doc': RangeDoc, 'host_doc': HostDoc, 'service_doc': ServiceDoc}

    def __init__(self):
        self.is_pipe = not isatty(sys.stdin.fileno())


    def get_pipe(self):
        """
            Returns a generator that maps the input of the pipe to an elasticsearch object.
            Will call id_to_object if it cannot serialize the data from json.
        """
        for line in sys.stdin:
            try:
                data = json.loads(line.strip())
                object_type = self.object_mapping[data['_type']]
                obj = object_type(**data)
                yield obj
            except ValueError:
                pass
            except KeyError:
                pass
