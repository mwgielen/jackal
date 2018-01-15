#!/usr/bin/env python3
import sys

from jackal.core import DocMapper
from jackal.utils import print_error, print_success


def add_tag():
    """
        Obtains the data from the pipe and appends the given tag.
    """
    if len(sys.argv) > 1:
        tag = sys.argv[1]
        doc_mapper = DocMapper()
        if doc_mapper.is_pipe:
            count = 0
            for obj in doc_mapper.get_pipe():
                obj.add_tag(tag)
                obj.update(tags=obj.tags)
                count += 1
            print_success("Added tag '{}' to {} object(s)".format(tag, count))
        else:
            print_error("Please use this script with pipes")
    else:
        print_error("Usage: jk-add-tag <tag>")
        sys.exit()

def remove_tag():
    """
        Obtains the data from the pipe and removes the given tag.
    """
    if len(sys.argv) > 1:
        tag = sys.argv[1]
        doc_mapper = DocMapper()
        if doc_mapper.is_pipe:
            count = 0
            for obj in doc_mapper.get_pipe():
                obj.remove_tag(tag)
                obj.update(tags=obj.tags)
                count += 1
            print_success("Removed tag '{}' from {} object(s)".format(tag, count))
        else:
            print_error("Please use this script with pipes")
    else:
        print_error("Usage: jk-remove-tag <tag>")
        sys.exit()


if __name__ == '__main__':
    add_tag()
