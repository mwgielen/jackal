#!/usr/bin/env python3
import subprocess
from jackal import Host, Core
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


    def save(self):
        tags = self.ip_range.tags or []
        tags.append('netdiscover')
        tags = list(set(tags))
        self.ip_range.update(tags=tags)

        for ip in self.ips:
            host = Host.get(ip, ignore=404)
            if host:
                tags = host.tags or []
                tags.append('netdiscover')
                tags = list(set(tags))
                host.update(tags=tags)
            else:
                host = Host(address=ip, tags=['netdiscover'])
                host.save()


if __name__ == '__main__':
    core = Core()
    ranges = core.get_ranges()
    for r in ranges:
        discover = NetDiscover(r)
        discover.execute()
        if not core.arguments.disable_save:
            discover.save()
