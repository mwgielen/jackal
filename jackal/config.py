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
    host = input_with_default("What is the Elasticsearch host?", config.host)
    index = input_with_default("What index prefix should jackal use?", config.index)
    initialize_indices = (input_with_default("Do you want to initialize the indices now?", 'n').lower() == 'y')
    config.configure(host, index, initialize_indices)


class Config(object):
    """
        The class that represents the jackal configuration.
        This class will try to read the config file from the users home directory.
    """

    def __init__(self):
        self.host = 'localhost'
        self.index = 'jackal'
        self.load_config()


    def load_config(self):
        """
            Loads the configuration file.
        """
        if os.path.exists(self.config_file):
            try:
                config = configparser.ConfigParser()
                config.read(self.config_file)
                self.host = config.get('jackal', 'host')
                self.index = config.get('jackal', 'index')
            except configparser.NoSectionError:
                pass


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
        

    def configure(self, host, index, initialize_indices):
        """
            Writes given configuration to the config file so it's used in jackal.
        """
        if not os.path.exists(self.config_dir):
            os.mkdir(self.config_dir)

        config = configparser.ConfigParser()
        if os.path.exists(self.config_file):
            try:
                config.read(self.config_file)
            except configparser.NoSectionError:
                config.add_section('jackal')
        else:
            config.add_section('jackal')
        config.set('jackal', 'host', host)
        config.set('jackal', 'index', index)

        with open(self.config_file, 'w') as configfile:
            config.write(configfile)

        if initialize_indices:
            from jackal.core import Host, Range, Service
            Host.init(index="{}-hosts".format(index))
            Range.init(index="{}-ranges".format(index))
            Service.init(index="{}-services".format(index))
