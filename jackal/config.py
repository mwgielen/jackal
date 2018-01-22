"""
    Configuration of jackal
"""
from builtins import input
from os.path import expanduser
import os
try:
    import configparser
except ImportError:
    import ConfigParser as configparser


def input_with_default(question, default):
    """
        Helper function to return default value if string is empty.
    """
    return input(question + ' [{}] '.format(default)) or default

def required_input(question):
    while True:
        result = input(question)
        if result:
            return result
        print("This option is required")


def manual_configure():
    """
        Function to manually configure jackal.
    """
    print("Manual configuring jackal")
    config = Config()
    host = input_with_default("What is the Elasticsearch host?", config.get('jackal', 'host'))
    config.set('jackal', 'host', host)
    index = input_with_default("What index prefix should jackal use?", config.get('jackal', 'index'))
    config.set('jackal', 'index', index)
    initialize_indices = (input_with_default("Do you want to initialize the indices?", 'n').lower() == 'y')

    nmap_options = input_with_default("What nmap options do you want to set for 'custom' (for example '-p 22,445')?", config.get('nmap', 'options'))
    config.set('nmap', 'options', nmap_options)

    configure_nessus = (input_with_default("Do you want to setup nessus?", 'n').lower() == 'y')
    if configure_nessus:
        nessus_host = input_with_default("What is the nessus host?", config.get('nessus', 'host'))
        nessus_template = input_with_default("What template should jackal use?", config.get('nessus', 'template_name'))
        nessus_access = input_with_default("What api access key should jackal use?", config.get('nessus', 'access_key'))
        nessus_secret = input_with_default("What api secret key should jackal use?", config.get('nessus', 'secret_key'))
        config.set('nessus', 'host', nessus_host)
        config.set('nessus', 'template_name', nessus_template)
        config.set('nessus', 'access_key', nessus_access)
        config.set('nessus', 'secret_key', nessus_secret)

    configure_pipes = (input_with_default("Do you want to setup named pipes?", 'n').lower() == 'y')
    if configure_pipes:
        directory = input_with_default("What directory do you want to place the named pipes in?", config.get('pipes', 'directory'))
        config.set('pipes', 'directory', directory)
        config_file = input_with_default("What is the name of the named pipe config?", config.get('pipes', 'config_file'))
        config.set('pipes', 'config_file', config_file)
        if not os.path.exists(directory):
            create = (input_with_default("Do you want to create the directory?", 'n').lower() == 'y')
            if create:
                os.makedirs(directory)
        if not os.path.exists(os.path.join(config.config_dir, config_file)):
            f = open(os.path.join(config.config_dir, config_file), 'a')
            f.close()

    config.write_config(initialize_indices)


def add_named_pipe():
    """
    """
    config = Config()
    pipes_config = config.get('pipes', 'config_file')
    pipes_config_path = os.path.join(config.config_dir, pipes_config)
    if not os.path.exists(pipes_config_path):
        print("First configure named pipes with jk-configure")
        return

    name = required_input("What is the name of the named pipe? ")
    object_type = input_with_default("What is the type of the named pipe? Pick from: [host, range, service]", 'service')
    ports = input_with_default("What ports do you want to filter on? Empty for disable", '')
    tags = input_with_default("What tags do you want to filter on? Empty for disable", '')
    search = input_with_default("What search query do you want to use?", '')
    up = (input_with_default("Do you want to include only up hosts/services?", 'n').lower() == 'y')
    unique = (input_with_default("Do you want to only show unique results?", 'n').lower() == 'y')
    output_format = input_with_default("How do you want the results to be formatted?", '{address}')

    print("Adding new named pipe")
    pipes_config = configparser.ConfigParser()
    pipes_config.read(pipes_config_path)

    pipes_config[name] = {}
    pipes_config[name]['type'] = object_type
    if ports:
        pipes_config[name]['ports'] = ports
    if search:
        pipes_config[name]['search'] = search
    if tags:
        pipes_config[name]['tags'] = tags
    if up:
        pipes_config[name]['up'] = '1'
    if unique:
        pipes_config[name]['unique'] = '1'

    pipes_config[name]['format'] = output_format
    with open(pipes_config_path, 'w') as f:
        pipes_config.write(f)


class Config(object):
    """
        The class that represents the jackal configuration.
        This class will try to read the config file from the users home directory.
    """
    defaults = {
        'jackal':
            {
                'host': 'localhost',
                'index': 'jackal'
            },
        'nessus':
            {
                'host': 'https://localhost:8834',
                'template_name': 'advanced',
                'access_key': '',
                'secret_key': '',
            },
        'pipes':
            {
                'directory': os.getcwd(),
                'config_file': 'pipes.ini'
            },
        'nmap':
            {
                'options': '',
            }
        }

    def __init__(self):
        self.config = configparser.ConfigParser()
        if os.path.exists(self.config_file):
            self.config.read(self.config_file)
        else:
            self.config.read_dict(self.defaults)

    def set(self, section, key, value):
        """
            Creates the section value if it does not exists and sets the value.
            Use write_config to actually set the value.
        """
        if not section in self.config:
            self.config.add_section(section)
        self.config.set(section, key, value)


    def get(self, section, key):
        """
            This function tries to retrieve the value from the configfile
            otherwise will return a default.
        """
        try:
            return self.config.get(section, key)
        except configparser.NoSectionError:
            pass
        except configparser.NoOptionError:
            pass
        return self.defaults[section][key]

    @property
    def config_file(self):
        """
            Returns the configuration file name
        """
        config_file = os.path.join(self.config_dir, 'config.ini')
        return config_file

    @property
    def config_dir(self):
        """
            Returns the configuration directory
        """
        home = expanduser('~')
        config_dir = os.path.join(home, '.jackal')
        return config_dir

    def write_config(self, initialize_indices=False):
        """
            Write the current config to disk to store them.
        """
        if not os.path.exists(self.config_dir):
            os.mkdir(self.config_dir)

        with open(self.config_file, 'w') as configfile:
            self.config.write(configfile)

        if initialize_indices:
            index = self.get('jackal', 'index')
            from jackal import HostDoc, RangeDoc, ServiceDoc
            HostDoc.init(index="{}-hosts".format(index))
            RangeDoc.init(index="{}-ranges".format(index))
            ServiceDoc.init(index="{}-services".format(index))
