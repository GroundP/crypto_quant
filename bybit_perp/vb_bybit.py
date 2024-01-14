import pprint
import pybit
import json
import time
import datetime
import pandas as pd
import math


class BybitAPI():
    def __init__(self):
        
        with open("keys.json", 'r') as file:
            data = json.load(file)
            apiKey = data["api-key"]
            secret = data["secret"]

        self.upbit = pyupbit.Upbit(apiKey, secret)
        symbol = "BTC/USDT"
        long_target, short_target = cal_target(binance, symbol)
        balance = binance.fetch_balance()
        usdt = balance['total']['USDT']
        op_mode = False
        position = {
            "type": None,
            "amount": 0
        }

        while True:
            now = datetime.datetime.now()

            if now.hour == 8 and now.minute == 50 and (0 <= now.second < 10):
                if op_mode and position['type'] is not None:
                    exit_position(binance, symbol, position)
                    op_mode = False         # 9시 까지는 다시 포지션 진입하지 않음

            # udpate target price
            if now.hour == 9 and now.minute == 0 and (20 <= now.second < 30):
                long_target, short_target = cal_target(binance, symbol)
                balance = binance.fetch_balance()
                usdt = balance['total']['USDT']
                op_mode = True
                time.sleep(10)

            ticker = binance.fetch_ticker(symbol)
            cur_price = ticker['last']
            amount = cal_amount(usdt, cur_price)

            if op_mode and position['type'] is None:
                enter_position(binance, symbol, cur_price, long_target,
                            short_target, amount, position)

            print(now, cur_price)
            time.sleep(1)


    def cal_target(exchange, symbol):
        btc = exchange.fetch_ohlcv(
            symbol=symbol,
            timeframe='1d',
            since=None,
            limit=10
        )

        df = pd.DataFrame(data=btc, columns=[
                        'datetime', 'open', 'high', 'low', 'close', 'volume'])
        df['datetime'] = pd.to_datetime(df['datetime'], unit='ms')
        df.set_index('datetime', inplace=True)

        yesterday = df.iloc[-2]
        today = df.iloc[-1]
        long_target = today['open'] + (yesterday['high'] - yesterday['low']) * 0.5
        short_target = today['open'] - (yesterday['high'] - yesterday['low']) * 0.5
        return long_target, short_target


    def cal_amount(usdt_balance, cur_price):
        portion = 0.1
        usdt_trade = usdt_balance * portion
        amount = math.floor((usdt_trade * 1000000)/cur_price) / 1000000
        return amount


    def enter_position(exchange, symbol, cur_price, long_target, short_target, amount, position):
        if cur_price > long_target:         # 현재가 > long 목표가
            position['type'] = 'long'
            position['amount'] = amount
            exchange.create_market_buy_order(symbol=symbol, amount=amount)
        elif cur_price < short_target:      # 현재가 < short 목표가
            position['type'] = 'short'
            position['amount'] = amount
            exchange.create_market_sell_order(symbol=symbol, amount=amount)


    def exit_position(exchange, symbol, position):
        amount = position['amount']
        if position['type'] == 'long':
            exchange.create_market_sell_order(symbol=symbol, amount=amount)
            position['type'] = None
        elif position['type'] == 'short':
            exchange.create_market_buy_order(symbol=symbol, amount=amount)
            position['type'] = None


    
