#!/usr/bin/env python3
import sys
from jackal.utils import print_line, print_error, PartialFormatter
from jackal.core import DocMapper, RangeDoc, HostDoc, ServiceDoc


fmt = PartialFormatter(missing='')

def format_input(style):
    doc_mapper = DocMapper()
    if doc_mapper.is_pipe:
        for obj in doc_mapper.get_pipe():
            print_line(fmt.format(style, **obj.to_dict(include_meta=True)))
    else:
        print_error("Please use this script with pipes")


def filter():
    if len(sys.argv) > 1:
        style = '{' + str(sys.argv[1]) + '}'
        format_input(style)
    else:
        print_error("Please provide an argument.")


def format():
    """
        Formats the output of another tool in the given way.
        Has default styles for ranges, hosts and services.
    """
    service_style = "{address:15} {port:7} {protocol:5} {service:15} {state:10} {banner} {tags}"
    host_style = "{address:15} {tags}"
    ranges_style = "{range:18} {tags}"
    if len(sys.argv) > 1:
        format_input(sys.argv[1])
    else:
        doc_mapper = DocMapper()
        if doc_mapper.is_pipe:
            for obj in doc_mapper.get_pipe():
                style = ''
                if isinstance(obj, RangeDoc):
                    style = ranges_style
                elif isinstance(obj, HostDoc):
                    style = host_style
                elif isinstance(obj, ServiceDoc):
                    style = service_style
                print_line(fmt.format(style, **obj.to_dict(include_meta=True)))
        else:
            print_error("Please use this script with pipes")
