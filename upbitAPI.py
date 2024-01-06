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
        
        sendText = "변동성 돌파 전략을 시작합니다."
        self.log(sendText)
        self.send_msg(sendText)
        
        with open("keys.json", 'r') as file:
            data = json.load(file)
            apiKey = data["api-key"]
            secret = data["secret"]
        
        self.upbit = pyupbit.Upbit(apiKey, secret)
        self.setCoinsPrice()    # 목표가 계산
        self.getMAline()    # 이동평균 계산
        self.checkNowMyTickers()    # 보유 현황 확인
        
    def checkNowMyTickers(self):
        balances = self.upbit.get_balances()  # 전체 잔고 조회
        print(balances)
        KRWBlanace = 0
        for balance in balances:
            if balance['currency'] == 'KRW':
                KRWBlanace += float(balance['balance'])
            elif balance['avg_buy_price'] != '0' and (balance['currency'] == 'BTC' or balance['currency'] == 'ETH'):
                KRWBlanace += float(balance['balance']) * float(balance['avg_buy_price'])
                ticker = balance['unit_currency'] + '-' + balance['currency']
                price = float(balance['avg_buy_price'])
                myCoin = float(balance['balance'])
                self.tickers[ticker][2] = price   # 평균 매수가
                self.tickers[ticker][3] = myCoin    # 코인 보유수량
                
        sendText = f"보유코인 현황 : {self.tickers}"
        self.log(sendText)
        self.send_msg(sendText)
        
        for ticker in self.tickers:
            balance = float(KRWBlanace) / self.buyCount # 코인 갯수별 균등 매매
            self.KRWBalances[ticker] = (math.trunc(balance/1000) * 1000) - 5000
            
        sendText = f"보유 자산 : {KRWBlanace}원(코인별 매수금액 : {self.KRWBalances}"
        self.log(sendText)
        self.send_msg(sendText)
    
    def getMAline(self):
        for ticker in self.tickers:
            df = pyupbit.get_ohlcv(ticker, count=30)
            
            ma = []
            close = df['close']
            ma.append(close.rolling(window=5).mean()[-2])
            ma.append(close.rolling(window=10).mean()[-2])
        
            self.MAline[ticker] = ma
            self.tickers[ticker][1] = df['low'].min()   # 저가들 중 min 값 = 손절가
            
            time.sleep(0.1)
            
        sendText = f"이동평균 계산 : {self.MAline}"
        self.log(sendText)
        self.send_msg(sendText)
            
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
            
        
        sendText = f"목표가 계산 : {self.tickers}"
        self.log(sendText)
        self.send_msg(sendText)
        
    def send_msg(self, msg):
        with open('telepot.json', 'r') as file:
            data = json.load(file)
            api = data['api_key']
            chatId = data['id']
        bot = telepot.Bot(api)
        bot.sendMessage(chatId, msg)

    def log(self, msg):
        now = datetime.datetime.now()
        curTime = now.strftime('%Y-%m-%d %H:%M:%S')
        print(curTime + ' - ' + msg + '\n')
        file = open(self.check_fail, 'a')
        file.write(msg)
        file.close()
    
if __name__ == "__main__":
    upbitPy = UpbitPy()
    
