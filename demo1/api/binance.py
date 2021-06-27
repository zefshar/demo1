import datetime

class BinanceKline:
    def __init__(self, kline: list):
        self.open_time = kline[0]
        self.open = kline[1]
        self.high = kline[2]
        self.low = kline[3]
        self.close = kline[4]
        self.volume = kline[5]
        self.close_time = kline[6]
        self.quote_asset_volume = kline[7]
        self.number_of_trades = kline[8]
        self.taker_buy_base_asset_volume = kline[9]
        self.taker_buy_quote_asset_volume = kline[10]
        self.ignore = kline[11]    
    
    def __repr__(self) -> str:
        return f'open_time: {datetime.datetime.fromtimestamp(self.open_time / 1000)}, open: {self.open}, high: {self.high}, low: {self.low}, ' +\
            f'close: {self.close}, volume: {self.volume}, close_time: {datetime.datetime.fromtimestamp(self.close_time / 1000)}, ' +\
            f'quote_asset_volume: {self.quote_asset_volume}, number_of_trades: {self.number_of_trades}, ' +\
            f'taker_buy_base_asset_volume: {self.taker_buy_base_asset_volume}, taker_buy_quote_asset_volume: {self.taker_buy_quote_asset_volume}, ' +\
            f'ignore: {self.ignore}'

    def to_list(self) -> list:
        return [
            datetime.datetime.fromtimestamp(self.open_time / 1000).isoformat() + 'Z',
            float(self.open),
            float(self.high),
            float(self.low),
            float(self.close),
            float(self.volume),
            datetime.datetime.fromtimestamp(self.close_time / 1000).isoformat() + 'Z',
            float(self.quote_asset_volume),
            float(self.number_of_trades),
            float(self.taker_buy_base_asset_volume),
            float(self.taker_buy_quote_asset_volume),
            float(self.ignore),
        ]

    @staticmethod
    def properties() -> list:
        return [
            'open_time',
            'open',
            'high',
            'low',
            'close',
            'volume',
            'close_time',
            'quote_asset_volume',
            'number_of_trades',
            'taker_buy_base_asset_volume',
            'taker_buy_quote_asset_volume',
            'ignore',
        ]
