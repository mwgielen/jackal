import json
import datetime
from jackal import HostSearch, Logger
from jackal.config import Config
import requests


class Nessus(object):
    """
        Quick nessus class to create and start nessus scans.
    """

    def __init__(self, access, secret, url, template_name):
        self.headers = {
            "X-ApiKeys": "accessKey = {}; secretKey = {};".format(access, secret),
            "content-type": "application/json"
        }
        if not url.endswith('/'):
            url += '/'
        self.url = url
        self.template_name = template_name


    def get_template_uuid(self):
        """
            Retrieves the uuid of the given template name.
        """
        response = requests.get(self.url + 'editor/scan/templates', headers=self.headers, verify=False)
        templates = json.loads(response.text)
        for template in templates['templates']:
            if template['name'] == self.template_name:
                return template['uuid']


    def create_scan(self, host_ips):
        """
            Creates a scan with the given host ips
            Returns the scan id of the created object.
        """
        now = datetime.datetime.now()
        data = {
            "uuid": self.get_template_uuid(),
            "settings": {
                "name": "jackal-" + now.strftime("%Y-%m-%d %H:%M"),
                "text_targets": host_ips
            }
        }
        response = requests.post(self.url + 'scans', data=json.dumps(data), verify=False, headers=self.headers)
        if response:
            result = json.loads(response.text)
            return result['scan']['id']


    def start_scan(self, scan_id):
        """
            Starts the scan identified by the scan_id.s
        """
        requests.post(self.url + 'scans/{}/launch'.format(scan_id), verify=False, headers=self.headers)


def main():
    """
        This function obtains hosts from core and starts a nessus scan on these hosts.
        The nessus tag is appended to the host tags.
    """
    config = Config()
    core = HostSearch()
    hosts = core.get_hosts(tags=['!nessus'], up=True)
    hosts = [host for host in hosts]
    host_ips = ",".join([str(host.address) for host in hosts])

    url = config.get('nessus', 'host')
    access = config.get('nessus', 'access_key')
    secret = config.get('nessus', 'secret_key')
    template_name = config.get('nessus', 'template_name')

    nessus = Nessus(access, secret, url, template_name)

    scan_id = nessus.create_scan(host_ips)
    nessus.start_scan(scan_id)

    for host in hosts:
        host.add_tag('nessus')
        host.save()

    Logger().log("nessus", "Nessus scan started on {} hosts".format(len(hosts)), {'scanned_hosts': len(hosts)})

if __name__ == '__main__':
    main()
