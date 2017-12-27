from setuptools import setup

setup(name='jackal',
      version='0.3.6',
      description='Jackal provides a way to store results from hacking tools in a single place.',
      author='Matthijs Gielen',
      author_email='github@mwgielen.com',
      url='https://github.com/mwgielen/jackal/',
      packages=['jackal', 'jackal.scripts'],
      install_requires=['elasticsearch_dsl', 'python-libnmap', 'future', 'gevent', 'grequests', 'requests'],
      extras_require={
          'Sniffer': ["psutil", "scapy-python3"]
      },
      entry_points={
          'console_scripts': [
              'jk-status = jackal.scripts.status:main',
              'jk-hosts = jackal.scripts.hosts:main',
              'jk-ranges = jackal.scripts.ranges:main',
              'jk-import-nmap = jackal.scripts.import_nmap:main',
              'jk-filter = jackal.scripts.filter:filter',
              'jk-format = jackal.scripts.filter:format',
              'jk-configure = jackal.config:manual_configure',
              'jk-netdiscover = jackal.scripts.netdiscover:main',
              'jk-tomcat-brute = jackal.scripts.tomcat_brute:main',
              'jk-services = jackal.scripts.services:main',
              'jk-overview = jackal.scripts.services:overview',
              'jk-add-tag = jackal.scripts.tags:add_tag',
              'jk-nessus = jackal.scripts.nessus:main',
              'jk-nmap-discover = jackal.scripts.nmap:nmap_discover',
              'jk-sniffer = jackal.scripts.sniffer:main',
          ]
      })
