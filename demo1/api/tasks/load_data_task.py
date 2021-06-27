from demo1.api.binance import BinanceKline
from demo1.api.api_request import ApiRequest
import os.path
import pickle
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import configparser
import json
import datetime
from datetime import timezone
import time
import sys

from demo1.api.tasks.basic_task import BasicTask
from demo1.api.demo1_error import Demo1Error
from demo1.api.tasks.cache.memory_cache import MemoryCache, google_creds


class LoadDataTask(BasicTask):

    def execute(self):
        from_date = datetime.datetime.fromisoformat(self.args[0]['from'])
        to_date = min(datetime.datetime.fromisoformat(
            self.args[0]['to']), datetime.datetime.now())
        symbol = self.args[0]['symbol']  # value example: BTCUSDT

        self.logger.info('Let\'s start')

        home = os.path.expanduser("~")
        credentials = configparser.ConfigParser(allow_no_value=True)
        with open(os.path.join(home, '.demo1', 'credentials.txt'), 'r') as f:
            credentials.read_string('\n'.join(f.readlines()))

        creds = google_creds()

        service = build('sheets', 'v4', credentials=creds, cache=MemoryCache())
        # sheet = service.spreadsheets()

        spreadsheet_id = '17wtNuilC5Z63mcsb85PTK868opdXXSG8GSUA-fZG_Vk'
        # WRITE HEADER
        result = service.spreadsheets().values().update(
            spreadsheetId=spreadsheet_id, range='Data!A2:L2',
            valueInputOption='USER_ENTERED', body={'values': [BinanceKline.properties()]}).execute()

        # Count minutes between dates / 1000 = count of batchs
        minutes = int(to_date.replace(tzinfo=timezone.utc).timestamp(
        ) - from_date.replace(tzinfo=timezone.utc).timestamp()) // 60
        if minutes <= 0:
            self.logger.info(
                f'Wrong interval between {from_date} {to_date}. Count of minutes is {minutes}')
            return
        if minutes > 10000:
            self.logger.info(
                f'Exceed limit of data between {from_date} {to_date}. Set count of minutes to {minutes}')
            minutes = 10000

        # CLEAR SHEET BEFORE LOAD DATA
        spreadsheet = service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
        data_sheet = [sheet for sheet in spreadsheet['sheets'] if str(sheet['properties']['title']).strip().upper() == 'DATA'][0]
        grafics_sheet = [sheet for sheet in spreadsheet['sheets'] if str(sheet['properties']['title']).strip().upper() == 'GRAFICS'][0]
        end_index = data_sheet['properties']['gridProperties']['rowCount'] - 1
        if end_index > 2:
            result = service.spreadsheets().batchUpdate(spreadsheetId=spreadsheet_id, body={
                'requests': [
                    {'deleteDimension': {
                        'range': {
                            'sheetId': 0,
                            'dimension': 'ROWS',
                            'startIndex': 2,
                            'endIndex': end_index
                        }
                    }}
                ]
            }).execute()
            # result = service.spreadsheets().values().clear(spreadsheetId=spreadsheet_id, range='Data!A3:L').execute()
        # CLEAR FIRST LINE
        result = service.spreadsheets().values().update(
            spreadsheetId=spreadsheet_id, range='Data!A3:L3',
            valueInputOption='USER_ENTERED', body={'values': [([''] * len(BinanceKline.properties()))]}).execute()

        count = 0
        min_price = sys.maxsize
        max_price = 0
        start_time = int(from_date.replace(
            tzinfo=timezone.utc).timestamp() * 1e3)
        for step_start_time_limit in [(o, int(start_time + o*1000*60*1e3), 1000 if minutes - (o + 1)*1000 > 0 else minutes % 1000) for o in range(0, minutes // 1000 + 1)]:
            step, start_time, limit = step_start_time_limit
            _count, batch_min_price, batch_max_price = self._load_data(
                service, spreadsheet_id, symbol, start_time, limit, step)
            count += _count
            min_price = min(min_price, batch_min_price)
            max_price = max(max_price, batch_max_price)
            time.sleep(1)  # API LIMITS

        # MARK HEAD AS PROCESSED
        result = service.spreadsheets().batchUpdate(
            spreadsheetId=spreadsheet_id, body={'requests': [
                {'updateCells': {
                    'range': {
                        'sheetId': data_sheet['properties']['sheetId'],
                        'startRowIndex': 0,
                        'endRowIndex': 1,
                        'startColumnIndex': 0,
                        'endColumnIndex': 5,
                    },
                    'rows': [
                        {'values': [
                            {'userEnteredFormat': {
                                'backgroundColor': {
                                    'red': 1,
                                    'green': 1,
                                    'blue': 1
                                }
                            }}
                        ]}
                    ],
                    'fields': 'userEnteredFormat.backgroundColor'
                }}
            ]}).execute()
        for chart in grafics_sheet['charts']:
            try:
                update_chart_spec = chart
                if self._update_chart(update_chart_spec, count, min_price, max_price):
                    result = service.spreadsheets().batchUpdate(
                        spreadsheetId=spreadsheet_id, body={'requests': [
                            {
                                'updateChartSpec': update_chart_spec
                            }
                        ]}).execute()
                    time.sleep(1)  # GOOGLE SHEET ISSUE
            except Exception as e:
                self.logger.error(
                    f'Can not update chart {json.dumps(chart)}. Error is {e}', exc_info=True)

        self.logger.info(f'{count} rows updated.')

    def _update_chart(self, chart, count, min_price, max_price):
        if count == 0:
            return False
        title = chart['spec']['title'] if 'title' in chart['spec'] else None
        if title == 'open, high, low и close':
            self.logger.info(
                f'Start update chart {json.dumps(chart)}.')
            if 'position' in chart:
                del chart['position']

            if len(chart['spec']['candlestickChart']) == 0:
                chart['spec']['candlestickChart'] = {
                    'domain': {  # chart['spec']['candlestickChart']['domain']['data']['sourceRange']['sources'][0]['endRowIndex']
                        "data": {
                            "sourceRange": {
                                "sources": [
                                    {
                                        "startRowIndex": 3,
                                        "endRowIndex": count + 3 + 1,
                                        "startColumnIndex": 0,
                                        "endColumnIndex": 1
                                    }
                                ]
                            }
                        }
                    },
                    'data': [{
                        "lowSeries": {  # chart['spec']['candlestickChart']['data'][0]['lowSeries']['data']['sourceRange']['sources'][0]['endRowIndex']
                            "data": {
                                "sourceRange": {
                                    "sources": [
                                        {
                                            "startRowIndex": 3,
                                            "endRowIndex": count + 3 + 1,
                                            "startColumnIndex": 3,
                                            "endColumnIndex": 4
                                        }
                                    ]
                                }
                            }
                        },
                        "openSeries": {  # chart['spec']['candlestickChart']['data'][0]['openSeries']['data']['sourceRange']['sources'][0]['endRowIndex']
                            "data": {
                                "sourceRange": {
                                    "sources": [
                                        {
                                            "startRowIndex": 3,
                                            "endRowIndex": count + 3 + 1,
                                            "startColumnIndex": 1,
                                            "endColumnIndex": 2
                                        }
                                    ]
                                }
                            }
                        },
                        "closeSeries": {  # chart['spec']['candlestickChart']['data'][0]['closeSeries']['data']['sourceRange']['sources'][0]['endRowIndex']
                            "data": {
                                "sourceRange": {
                                    "sources": [
                                        {
                                            "startRowIndex": 3,
                                            "endRowIndex": count + 3 + 1,
                                            "startColumnIndex": 4,
                                            "endColumnIndex": 5
                                        }
                                    ]
                                }
                            }
                        },
                        "highSeries": {  # chart['spec']['candlestickChart']['data'][0]['highSeries']['data']['sourceRange']['sources']['endRowIndex']
                            "data": {
                                "sourceRange": {
                                    "sources": [
                                        {
                                            "startRowIndex": 3,
                                            "endRowIndex": count + 3 + 1,
                                            "startColumnIndex": 2,
                                            "endColumnIndex": 3
                                        }
                                    ]
                                }
                            }
                        }
                    }]
                }
            else:
                chart['spec']['candlestickChart']['domain']['data']['sourceRange']['sources'][0]['startRowIndex'] = 3
                chart['spec']['candlestickChart']['domain']['data']['sourceRange']['sources'][0]['endRowIndex'] = count + 3 + 1
                chart['spec']['candlestickChart']['data'][0]['lowSeries']['data']['sourceRange']['sources'][0]['startRowIndex'] = 3
                chart['spec']['candlestickChart']['data'][0]['lowSeries']['data']['sourceRange']['sources'][0]['endRowIndex'] = count + 3 + 1
                chart['spec']['candlestickChart']['data'][0]['openSeries']['data']['sourceRange']['sources'][0]['startRowIndex'] = 3
                chart['spec']['candlestickChart']['data'][0]['openSeries']['data']['sourceRange']['sources'][0]['endRowIndex'] = count + 3 + 1
                chart['spec']['candlestickChart']['data'][0]['closeSeries']['data']['sourceRange']['sources'][0]['startRowIndex'] = 3
                chart['spec']['candlestickChart']['data'][0]['closeSeries']['data']['sourceRange']['sources'][0]['endRowIndex'] = count + 3 + 1
                chart['spec']['candlestickChart']['data'][0]['highSeries']['data']['sourceRange']['sources'][0]['startRowIndex'] = 3
                chart['spec']['candlestickChart']['data'][0]['highSeries']['data']['sourceRange']['sources'][0]['endRowIndex'] = count + 3 + 1

            # chart['spec']['vAxis'] = {'viewWindow': {'min': min_price, 'max': max_price}}            
            chart['spec']['maximized'] = True
            return True
        elif title == 'volume относительно параметра "open_time"':
            self.logger.info(
                f'Start update chart {json.dumps(chart)}.')
            if 'position' in chart:
                del chart['position']

            if len(chart['spec']['basicChart']['domains']) == 0:
                chart['spec']['basicChart']['domains'] = [
                    {
                        "domain": { # chart['spec']['basicChart']['domains'][0]['domain']['sourceRange']['sources'][0]['endRowIndex']
                            "sourceRange": {
                                "sources": [
                                    {
                                        "startRowIndex": 3,
                                        "endRowIndex": count + 3 + 1,
                                        "startColumnIndex": 0,
                                        "endColumnIndex": 1
                                    }
                                ]
                            }
                        }
                    }
                ]
                chart['spec']['basicChart']['series'] = [
                    {
                        "series": { # chart['spec']['basicChart']['domains'][0]['domain']['sourceRange']['sources'][0]['endRowIndex']
                            "sourceRange": {
                                "sources": [
                                    {
                                        "startRowIndex": 3,
                                        "endRowIndex": count + 3 + 1,
                                        "startColumnIndex": 5,
                                        "endColumnIndex": 6
                                    }
                                ]
                            }
                        }
                    }
                ]
            else:
                chart['spec']['basicChart']['domains'][0]['domain']['sourceRange']['sources'][0]['startRowIndex'] = 3
                chart['spec']['basicChart']['domains'][0]['domain']['sourceRange']['sources'][0]['endRowIndex'] = count + 3 + 1
                chart['spec']['basicChart']['series'][0]['series']['sourceRange']['sources'][0]['startRowIndex'] = 3
                chart['spec']['basicChart']['series'][0]['series']['sourceRange']['sources'][0]['endRowIndex'] = count + 3 + 1

            chart['spec']['maximized'] = True
            return True
        return False

    def _load_data(self, service, spreadsheet_id, symbol, start_time, limit, step) -> int:
        # GET KLINES
        response = ApiRequest('api.binance.com', 'GET /api/v3/klines', {
            'symbol': symbol,  # BTCUSDS,BTCUSDT,BTCUSDC
            'interval': '1m',
            'startTime': start_time,
            'limit': limit,
        }).response

        values = []
        count = 0
        batch_min_price = sys.maxsize
        batch_max_price = 0
        if response.ok:
            for kline in response.json():
                binance_kline = BinanceKline(kline)
                values.append(binance_kline.to_list())
                count += 1
                batch_min_price = min(batch_min_price, float(binance_kline.open), float(
                    binance_kline.high), float(binance_kline.low), float(binance_kline.close))
                batch_max_price = max(batch_max_price, float(binance_kline.open), float(
                    binance_kline.high), float(binance_kline.low), float(binance_kline.close))
        else:
            raise Demo1Error(
                f'Response from binance.com invalid: {response}')
        # body
        body = {
            'values': values
        }
        result = service.spreadsheets().values().append(
            spreadsheetId=spreadsheet_id, range=f'Data!A{3 + step*1000}:L',
            valueInputOption='USER_ENTERED', body=body).execute()

        return count, batch_min_price, batch_max_price
