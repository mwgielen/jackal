import datetime
import json
import subprocess
import tempfile

from jackal.core import DocMapper
from jackal.utils import datetime_handler, print_error, print_success


def modify_data(data):
    """
        Creates a tempfile and starts the given editor, returns the data afterwards.
    """
    with tempfile.NamedTemporaryFile('w') as f:
        for entry in data:
            f.write(json.dumps(entry.to_dict(
                include_meta=True),
                default=datetime_handler))
            f.write('\n')
        f.flush()
        print_success("Starting editor")
        subprocess.call(['nano', '-', f.name])
        with open(f.name, 'r') as f:
            return f.readlines()


def modify_input():
    """
        This functions gives the user a way to change the data that is given as input.
    """
    doc_mapper = DocMapper()
    if doc_mapper.is_pipe:
        objects = [obj for obj in doc_mapper.get_pipe()]
        modified = modify_data(objects)
        for line in modified:
            obj = doc_mapper.line_to_object(line)
            obj.save()
        print_success("Object(s) successfully changed")
    else:
        print_error("Please use this tool with pipes")


if __name__ == '__main__':
    modify_input()
