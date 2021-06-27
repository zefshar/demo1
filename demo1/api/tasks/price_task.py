from demo1.api.binance import BinanceKline
from demo1.api.api_request import ApiRequest
import os.path
import pickle
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery_cache.base import Cache
import configparser
import json
from datetime import timezone, datetime
import time
import sys

from demo1.api.tasks.basic_task import BasicTask
from demo1.api.demo1_error import Demo1Error
from demo1.api.tasks.cache.memory_cache import MemoryCache, google_creds
from demo1.api.signed_api_request import SignedApiRequest


class PriceTask(BasicTask):

    def execute(self):
        self.logger.info(f'Execute sell task for request {self.args[0]}')

        symbol = self.args[0].get('symbol', None)  # value example: BTCUSDT
        row = self.args[0]['row']  # row in google-sheet

        home = os.path.expanduser("~")
        credentials = configparser.ConfigParser(allow_no_value=True)
        with open(os.path.join(home, '.demo1', 'credentials.txt'), 'r') as f:
            credentials.read_string('\n'.join(f.readlines()))

        creds = google_creds()
        service = build('sheets', 'v4', credentials=creds, cache=MemoryCache())

        spreadsheet_id = '17wtNuilC5Z63mcsb85PTK868opdXXSG8GSUA-fZG_Vk'

        try:
            if not symbol:
                raise Demo1Error(f'Symbol is mandatory parameter (example: symbol=BTCUSDT)')

            # GET API KEYS
            spreadsheet = service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
            # private_sheet = [sheet for sheet in spreadsheet['sheets'] if str(sheet['properties']['title']).strip().upper() == 'PRIVATE'][0]
            # scenario_sheet = [sheet for sheet in spreadsheet['sheets'] if str(sheet['properties']['title']).strip().upper() == 'SCENARIO'][0]

            request = service.spreadsheets().values().get(spreadsheetId=spreadsheet_id, range='Private!A2:B3', valueRenderOption='UNFORMATTED_VALUE', dateTimeRenderOption='FORMATTED_STRING')
            response = request.execute()
            table = dict(response['values'])
            keys = (table['x-api-cryp23'], table['s-api-cryp23'])

            response = ApiRequest('api.binance.com', 'GET /api/v3/avgPrice', {
                'symbol': symbol,  # BTCUSDS,BTCUSDT,BTCUSDC
            }).response
            result = response.json()['price'] if response.ok else f'[{datetime.now()}] Error'
            service.spreadsheets().values().update(
                spreadsheetId=spreadsheet_id, range=f'ScenarioRecorder!E{row}:F{row}',
                valueInputOption='USER_ENTERED', body={'values': [([result, f'{response.request.body} => {json.dumps(response.json())}'])]}).execute()
        except Exception as e:
            service.spreadsheets().values().update(
                spreadsheetId=spreadsheet_id, range=f'ScenarioRecorder!E{row}:F{row}',
                valueInputOption='USER_ENTERED', body={'values': [([f'[{datetime.now()}] Error', f'{e}'])]}).execute()
            raise e