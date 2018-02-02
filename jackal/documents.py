from datetime import datetime

from elasticsearch_dsl import (Date, DocType, Integer, Ip,
                               Keyword, Object, Text, Boolean)
from jackal.config import Config

config = Config()


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
        index = "{}-ranges".format(config.get('jackal', 'index'))

    def save(self, ** kwargs):
        self.created_at = datetime.now()
        self.meta.id = self.range
        return super(Range, self).save(** kwargs)

    def update(self, ** kwargs):
        self.updated_at = datetime.now()
        return super(Range, self).update(** kwargs)

    def __init__(self, **kwargs):
        args = dict((k, v) for k, v in kwargs.items() if not k.startswith('_'))
        super(Range, self).__init__(** args)
        self.meta.id = kwargs.get('range', '')

    def add_tag(self, tag):
        self.tags = list(set(self.tags or []) | set([tag]))

    def remove_tag(self, tag):
        self.tags = list(set(self.tags or []) - set([tag]))

    def to_dict(self, include_meta=False):
        result = super(Range, self).to_dict(include_meta=include_meta)
        if include_meta:
            source = result.pop('_source')
            return {**result, **source}
        else:
            return result


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
    id = Keyword()
    service = Keyword()
    tags = Keyword(multi=True)

    class Meta:
        index = "{}-services".format(config.get('jackal', 'index'))

    def save(self, ** kwargs):
        self.created_at = datetime.now()
        return super(Service, self).save(** kwargs)

    def update(self, ** kwargs):
        self.updated_at = datetime.now()
        return super(Service, self).update(** kwargs)

    def add_tag(self, tag):
        self.tags = list(set(self.tags or []) | set([tag]))

    def remove_tag(self, tag):
        self.tags = list(set(self.tags or []) - set([tag]))

    def to_dict(self, include_meta=False):
        result = super(Service, self).to_dict(include_meta=include_meta)
        if include_meta:
            source = result.pop('_source')
            return {**result, **source}
        else:
            return result

    def __init__(self, ** kwargs):
        args = dict((k, v) for k, v in kwargs.items() if not k.startswith('_'))
        super(Service, self).__init__(** args)
        if '_id' in kwargs:
            self.meta.id = kwargs['_id']


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
    status = Keyword()
    description = Keyword(multi=True)
    domain_controller = Boolean()

    class Meta:
        index = "{}-hosts".format(config.get('jackal', 'index'))

    def save(self, ** kwargs):
        self.meta.id = self.address
        self.created_at = datetime.now()
        return super(Host, self).save(** kwargs)

    def update(self, ** kwargs):
        self.updated_at = datetime.now()
        return super(Host, self).update(** kwargs)

    def __init__(self, ** kwargs):
        args = dict((k, v) for k, v in kwargs.items() if not k.startswith('_'))
        super(Host, self).__init__(** args)
        self.meta.id = self.address

    def add_tag(self, tag):
        self.tags = list(set(self.tags or []) | set([tag]))

    def remove_tag(self, tag):
        self.tags = list(set(self.tags or []) - set([tag]))

    def to_dict(self, include_meta=False):
        result = super(Host, self).to_dict(include_meta=include_meta)
        if include_meta:
            source = result.pop('_source')
            return {**result, **source}
        else:
            return result

class User(DocType):
    """
    """
    username = Keyword(required=True)
    tags = Keyword(multi=True)
    description = Keyword()
    name = Keyword()
    domain = Keyword(multi=True)
    flags = Keyword(multi=True)
    sid = Keyword()
    groups = Keyword(multi=True)
    created_at = Date()
    updated_at = Date()

    class Meta:
        index = "{}-users".format(config.get('jackal', 'index'))

    def save(self, ** kwargs):
        self.meta.id = self.username
        self.created_at = datetime.now()
        return super(User, self).save(** kwargs)

    def update(self, ** kwargs):
        self.updated_at = datetime.now()
        return super(User, self).update(** kwargs)

    def __init__(self, ** kwargs):
        args = dict((k, v) for k, v in kwargs.items() if not k.startswith('_'))
        super(User, self).__init__(** args)
        self.meta.id = self.username

    def add_tag(self, tag):
        self.tags = list(set(self.tags or []) | set([tag]))

    def remove_tag(self, tag):
        self.tags = list(set(self.tags or []) - set([tag]))

    def to_dict(self, include_meta=False):
        result = super(User, self).to_dict(include_meta=include_meta)
        if include_meta:
            source = result.pop('_source')
            return {**result, **source}
        else:
            return result