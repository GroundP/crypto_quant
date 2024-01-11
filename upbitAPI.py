import pyupbit
import time
import math
import json
import datetime
import telepot

TARGET_PRICE = 0
LOSS_PRICE = 1
BUY_PRICE = 2
HAVING_QTY = 3
class UpbitPy():
    def __init__(self):
        now = datetime.datetime.now()
        self.check_fail = 'logs/' + now.strftime('%Y-%m-%d') + '.log'
        # file = open(self.check_fail, 'w', encoding="UTF8")
        # file.close()
        
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
        self.checkMA()    # 이동평균보다 현재가가 낮으면 Skip
        
        while True:
            try:
                for ticker in self.tickers:
                    nowPrice = pyupbit.get_current_price(ticker)
                    # print(f"{ticker}의 현재가 {nowPrice}")
                    
                    if self.tickers[ticker][BUY_PRICE] == 0:    # 보유수량이 없는 상태이므로 목표가와 현재가격 비교 후 매수
                        if nowPrice > int(self.tickers[ticker][TARGET_PRICE]):
                            ret = self.upbit.buy_market_order(ticker, self.KRWBalances[ticker]) # 시장가 매수(티커, 금액)
                            sendText = f"[{ticker}] 매수 -> 현재가: {nowPrice}, 목표가: {self.tickers[ticker][TARGET_PRICE]}, 수량: {self.KRWBalances[ticker]}, 응답: {ret}"
                            self.log(sendText)
                            self.send_msg(sendText)
                            
                            time.sleep(1)
                            self.checkNowMyTickers()
                    else:   # 보유수량이 있으므로 손절가와 현재가 비교 후 매도
                        if nowPrice < float(self.tickers[ticker][LOSS_PRICE]):
                            ret = self.upbit.sell_market_order(ticker, self.tickers[ticker][HAVING_QTY]) # 시장가 매도(티커, 수량)
                            self.tickers[ticker][BUY_PRICE] = 0
                            self.tickers[ticker][HAVING_QTY] = 0
                            sendText = f"[{ticker}] 매도 -> 현재가: {nowPrice}, 손절(하한)가: {self.tickers[ticker][LOSS_PRICE]}, 수량: {self.tickers[ticker][HAVING_QTY]}, 응답: {ret}"
                            self.log(sendText)
                            self.send_msg(sendText)
                            
                            time.sleep(1)
                            self.checkNowMyTickers()
                           
                nowMin = int(datetime.datetime.now().strftime('%M'))
                if nowMin > self.chkTime:
                    if nowMin == 1:
                        sendText = f"매매 대기 중 - {int(datetime.datetime.now().strftime('%H'))}"
                        self.log(sendText)
                        self.checkNowMyTickers()

                    if nowMin == 59:
                        self.chkTime = -1
                    else:
                        self.chkTime = nowMin
                
                if int(datetime.datetime.now().strftime('%H%M')) == 859:
                    sendText = "매수종료 및 전량매도"
                    self.log(sendText)
                    self.send_msg(sendText)
                    
                    self.sellAllCoin()  # 전체 매도
                    
                    quit()
                    
                time.sleep(0.15)
            except Exception as e:
                sendText = f"예외 발생 : {e}"
                self.log(sendText)
                
        
    def checkMA(self):
        for ticker in self.MAline:
            nowPrice = pyupbit.get_current_price(ticker)
            if nowPrice < max(self.MAline[ticker]):
                if self.tickers[ticker][HAVING_QTY] > 0:
                    ret = self.upbit.sell_market_order(ticker, self.tickers[ticker][HAVING_QTY])
                    sendText = f"매도 완료 -> {ret}"
                    self.log(sendText)
                    self.send_msg(sendText)
                
                del self.tickers[ticker]    # 현재가가 이동평균보다 낮을 경우 tickers에서 삭제
            
            time.sleep(0.1)
            
        if len(self.tickers) != 0:
            sendText = f"현재가 구독 시작 : {self.tickers}"
            self.log(sendText)
            self.send_msg(sendText)
        else:
            sendText = "모든 코인이 현재가 이하 -> 종료"
            self.log(sendText)
            self.send_msg(sendText)
            
            quit()

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
                self.tickers[ticker][BUY_PRICE] = price   # 평균 매수가
                self.tickers[ticker][HAVING_QTY] = myCoin  # 코인 보유수량

        nowPrices = []
        for ticker in self.tickers:
            nowPrices.append({ticker : pyupbit.get_current_price(ticker)}) 
            balance = float(KRWBlanace) / self.buyCount # 코인 갯수별 균등 매매
            self.KRWBalances[ticker] = (math.trunc(balance/1000) * 1000) - 5000
            
        sendText = f"현재가: {nowPrices}\n\n보유코인 현황 : {self.tickers}\n\n보유 자산 : {int(KRWBlanace)}원(코인별 매수금액 : {self.KRWBalances}"
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
            #self.tickers[ticker][LOSS_PRICE] = df['low'].min()   # 저가들 중 min 값 = 손절가
            
            time.sleep(0.1)
            
        sendText = f"이동평균 계산 : {self.MAline}"
        self.log(sendText)
        self.send_msg(sendText)
            
    def setCoinsPrice(self):
        for ticker in self.tickers:
            # 코인별 매수 목표가 계산
            df = pyupbit.get_ohlcv(ticker, count=2)
            print(df)
            interval = df.iloc[0]['high'] - df.iloc[0]['low']   # 0번째 인덱스는 전날 데이터
            k_range = interval * 0.5
            targetPrice = df.iloc[1]['open'] + k_range  # 1번째 인덱스는 당일 데이터
            
            self.tickers[ticker][TARGET_PRICE] = targetPrice
            self.tickers[ticker][LOSS_PRICE] = df['low'].min()
            
            time.sleep(0.1)
            
        
        sendText = f"목표가 계산 : {self.tickers}"
        self.log(sendText)
        self.send_msg(sendText)
        
    def sellAllCoin(self):
        self.checkNowMyTickers()
        
        count = 0
        for ticker in self.tickers:
            if self.tickers[ticker][HAVING_QTY] > 0:
                ret = self.upbit.sell_market_order(ticker, self.tickers[ticker][HAVING_QTY])
                sendText = f"{ticker} 매도요청 -> 응답: {ret}"
                self.log(sendText)
                self.send_msg(sendText)
                count += 1
                
                time.sleep(1)
                
        text = f"전량매도 완료({count})"
        self.log(text)
        self.send_msg(text)
        
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
        sendText = curTime + ' - ' + msg
        print(sendText)
        file = open(self.check_fail, 'a', encoding='UTF8')
        file.write(sendText + '\n')
        file.close()
    
if __name__ == "__main__":
    upbitPy = UpbitPy()
    
