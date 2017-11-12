"""
    Configuration of jackal
"""
from builtins import input
from os.path import expanduser
import os
import ConfigParser


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
    host = input_with_default("What is the Elasticsearch host?", 'localhost')
    index_prefix = input_with_default("What prefix should jackal use for indices?", 'jk-')
    initialize_indices = (input_with_default("Do you want to initialize the indices now?", 'n').lower() == 'y')
    config = Config()
    config.configure(host, index_prefix, initialize_indices)


class Config(object):
    """
        The class that represents the jackal configuration.
        This class will try to read the config file from the users home directory.
    """

    def __init__(self):
        self.load_config()
        self.host = 'localhost'
        self.index_prefix = 'jk-'
        self.load_config()


    def load_config(self):
        """
            Loads the configuration file.
        """
        if os.path.exists(self.config_file):
            config = ConfigParser.ConfigParser()
            config.read(self.config_file)
            self.host = config.get('jackal', 'host')
            self.index_prefix = config.get('jackal', 'index_prefix')


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
        

    def configure(self, host, index_prefix, initialize_indices):
        """
            Writes given configuration to the config file so it's used in jackal.
        """
        if not os.path.exists(self.config_dir):
            os.mkdir(self.config_dir)
        config = ConfigParser.ConfigParser()
        config.add_section('jackal')
        config.set('jackal', 'host', host)
        config.set('jackal', 'index_prefix', index_prefix)

        with open(self.config_file, 'wb') as configfile:
            config.write(configfile)

        if initialize_indices:
            from jackal.core import Host, Range
            Host.init()
            Range.init()
