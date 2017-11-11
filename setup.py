from setuptools import setup

setup(name='jackal',
      version='0.1.3',
      description='Jackal provides a way to store results from hacking tools in a single place.',
      author='Matthijs Gielen',
      author_email='github@mwgielen.com',
      url='https://github.com/mwgielen/jackal/',
      packages=['jackal'],
      install_requires=['elasticsearch_dsl', 'python-libnmap', 'builtins'],
      scripts=['bin/jk-status', 'bin/jk-hosts', 'bin/jk-ranges', 'bin/jk-import-nmap', 'bin/jk-filter', 'bin/jk-configure', 'bin/jk-netdiscover'])
