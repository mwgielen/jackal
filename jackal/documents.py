from datetime import datetime

from elasticsearch_dsl import (Date, DocType, InnerObjectWrapper, Integer, Ip,
                               Keyword, Object, Text)
from jackal.config import Config

config = Config()


class RangeDoc(DocType):
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
        return super(RangeDoc, self).save(** kwargs)

    def update(self, ** kwargs):
        self.updated_at = datetime.now()
        return super(RangeDoc, self).update(** kwargs)

    def __init__(self, **kwargs):
        args = dict((k, v) for k, v in kwargs.items() if not k.startswith('_'))
        super(RangeDoc, self).__init__(** args)
        self.meta.id = kwargs.get('range', '')

    def add_tag(self, tag):
        self.tags = list(set(self.tags or []) | set([tag]))

    def to_dict(self, include_meta=False):
        result = super(RangeDoc, self).to_dict(include_meta=include_meta)
        if include_meta:
            source = result.pop('_source')
            return {**result, **source}
        else:
            return result


class ServiceDoc(DocType):
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
        index = "{}-services".format(config.get('jackal', 'index'))

    def save(self, ** kwargs):
        self.created_at = datetime.now()
        return super(ServiceDoc, self).save(** kwargs)

    def update(self, ** kwargs):
        self.updated_at = datetime.now()
        return super(ServiceDoc, self).update(** kwargs)

    def add_tag(self, tag):
        self.tags = list(set(self.tags or []) | set([tag]))

    def to_dict(self, include_meta=False):
        result = super(ServiceDoc, self).to_dict(include_meta=include_meta)
        if include_meta:
            source = result.pop('_source')
            return {**result, **source}
        else:
            return result

    def __init__(self, ** kwargs):
        args = dict((k, v) for k, v in kwargs.items() if not k.startswith('_'))
        super(ServiceDoc, self).__init__(** args)
        if '_id' in kwargs:
            self.meta.id = kwargs['_id']


class HostDoc(DocType):
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
        index = "{}-hosts".format(config.get('jackal', 'index'))

    def save(self, ** kwargs):
        self.meta.id = self.address
        self.created_at = datetime.now()
        return super(HostDoc, self).save(** kwargs)

    def update(self, ** kwargs):
        self.updated_at = datetime.now()
        return super(HostDoc, self).update(** kwargs)

    def __init__(self, ** kwargs):
        args = dict((k, v) for k, v in kwargs.items() if not k.startswith('_'))
        super(HostDoc, self).__init__(** args)
        self.meta.id = self.address

    def add_tag(self, tag):
        self.tags = list(set(self.tags or []) | set([tag]))

    def to_dict(self, include_meta=False):
        result = super(HostDoc, self).to_dict(include_meta=include_meta)
        if include_meta:
            source = result.pop('_source')
            return {**result, **source}
        else:
            return result
