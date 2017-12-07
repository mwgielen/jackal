from elasticsearch_dsl import (Date, DocType, InnerObjectWrapper, Integer, Ip,
                               Keyword, Object, Text)
from jackal.config import Config
from datetime import datetime

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
        index = "{}-ranges".format(config.index)

    def save(self, ** kwargs):
        self.created_at = datetime.now()
        self.meta.id = self.range
        return super(Range, self).save(** kwargs)

    def update(self, ** kwargs):
        self.updated_at = datetime.now()
        return super(Range, self).update(** kwargs)

    def __init__(self, **kwargs):
        super(Range, self).__init__(** kwargs)
        self.meta.id = kwargs.get('range', '')


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

    def __init__(self, ** kwargs):
        super(Host, self).__init__(** kwargs)
        self.meta.id = self.address
