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

    config.write_config(initialize_indices)


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
