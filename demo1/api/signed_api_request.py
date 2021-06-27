import hmac
import hashlib
import requests
from demo1.api.api_request import ApiMethod, ApiRequest


class SignedApiRequest(ApiRequest):

    def __init__(self, server: str, request: str, keys: tuple, params: dict = None):
        super().__init__(server, request, {'params': params, 'api_key': keys[0], 'secret_key': keys[1]})

    @staticmethod
    def _data(params):
        return '&'.join([f'{k}={v}' for k, v in params.items()])

    def _go(self):
        if self.method == ApiMethod.POST:
            data = self._data(self.params['params'])
            signature = hmac.new(self.params['secret_key'].encode('utf-8'), data.encode('utf-8'), hashlib.sha256).hexdigest()
            return requests.post(f'{self.server.base_url}{self.path}', data=f'{data}&signature={signature}', headers={'X-MBX-APIKEY': self.params['api_key']})
        if self.method == ApiMethod.GET:
            data = self._data(self.params['params'])
            signature = hmac.new(self.params['secret_key'].encode('utf-8'), data.encode('utf-8'), hashlib.sha256).hexdigest()
            return requests.get(f'{self.server.base_url}{self.path}?{data}&signature={signature}', headers={'X-MBX-APIKEY': self.params['api_key']})
        raise Exception(f'Not implemented logic for HTTP method: {self.method}')
