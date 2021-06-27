import requests
from enum import Enum
import re
import json


class ApiProtocol(Enum):
    HTTPS = 1
    HTTP = 2


class ApiServer(object):

    DNS_REGEXP = r''
    PROTOCOL_REGEXP = r'(http|https)://'

    def __init__(self, protocol: ApiProtocol, dns_name: str):
        super().__init__()
        self.protocol = protocol
        self.dns_name = dns_name
        self.base_url = f'{str(self.protocol.name).lower()}://{self.dns_name}'

    def __init__(self, server: str):
        super().__init__()
        protocol, dns_name = self._parse(server)
        self.protocol = protocol
        self.dns_name = dns_name
        self.base_url = f'{str(self.protocol.name).lower()}://{self.dns_name}'

    def _parse(self, server: str) -> tuple:
        matcher = re.search(r'((http|https)://)?([^/]+)', server)
        if matcher is None:
            raise Exception(f'Can not parse server: {server}')
        groups = matcher.groups()
        if not groups[0] is None:
            protocol = matcher.group(1)
        else:
            protocol = ApiProtocol.HTTPS
        dns_name = groups[2]
        return (protocol, dns_name)


class ApiMethod(Enum):
    GET = 1
    POST = 2


class ApiRequest(object):

    def __init__(self, server: str, request: str, params: dict = None):
        super().__init__()
        self.server = ApiServer(server)
        method, path = self._parse(request)
        self.method = method
        self.path = path
        self.params = self._parse_params(params)
        self.response = self._go()

    def _parse(self, request: str) -> tuple:
        matcher = re.search(r'(GET|POST)?\s+(.*)', request)
        if matcher is None:
            raise Exception(f'Can not parse request: {request}')
        groups = matcher.groups()
        if not groups[0] is None:
            method = ApiMethod[groups[0].upper()]
        else:
            method = ApiMethod.GET
        url = groups[1]
        return (method, url)

    def _parse_params(self, params: dict) -> str:
        return params

    def _go(self):
        if self.method == ApiMethod.GET:
            return requests.get(f'{self.server.base_url}{self.path}', params=self.params)
        if self.method == ApiMethod.POST:
            return requests.post(f'{self.server.base_url}{self.path}', params=self.params)
        raise Exception(f'Not implemented logic for HTTP method: {self.method}')

