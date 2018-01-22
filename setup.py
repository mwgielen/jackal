from setuptools import setup

setup(name='jackal',
      version='0.4.7',
      description='Jackal provides a way to store results from hacking tools in a single place.',
      author='Matthijs Gielen',
      author_email='github@mwgielen.com',
      license='MIT',
      classifiers=[
          'Development Status :: 3 - Alpha',
          'License :: OSI Approved :: MIT License',
          'Programming Language :: Python :: 3 :: Only'
      ],
      requires_python='>=3',
      url='https://github.com/mwgielen/jackal/',
      packages=['jackal', 'jackal.scripts'],
      install_requires=['elasticsearch_dsl', 'python-libnmap', 'future', 'gevent', 'grequests', 'requests'],
      entry_points={
          'console_scripts': [
              'jk-status = jackal.scripts.status:main',
              'jk-hosts = jackal.scripts.hosts:main',
              'jk-hosts-overview = jackal.scripts.hosts:overview',
              'jk-ranges = jackal.scripts.ranges:main',
              'jk-ranges-overview = jackal.scripts.ranges:overview',
              'jk-import-nmap = jackal.scripts.nmap:import_file',
              'jk-filter = jackal.scripts.filter:filter',
              'jk-format = jackal.scripts.filter:format',
              'jk-configure = jackal.config:manual_configure',
              'jk-netdiscover = jackal.scripts.netdiscover:main',
              'jk-tomcat-brute = jackal.scripts.tomcat_brute:main',
              'jk-services = jackal.scripts.services:main',
              'jk-services-overview = jackal.scripts.services:overview',
              'jk-add-tag = jackal.scripts.tags:add_tag',
              'jk-remove-tag = jackal.scripts.tags:remove_tag',
              'jk-nessus = jackal.scripts.nessus:main',
              'jk-nmap-discover = jackal.scripts.nmap:nmap_discover',
              'jk-named-pipes = jackal.scripts.named_pipes:main',
              'jk-add-named-pipe = jackal.config:add_named_pipe',
          ]
      })
