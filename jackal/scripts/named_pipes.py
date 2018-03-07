#!/usr/bin/env python3
import configparser
import multiprocessing
import os

from jackal import HostSearch, RangeSearch, ServiceSearch, UserSearch
from jackal.config import Config
from jackal.utils import print_error, print_notification, print_success
from jackal.utils import PartialFormatter

fmt = PartialFormatter(missing='')

def pipe_worker(pipename, filename, object_type, query, format_string, unique=False):
    """
        Starts the loop to provide the data from jackal.
    """
    print_notification("[{}] Starting pipe".format(pipename))
    object_type = object_type()
    try:
        while True:
            uniq = set()
            # Remove the previous file if it exists
            if os.path.exists(filename):
                os.remove(filename)

            # Create the named pipe
            os.mkfifo(filename)
            # This function will block until a process opens it
            with open(filename, 'w') as pipe:
                print_success("[{}] Providing data".format(pipename))
                # Search the database
                objects = object_type.search(**query)
                for obj in objects:
                    data = fmt.format(format_string, **obj.to_dict())
                    if unique:
                        if not data in uniq:
                            uniq.add(data)
                            pipe.write(data + '\n')
                    else:
                        pipe.write(data + '\n')
            os.unlink(filename)
    except KeyboardInterrupt:
        print_notification("[{}] Shutting down named pipe".format(pipename))
    except Exception as e:
        print_error("[{}] Error: {}, stopping named pipe".format(e, pipename))
    finally:
        os.remove(filename)


def create_query(section):
    """
        Creates a search query based on the section of the config file.
    """
    query = {}

    if 'ports' in section:
        query['ports'] = [section['ports']]
    if 'up' in section:
        query['up'] = bool(section['up'])
    if 'search' in section:
        query['search'] = [section['search']]
    if 'tags' in section:
        query['tags'] = [section['tags']]
    if 'groups' in section:
        query['groups'] = [section['groups']]

    return query


def create_pipe_workers(configfile, directory):
    """
        Creates the workers based on the given configfile to provide named pipes in the directory.
    """
    type_map = {'service': ServiceSearch,
                'host': HostSearch, 'range': RangeSearch,
                'user': UserSearch}
    config = configparser.ConfigParser()
    config.read(configfile)

    if not len(config.sections()):
        print_error("No named pipes configured")
        return

    print_notification("Starting {} pipes in directory {}".format(
        len(config.sections()), directory))

    workers = []
    for name in config.sections():
        section = config[name]
        query = create_query(section)
        object_type = type_map[section['type']]
        args = (name, os.path.join(directory, name), object_type, query,
                section['format'], bool(section.get('unique', 0)))
        workers.append(multiprocessing.Process(target=pipe_worker, args=args))

    return workers


def main():
    """
        Loads the config and handles the workers.
    """
    config = Config()
    pipes_dir = config.get('pipes', 'directory')
    pipes_config = config.get('pipes', 'config_file')
    pipes_config_path = os.path.join(config.config_dir, pipes_config)
    if not os.path.exists(pipes_config_path):
        print_error("Please configure the named pipes first")
        return

    workers = create_pipe_workers(pipes_config_path, pipes_dir)
    if workers:
        for worker in workers:
            worker.start()

        try:
            for worker in workers:
                worker.join()
        except KeyboardInterrupt:
            print_notification("Shutting down")
            for worker in workers:
                worker.terminate()
                worker.join()



if __name__ == '__main__':
    main()
