#!/usr/bin/env python3
import subprocess
from jackal import Host, RangeSearch, Logger
from jackal.utils import print_line


class NetDiscover(object):

    def __init__(self, ip_range):
        self.ip_range = ip_range
        self.ips = []


    def execute(self):
        print_line("Starting on range {}".format(self.ip_range.range))
        command = "netdiscover -r {} -P -N".format(self.ip_range.range)
        process = subprocess.Popen(command.split(' '), stdout=subprocess.PIPE)
        output = process.stdout.read().decode('utf-8').strip().split('\n')
        for line in output:
            line = [i for i in filter(None, line.strip().split('  '))]
            if len(line) == 5:
                self.ips.append(line[0])
        print_line("Found {} systems".format(len(self.ips)))
        return len(self.ips)


    def save(self):
        self.ip_range.add_tag('netdiscover')
        self.ip_range.update(tags=self.ip_range.tags)

        for ip in self.ips:
            host = Host.get(ip, ignore=404)
            if host:
                host.add_tag('netdiscover')
                host.update(tags=host.tags)
            else:
                host = Host(address=ip, tags=['netdiscover'])
                host.save()

def main():
    ranges = RangeSearch()
    arguments = ranges.argparser.parse_args()
    if arguments.tags or ranges.is_pipe:
        ranges = ranges.get_ranges()
    else:
        ranges = ranges.search(tags=['!netdiscover'])

    for r in ranges:
        discover = NetDiscover(r)
        results = discover.execute()
        discover.save()

    Logger().log('netdiscover', "Netdiscover on {} ranges".format(len(ranges)), stats={'scanned_ranges': len(ranges), 'hosts': results})


if __name__ == '__main__':
    main()
