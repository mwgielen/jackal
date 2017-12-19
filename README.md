# Jackal
Jackal provides a way to store results from hacking tools in a single place.


## Introduction
During a network penetration test, there is a lot of information that hackers have to their disposal:
- Ranges that are in use
- Hosts that are up.
- Port states on different hosts.
- Which hosts are investigated already

To sort through this data hackers may use things like cut, sort grep etc to go through this data. However this could lead to a lot of files on disk provided by different tools.
Jackal tries to simplify this process by storing everything on a central place by merging the data gathered by the hacker and making it easily searchable.


## Dependencies and installation

Jackal requires [python-libnmap](https://github.com/savon-noir/python-libnmap) and [elasticsearch_dsl](https://github.com/elastic/elasticsearch-dsl-py) to function.
To use the jk-netdiscover tool, netdiscover should be installed. Jackal seems to work fine in python3, use python2 at your own risk.

Thispackage can be installed with `pip3 install jackal` or the latest version can be installed with `python3 setup.py install`.

## Usage

Jackal provides tools to interact with the database. The stand alone tools that can be used are:
- jk-hosts, this provides a way to retrieve and search through the hosts data. See the command line arguments below.
- jk-ranges, this tool can be used to retrieve ranges that are saved from elasticsearch.
- jk-status, this tool will show some information about the data in the elasticsearch instance and print them to screen.
- jk-filter, to filter an json object to a single value. This provides the ability to use the output of jackal in other tools.
- jk-configure, to configure jackal.

Futhermore there are tools to interact with some commonly used tools to map the network:
- jk-import-nmap, to import a finished nmap scan into jackal
- jk-netdiscover, this will retrieve and scan ranges from elastic. Any discovered hosts are stored in elastic.

### Command line arguments
The command line arguments that are shared between all jackal tools can be obtained by the --help or -h switch:
```
  -h, --help            show this help message and exit
  -r RANGES, --ranges RANGES
                        The ranges to use
  -H HOSTS, --hosts HOSTS
                        The hosts to use
  -v                    Increase verbosity
  -s, --disable-save    Don't store the results automatically
  -f FILE, --file FILE  Input file to use
  -S SEARCH, --search SEARCH
                        Search string to use
  -p PORTS, --ports PORTS
                        Ports to include
  -u, --up              Only hosts / ports that are open / up
  -t TAG, --tag TAG     Tag(s) to search for, use (!) for not search, comma
                        (,) to seperate tags
  -c, --count           Only show the number of results
```

### Examples

A simple way to update the ranges in the elasticsearch instance is by piping your file with ranges to jk-ranges:
```
cat ranges.txt | jk-ranges
```
As long as the save is not disabled jackal will parse the input and store it in elasticsearch.
After doing this the ranges are shown on screen and later can be retrieved by using jk-ranges again.

The same can be done by piping a file of ip addresses to jk-hosts:
```
cat hosts.txt | jk-hosts
```

The hosts can be retrieved by using jk-hosts again.

To import a nmap scan into jackal use jk-import-nmap with the file flag:
```
jk-import-nmap /your/nmap/scan.xml
```
After the import is done the results can be shown by running the jk-hosts.

To filter the output of jk-hosts pipe the output to jk-filter and give a single argument to filter, for example:
```
jk-hosts -p 80 -u | jk-filter address
```
Will print the ip addresses of the hosts that have port 80 open and are up.

Jackal has support to use the netdiscover tool to search for hosts in the ranges. To scan the ranges that have not been scanned by netdiscover use the next command:
```
jk-netdiscover -t '!netdiscover'
```

## Building your own tools
Jackal provides a multiple classes to interact with the elasticsearch instance. If you want to include jackal in your own tool it's as simple as importing one of these classes.
All of these classes share the Core class. This means that these classes share most of the functionality.
```
from jackall import Ranges, Hosts, Services
from jackal.utils import print_json

ranges = Ranges()
for r in ranges.get_ranges():
    print_json(r.to_dict())

hosts = Hosts()
for h in hosts.get_hosts():
    print_json(h.to_dict())

services = Services()
for s in services.get_services():
    print_json(s.to_dict())
```

These core classes provides functionality to obtain the ranges, hosts and service from elasticsearch. Also it provides functionality to obtain hosts and ranges from pipes and to parse commonly used parameters.
The scripts folder contain some examples that provide some insight on how to use these classes.
