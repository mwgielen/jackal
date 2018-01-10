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
Jackal only works on Python 3.
Jackal requires [python-libnmap](https://github.com/savon-noir/python-libnmap) and [elasticsearch_dsl](https://github.com/elastic/elasticsearch-dsl-py) to function. Some of the included tools require some other install tools on your system, for example jk-netdiscover requires netdiscover.

This package can be installed with `pip install jackal` or the latest version can be installed with `python setup.py install`.

## Usage

Jackal provides tools to interact with the database. The stand alone tools that can be used are:
- jk-hosts, this provides a way to retrieve and search through the hosts data. See the command line arguments below.
- jk-ranges, this tool can be used to retrieve ranges that are saved from elasticsearch.
- jk-status, this tool will show some information about the data in the elasticsearch instance and print them to screen.
- jk-filter, to filter an json object to a single value. This provides the ability to use the output of jackal in other tools.
- jk-format, to format the output of the ranges, hosts and services tools to improve reading.
- jk-configure, to configure jackal.

Futhermore there are tools to interact with some commonly used tools to map the network:
- jk-import-nmap, to import a finished nmap scan into jackal
- jk-nmap, to perform a ping or reverse lookup scan on the ranges in elasticsearch.
- jk-netdiscover, this will retrieve and scan ranges from elastic. Any discovered hosts are stored in elastic.

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

You can also generate urls of hosts by using the jk-format tool:
```
jk-services -S http | jk-format '{service}://{address}:{port}'
```

Jackal has some wrappers around commonly used tools to find hosts on the network these include:
```
jk-netdiscover
jk-nmap
jk-sniffer
```
These tools will include the tag in the found hosts and ranges to indicate which tool found it.

### Named pipes
Jackal has a build in named pipe server, this server can be used to give access to the data of jackal in other tools.
To start using it first configure the usage with jk-configure, after add new pipes to the config file or use the jk-add-named-pipe tool.
An example of a named pipe config is shown below:

```
[smb]
type = service
ports = 445
up = 1
unique = 1
format = {address}
```

After configuring named pipes start the jk-named-pipe tool. It will show the named pipes that are configured and will indicate what pipes are accessed.
Now the pipes can be used in other programs, for example cat or in msfconsole by using the 'file:' option.

```
    set RHOSTS file:/path/to/pipes/dir/smb
```

Metasploit will then access the file to get the hosts from the file.


## Building your own tools
Jackal provides a multiple classes to interact with the elasticsearch instance. If you want to include jackal in your own tool it's as simple as importing one of these classes.
All of these classes share the Core class. This means that these classes share most of the functionality.
```
from jackall import RangeSearch, HostSearch, ServiceSearch
from jackal.utils import print_json

ranges = RangeSearch()
for r in ranges.get_ranges():
    print_json(r.to_dict())

hosts = HostSearch()
for h in hosts.get_hosts():
    print_json(h.to_dict())

services = ServiceSearch()
for s in services.get_services():
    print_json(s.to_dict())
```

These core classes provides functionality to obtain the ranges, hosts and service from elasticsearch. Also it provides functionality to obtain hosts and ranges from pipes and to parse commonly used parameters.
The scripts folder contain some examples that provide some insight on how to use these classes.
