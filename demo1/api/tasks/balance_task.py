from demo1.api.binance import BinanceKline
from demo1.api.signed_api_request import SignedApiRequest
import os.path
import pickle
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery_cache.base import Cache
import configparser
import json
import datetime
from datetime import timezone, datetime
import time
import sys

from demo1.api.tasks.basic_task import BasicTask
from demo1.api.demo1_error import Demo1Error
from demo1.api.tasks.cache.memory_cache import MemoryCache, google_creds
from demo1.api.api_request import ApiRequest


class BalanceTask(BasicTask):

    def execute(self):
        self.logger.info(f'Execute buy task for request {self.args[0]}')

        symbol = self.args[0]['symbol'] if 'symbol' in self.args[0] else None  # value example: USDT
        # Response store to google sheet row
        row = self.args[0]['row']  # row in googlesheet

        home = os.path.expanduser("~")
        credentials = configparser.ConfigParser(allow_no_value=True)
        with open(os.path.join(home, '.demo1', 'credentials.txt'), 'r') as f:
            credentials.read_string('\n'.join(f.readlines()))

        creds = google_creds()
        service = build('sheets', 'v4', credentials=creds, cache=MemoryCache())

        spreadsheet_id = '17wtNuilC5Z63mcsb85PTK868opdXXSG8GSUA-fZG_Vk'
        # GET API KEYS
        spreadsheet = service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
        # private_sheet = [sheet for sheet in spreadsheet['sheets'] if str(sheet['properties']['title']).strip().upper() == 'PRIVATE'][0]
        # scenario_sheet = [sheet for sheet in spreadsheet['sheets'] if str(sheet['properties']['title']).strip().upper() == 'SCENARIO'][0]

        request = service.spreadsheets().values().get(spreadsheetId=spreadsheet_id, range='Private!A2:B3', valueRenderOption='UNFORMATTED_VALUE', dateTimeRenderOption='FORMATTED_STRING')
        response = request.execute()
        table = dict(response['values'])
        keys = (table['x-api-cryp23'], table['s-api-cryp23'])

        response = ApiRequest('api.binance.com', 'GET /api/v3/time', {}).response
        server_time = response.json()['serverTime']

        response = SignedApiRequest('api.binance.com', 'GET /api/v3/account', keys, {
            'recvWindow': 5000,
            'timestamp': server_time
        }).response
        response_data = response.json()
        assets_balances = [] if not response_data or 'balances' not in response_data else response_data['balances']
        if symbol:
            requested_not_zero_balances = [f'{a["asset"]}:{a["free"]}' for a in assets_balances if float(a["free"]) > 0 and a["asset"] == symbol]
        else:
            requested_not_zero_balances = [f'{a["asset"]}:{a["free"]}' for a in assets_balances if float(a["free"]) > 0]

        result = service.spreadsheets().values().update(
            spreadsheetId=spreadsheet_id, range=f'ScenarioRecorder!E{row}:F{row}',
            valueInputOption='USER_ENTERED', body={'values': [([f'{requested_not_zero_balances}', f'{response.request.body} => {json.dumps(response_data)}'])]}).execute()
