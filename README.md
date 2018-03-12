# Jackal
Jackal provides a way to store results from hacking tools in a single place.


## Introduction
During a network penetration test, there is a lot of information that hackers have to their disposal:
- Ranges that are in use
- Hosts that are up.
- Open ports on different hosts.
- Which hosts are investigated already
- Output from different tools

To sort through this data hackers may use things like cut, sort grep etc. to go through this data. However this could lead to a lot of files on disk provided by different tools and can be a hassle to exchange (securely) between teammembers.
Jackal tries to simplify this process by storing everything on a central place by merging the data gathered by the hackers and making it easily searchable.


## Dependencies and installation
Jackal only works on Python 3.
Jackal requires [python-libnmap](https://github.com/savon-noir/python-libnmap) and [elasticsearch_dsl](https://github.com/elastic/elasticsearch-dsl-py) to function. Also an [elasticsearch](https://www.elastic.co/) instance is required. Some of the included tools require some other install tools on your system, for example jk-netdiscover requires netdiscover.


This package can be installed with `pip3 install jackal` or the latest version can be installed with `python3 setup.py install`.

## Usage

Jackal provides tools to interact with the database. The stand alone tools that can be used are:
- jk-hosts, this provides a way to retrieve and search through the hosts data. See the command line arguments below.
- jk-ranges, this tool can be used to retrieve ranges that are saved from elasticsearch.
- jk-services, retrieves services.
- jk-users, retrieves users.
- jk-status, this tool will show some information about the data in the elasticsearch instance.
- jk-filter, to filter an json object to a single value. This provides the ability to use the output of jackal in other tools.
- jk-format, to format the output of the ranges, hosts and services tools to improve reading.
- jk-configure, to configure jackal.
- jk-initialize, to initialize the indices in elasticsearch.
- jk-add-named-pipe, tool to update the named pipe configuration.

Jackal also provides ways to import output from other tools:
- jk-import-nmap, to import a finished [nmap](https://nmap.org/) scan into jackal
- jk-import-domaindump, to import the output of [ldapdomaindump](https://github.com/dirkjanm/ldapdomaindump).

Futhermore there are tools to interact with some commonly used tools to map the network:
- jk-nmap-discover, to perform a ping or reverse lookup scan on the ranges in elasticsearch.
- jk-nmap, to perform nmap scans on hosts in elasticsearch.
- jk-netdiscover, this will retrieve and scan ranges from elastic. Any discovered hosts are stored in elastic.

### Examples

A simple way to update the ranges in the elasticsearch instance is by piping your file with ranges to jk-ranges:
```
cat ranges.txt | jk-ranges
```
Jackal will parse the input and store it in elasticsearch.
After doing this the ranges are shown on screen and later can be retrieved by using jk-ranges.

The same can be done by piping a file of ip addresses to jk-hosts and usernames to jk-users:
```
cat hosts.txt | jk-hosts
echo "admin"  | jk-users
```

If you know a specific user, host or range is in the database you can also retrieve the information this way.


To import a nmap scan into jackal use jk-import-nmap:
```
jk-import-nmap /your/nmap/scan.xml other/scan.xml
```
After the import is done the results can be shown by running the jk-hosts and jk-services tools.

To filter the output of jk-hosts pipe the output to jk-filter and give a single argument to filter, for example:
```
jk-hosts -p 80 -u | jk-filter address
```
Will print the ip addresses of the hosts that have port 80 open and are up.

The jk-format tool can be used to create more human readable output, some default values are provided. Othwise the second argument will be interpreted as a [python format string](https://docs.python.org/3.3/library/string.html#format-specification-mini-language).

```
jk-ranges | jk-format
jk-hosts | jk-format {address} # Is the same as jk-filter address
jk-services -S http | jk-format '{service}://{address}:{port}'
```

Jackal has some wrappers around commonly used tools to find hosts and services on the network these include:
```
jk-netdiscover
jk-nmap-discover
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
# Ranges will be obtained from the pipe, user given search parameters or all ranges.
for r in ranges.get_ranges():
    # The include_meta parameter will include more information about the type, index and others.
    print_json(r.to_dict(include_meta=True))

# Disables the pipe
hosts = HostSearch(use_pipe=False)
# Optional search options can be given, if a user gives no search parameters, these will be used.
for h in hosts.get_hosts(ports=['445']):
    print_json(h.to_dict())

services = ServiceSearch()
# The search function will always honor the given arguments, user input and piped objects are ignored.
for s in services.search(ports=['445']):
    print_json(s.to_dict())
```

These core classes provides functionality to obtain the ranges, hosts and service from elasticsearch. Also it provides functionality to obtain hosts and ranges from pipes and to parse commonly used parameters.
The scripts folder contain some examples that provide some insight on how to use these classes.
