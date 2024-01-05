import pyupbit
import time
import math
import json
import datetime
import telepot

class UpbitPy():
    def __init__(self):
        now = datetime.datetime.now()
        self.check_fail = 'logs/' + now.strftime('%Y-%m-%d_%H%M%S') + '.log'
        file = open(self.check_fail, 'w', encoding="UTF8")
        file.close()
        
        self.tickers = {"KRW-BTC": [0,0,0,0], "KRW-ETH": [0,0,0,0]} # [매수목표가, 손절가, 매수가, 보유수]
        self.buyCount = len(self.tickers) # 코인 개수
        self.chkTime = int(datetime.datetime.now().strftime('%M'))
        self.KRWBalances = {}   # 코인별 매수 금액
        self.MAline = {}    # 코인별 이평선
        
        curTime = now.strftime('%Y-%m-%d %H:%M:%S')
        sendText = f"{curTime} - 변동성 돌파 전략을 시작합니다.\n"
        print(sendText)
        file = open(self.check_fail, 'a')
        file.write(sendText)
        file.close()
        self.send_msg(sendText)
        
        with open("keys.json", 'r') as file:
            data = json.load(file)
            apiKey = data["api-key"]
            secret = data["secret"]
        
        self.upbit = pyupbit.Upbit(apiKey, secret)
        self.setCoinsPrice()
        
    def setCoinsPrice(self):
        for ticker in self.tickers:
            # 코인별 매수 목표가 계산
            df = pyupbit.get_ohlcv(ticker, count=2)
            
            interval = df.iloc[0]['high'] - df.iloc[0]['low']   # 0번째 인덱스는 전날 데이터
            k_range = interval * 0.5
            targetPrice = df.iloc[1]['open'] + k_range  # 1번째 인덱스는 당일 데이터
            
            self.tickers[ticker][0] = targetPrice
            self.tickers[ticker][1] = df['low'].min()
            
            time.sleep(0.1)
            
        now = datetime.datetime.now()
        curTime = now.strftime('%Y-%m-%d %H:%M:%S')
        sendText = f"{curTime} - 목표가 계산 : {self.tickers}\n"
        print(sendText)
        file = open(self.check_fail, 'a')
        file.write(sendText)
        file.close()
        self.send_msg(sendText)
        
        
    def send_msg(self, msg):
        with open('telepot.json', 'r') as file:
            data = json.load(file)
            api = data['api_key']
            chatId = data['id']
        bot = telepot.Bot(api)
        bot.sendMessage(chatId, msg)

        
if __name__ == "__main__":
    upbitPy = UpbitPy()
    
