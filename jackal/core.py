import argparse
import json
import sys
from datetime import datetime
from os import isatty

from elasticsearch_dsl import (Date, DocType, InnerObjectWrapper, Integer, Ip,
                               Keyword, Object, Text)
from elasticsearch_dsl.connections import connections

from jackal.config import Config

config = Config()

connections.create_connection(hosts=[config.host], timeout=20)


class Range(DocType):
    """
        This class represents a range in elasticsearch.
        The range attribute will also be used as the id of a range.
    """
    name = Text()
    range = Text(required=True)
    tags = Keyword(multi=True)
    created_at = Date()
    updated_at = Date()

    class Meta:
        index = "{}-ranges".format(config.index)

    def save(self, ** kwargs):
        self.created_at = datetime.now()
        self.meta.id = self.range
        return super(Range, self).save(** kwargs)

    def update(self, ** kwargs):
        self.updated_at = datetime.now()
        return super(Range, self).update(** kwargs)



class Service(DocType):
    """
        This class represents a service object in elasticsearch.
    """
    address = Ip(required=True)
    port = Integer()
    state = Keyword()
    banner = Keyword()
    script_results = Keyword(multi=True)
    protocol = Keyword()
    reason = Keyword()
    service_id = Keyword()
    created_at = Date()
    updated_at = Date()
    tags = Keyword(multi=True)

    class Meta:
        index = "{}-services".format(config.index)

    def save(self, ** kwargs):
        self.created_at = datetime.now()
        return super(Service, self).save(** kwargs)

    def update(self, ** kwargs):
        self.updated_at = datetime.now()
        return super(Service, self).update(** kwargs)


class Host(DocType):
    """
        This class represents a host object in elasticsearch.
        The address attribute will be used to set the id of a host.
    """
    address = Ip(required=True)
    tags = Keyword(multi=True)
    os = Keyword()
    hostname = Keyword(multi=True)
    created_at = Date()
    updated_at = Date()
    open_ports = Integer(multi=True)
    closed_ports = Integer(multi=True)
    filtered_ports = Integer(multi=True)

    class Meta:
        index = "{}-hosts".format(config.index)


    def save(self, ** kwargs):
        self.meta.id = self.address
        self.created_at = datetime.now()
        return super(Host, self).save(** kwargs)


    def update(self, ** kwargs):
        self.updated_at = datetime.now()
        return super(Host, self).update(** kwargs)



class Core(object):
    """
        Core class that provides the default functionality of all jackal tools.abs
        The core class provides a way to:
            - Parse commonly used arguments
            - Retrieve hosts and ranges from the elasticsearch instance and filter them based on the arguments given.
            - Create host and range objects from piped input.
    """

    def __init__(self, use_pipe=True):
        self.is_pipe = not isatty(sys.stdin.fileno())
        self.arguments = self.core_parser.parse_args()
        self.use_pipe = use_pipe


    # Provides all of the given ranges as Range objects
    def get_ranges(self, save=True):
        """
            Two options, pipe input or elasticsearch input.
            Pipe input should be checked to see if its json.
            Otherwise default to database.
        """
        ranges = []
        if self.is_pipe and self.use_pipe:
            for line in sys.stdin:
                try:
                    data = json.loads(line.strip())
                    r = Range(**data)
                    r.meta.id = r.range
                    ranges.append(r)
                except ValueError:
                    ranges.append(self.ip_to_range(line.strip(), save))

        else:
            ranges = self.search_ranges()
        return ranges


    def ip_to_range(self, range_ip, save=True):
        """
            Resolves an ip adres to a range object, creating it if it doesn't exists.
        """
        result = Range.get(range_ip, ignore=404)
        if not result:
            result = Range(range=range_ip)
            if save:
                result.save()
        return result


    def ip_to_host(self, ip, save=True):
        """
            Resolves an ip adres to a host object, creating it if it doesn't exists.
        """
        host = Host.get(ip, ignore=404)
        if not host:
            host = Host(address=ip)
            if save:
                host.save()
        return host


    def get_hosts(self, save=True):
        """
            Two types of input, pipe or elasticsearch. See get_ranges
        """
        hosts = []
        # pipe input first
        if self.is_pipe and self.use_pipe:
            for line in sys.stdin:
                # Check for json
                try:
                    data = json.loads(line.strip())
                    host = Host(**data)
                    host.meta.id = host.address
                    hosts.append(host)
                except ValueError:
                    # ip data will be created if applicable
                    hosts.append(self.ip_to_host(line.strip(), save))

        else:
            # Otherwise use the search function.
            hosts = self.search_hosts()
        return hosts


    def get_services(self):
        """
            Retrieves the services.
        """
        services = []
        # pipe input first
        if self.is_pipe and self.use_pipe:
            for line in sys.stdin:
                # Check for json
                try:
                    data = json.loads(line.strip())
                    service = Service(**data)
                    services.append(service)
                except ValueError:
                    pass

        else:
            # Otherwise use the search function.
            services = self.search_services()
        return services


    @property
    def total_hosts(self):
        """
            Helper function to return the number of hosts.
        """
        return Host.search().count()

    @property
    def total_ranges(self):
        """
            Helper function to return the number of ranges.
        """
        return Range.search().count()


    @property
    def total_services(self):
        """
            Helper function to return the number of services.
        """
        return Service.search().count()


    def search_services(self):
        """
            This function will return the services in the elasticsearch instance.
        """
        services = []
        search = Service.search()
        if self.arguments.tag:
            for tag in self.arguments.tag.split(','):
                if tag[0] == '!':
                    search = search.exclude("term", tags=tag[1:])
                else:
                    search = search.filter("term", tags=tag)
        if self.arguments.up:
            search = search.filter("term", state='open')
        if self.arguments.ports:
            for port in self.arguments.ports.split(','):
                search = search.filter("match", port=port)
        if self.arguments.search:
            for search_argument in self.arguments.search.split(','):
                search = search.query("query_string", query='*{}*'.format(search_argument), analyze_wildcard=True)
        if self.arguments.range:
            search = search.filter('term', address=self.arguments.range)
        if self.arguments.number:
            response = search[0:self.arguments.number]
        elif self.arguments.count:
            return search.count()
        else:
            response = search.scan()

        # response = search.scan()
        for hit in response:
            services.append(hit)
        return services


    def search_hosts(self):
        """
            This function will perform a query on the elasticsearch instance with the given command line arguments.
            Currently tag, up, port and search arguments are implemented.
        """
        hosts = []
        search = Host.search()
        if self.arguments.tag:
            for tag in self.arguments.tag.split(','):
                if tag[0] == '!':
                    search = search.exclude("term", tags=tag[1:])
                else:
                    search = search.filter("term", tags=tag)
        if self.arguments.up:
            search = search.filter("term", tags='up')
        if self.arguments.ports:
            for port in self.arguments.ports.split(','):
                search = search.filter("match", open_ports=port)
        if self.arguments.search:
            for search_argument in self.arguments.search.split(','):
                search = search.query("query_string", query='*{}*'.format(search_argument), analyze_wildcard=True)
        if self.arguments.range:
            search = search.filter('term', address=self.arguments.range)
        if self.arguments.number:
            response = search[0:self.arguments.number]
        elif self.arguments.count:
            return search.count()
        else:
            response = search.scan()

        for hit in response:
            hosts.append(hit)

        return hosts


    def search_ranges(self):
        """
            This function will perform a query on the elasticsearch instance.
            Currently only tag search is implemented.
        """
        search = Range.search()
        if self.arguments.tag:
            for tag in self.arguments.tag.split(','):
                if tag[0] == '!':
                    search = search.exclude("term", tags=tag[1:])
                else:
                    search = search.filter("term", tags=tag)

        ranges = []
        if self.arguments.number:
            response = search[0:self.arguments.number]
        elif self.arguments.count:
            return search.count()
        else:
            response = search.scan()

        for hit in response:
            ranges.append(hit)

        return ranges


    @property
    def core_parser(self):
        core_parser = argparse.ArgumentParser(add_help=True)
        core_parser.add_argument('-r', '--range', type=str, help="The range / host to use")
        core_parser.add_argument('-v', help="Increase verbosity", action="count", default=0)
        core_parser.add_argument('-s', '--disable-save', help="Don't store the results automatically", action="store_true")
        core_parser.add_argument('-f', '--file', type=str, help="Input file to use")
        core_parser.add_argument('-S', '--search', type=str, help="Search string to use")
        core_parser.add_argument('-p', '--ports', type=str, help="Ports to include")
        core_parser.add_argument('-u', '--up', help="Only hosts / ports that are open / up", action="store_true")
        core_parser.add_argument('-t', '--tag', type=str, help="Tag(s) to search for, use (!) for not search, comma (,) to seperate tags")
        core_parser.add_argument('-c', '--count', help="Only show the number of results", action="store_true")
        core_parser.add_argument('-n', '--number', type=int, help="Limit the result list to this number", action="store")
        return core_parser


    def merge_host(self, host):
        """
            Merge the given host with the host in the elasticsearch cluster, all of the arguments are appended.
            If the host does not exist yet in elastic, it will be created.
        """
        self.merge(host, Host, 'address')


    def merge(self, new, object_type, id_value):
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
                    value.extend(new[key])
                    try:
                        update[key] = list(set(value))
                    except TypeError:
                        update[key] = value
            elastic_object.update(**update)
        else:
            new.save()
