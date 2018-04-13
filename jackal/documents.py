from datetime import datetime

from elasticsearch_dsl import (Date, DocType, Integer, Ip,
                               Keyword, Object, Text, Boolean, Object)
from jackal.config import Config

config = Config()


class JackalDoc(DocType):
    """
        Document type to provide some default behaviour for jackal.
    """
    tags = Keyword(multi=True)
    created_at = Date()
    updated_at = Date()


    def save(self, **kwargs):
        self.created_at = datetime.now()
        return super(JackalDoc, self).save(** kwargs)


    def add_tag(self, tag):
        """
            Adds a tag to the list of tags and makes sure the result list contains only unique results.
        """
        self.tags = list(set(self.tags or []) | set([tag]))


    def remove_tag(self, tag):
        """
            Removes a tag from this object
        """
        self.tags = list(set(self.tags or []) - set([tag]))




    def to_dict(self, include_meta=False):
        """
            Returns the result as a dictionary, provide the include_meta flag to als show information like index and doctype.
        """
        result = super(JackalDoc, self).to_dict(include_meta=include_meta)
        if include_meta:
            source = result.pop('_source')
            return {**result, **source}
        else:
            return result

    def __init__(self, ** kwargs):
        args = dict((k, v) for k, v in kwargs.items() if not k.startswith('_'))
        super(JackalDoc, self).__init__(** args)
        if '_id' in kwargs:
            self.meta.id = kwargs['_id']


class Range(JackalDoc):
    """
        This class represents a range in elasticsearch.
        The range attribute will also be used as the id of a range.
    """
    name = Text()
    range = Text(required=True)


    class Meta:
        index = "{}-ranges".format(config.get('jackal', 'index'))

    def save(self, **kwargs):
        self.meta.id = self.range
        return super(Range, self).save(** kwargs)

    def __init__(self, **kwargs):
        super(Range, self).__init__(**kwargs)
        if self.range:
            self.meta.id = self.range


class Service(JackalDoc):
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
    id = Keyword()
    service = Keyword()

    class Meta:
        index = "{}-services".format(config.get('jackal', 'index'))


class Host(JackalDoc):
    """
        This class represents a host object in elasticsearch.
        The address attribute will be used to set the id of a host.
    """
    address = Ip(required=True)
    os = Keyword()
    hostname = Keyword(multi=True)
    open_ports = Integer(multi=True)
    closed_ports = Integer(multi=True)
    filtered_ports = Integer(multi=True)
    status = Keyword()
    description = Keyword(multi=True)
    domain_controller = Boolean()

    class Meta:
        index = "{}-hosts".format(config.get('jackal', 'index'))

    def save(self, **kwargs):
        self.meta.id = self.address
        try:
            self.hostname = list(set(self.hostname))
        except TypeError:
            pass
        return super(Host, self).save(** kwargs)

    def __init__(self, ** kwargs):
        super(Host, self).__init__(**kwargs)
        if self.address:
            self.meta.id = self.address


class Credential(JackalDoc):
    """
        User passwords document
    """
    secret = Keyword(required=True)
    username = Keyword(required=True)
    plaintext = Keyword()
    cracked = Boolean()
    domain = Keyword()
    type = Keyword(required=True)
    access_level = Keyword()
    port = Integer()
    host_ip = Ip()
    description = Keyword()

    class Meta:
        index = "{}-creds".format(config.get('jackal', 'index'))


class User(JackalDoc):
    """
        User document, username will be used as id.
    """
    username = Keyword(required=True)
    tags = Keyword(multi=True)
    description = Keyword()
    name = Keyword()
    domain = Keyword(multi=True)
    flags = Keyword(multi=True)
    sid = Keyword()
    groups = Keyword(multi=True)

    class Meta:
        index = "{}-users".format(config.get('jackal', 'index'))

    def save(self, **kwargs):
        self.meta.id = self.username
        return super(User, self).save(**kwargs)

    def __init__(self, **kwargs):
        super(User, self).__init__(**kwargs)
        if self.username:
            self.meta.id = self.username

class Log(DocType):
    """
        Log entry
    """
    timestamp = Date()
    tool = Keyword()
    description = Keyword()
    stats = Object()

    def save(self, **kwargs):
        self.timestamp = datetime.now()
        return super(Log, self).save(**kwargs)

    class Meta:
        index = "{}-log".format(config.get('jackal', 'index'))
