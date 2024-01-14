from pybit.unified_trading import HTTP
import time
import math
import json
import datetime
import telepot

TARGET_PRICE = 0
LOSS_PRICE = 1
BUY_PRICE = 2
HAVING_QTY = 3


class BybitAPI():
    def __init__(self):
        # 목표가 계산(사이드 결정(Long, Short)
        # 이동평균 계산
        # 보유현황 확인
        # Polling하면서 매수, 매도 진행
        
        now = datetime.datetime.now()
        self.check_fail = 'logs/' + now.strftime('%Y-%m-%d') + '.log'

        # [매수/매도 목표가, 손절가, 매수/매도가, 보유수]
        self.tickers_buy = {"BTCUSDT": [0, 0, 0, 0], "ETHUSDT": [0, 0, 0, 0]}
        self.tickers_sell = {"BTCUSDT": [0, 0, 0, 0], "ETHUSDT": [0, 0, 0, 0]}
        self.buyCount = len(self.tickers_buy)  # 매수 코인 개수
        self.sellCount = len(self.tickers_sell)  # 매도 코인 개수
        self.chkTime = int(datetime.datetime.now().strftime('%M'))
        self.balances = {}   # 코인별 매수/매도 금액

        sendText = "[bybit-perp] 변동성 돌파 전략을 시작합니다."
        self.log(sendText)
        self.send_msg(sendText)

        with open("keys.json", 'r') as file:
            data = json.load(file)
            apiKey = data["api-key"]
            secret = data["secret"]


        self.bybit = HTTP(
            #endpoint="https://api.bybit.com",
            testnet=True,
            api_key=apiKey,
            api_secret=secret
        )
        
        self.session = HTTP(testnet=True)
        
        self.setCoinsPrice()    # 목표가 계산
        self.checkNowMyTickers()    # 보유 현황 확인

        while True:
            try:
                for ticker in self.tickers:
                    nowPrice = pyupbit.get_current_price(ticker)
                    # print(f"{ticker}의 현재가 {nowPrice}")

                    # 보유수량이 없는 상태이므로 목표가와 현재가격 비교 후 매수
                    if self.tickers[ticker][BUY_PRICE] == 0:
                        if nowPrice > int(self.tickers[ticker][TARGET_PRICE]):
                            ret = self.upbit.buy_market_order(
                                ticker, self.KRWBalances[ticker])  # 시장가 매수(티커, 금액)
                            sendText = f"[{ticker}] 매수 -> 현재가: {nowPrice}, 목표가: {self.tickers[ticker][TARGET_PRICE]}, 수량: {self.KRWBalances[ticker]}, 응답: {ret}"
                            self.log(sendText)
                            self.send_msg(sendText)

                            time.sleep(1)
                            self.checkNowMyTickers()
                    else:   # 보유수량이 있으므로 손절가와 현재가 비교 후 매도
                        if nowPrice < float(self.tickers[ticker][LOSS_PRICE]):
                            ret = self.upbit.sell_market_order(
                                ticker, self.tickers[ticker][HAVING_QTY])  # 시장가 매도(티커, 수량)
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


    def checkNowMyTickers(self):
        res = self.bybit.get_coins_balance(
            accountType="CONTRACT"
        )
        
        print(res)
        USDTBalance = 0
        for balance in res['result']['balance']:
            if balance['coin'] == 'USDT':
                USDTBalance += float(balance['walletBalance'])
            elif balance['coin'] == 'BTC' or balance['coin'] == 'ETH':
                if (float(balance['walletBalance']) > 0):
                    
                KRWBlanace += float(balance['balance']) * \
                    float(balance['avg_buy_price'])
                ticker = balance['unit_currency'] + '-' + balance['currency']
                price = float(balance['avg_buy_price'])
                myCoin = float(balance['balance'])
                self.tickers[ticker][BUY_PRICE] = price   # 평균 매수가
                self.tickers[ticker][HAVING_QTY] = myCoin  # 코인 보유수량

        nowPrices = []
        for ticker in self.tickers:
            nowPrices.append({ticker: pyupbit.get_current_price(ticker)})
            balance = float(KRWBlanace) / self.buyCount  # 코인 갯수별 균등 매매
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
            # self.tickers[ticker][LOSS_PRICE] = df['low'].min()   # 저가들 중 min 값 = 손절가

            time.sleep(0.1)

        sendText = f"이동평균 계산 : {self.MAline}"
        self.log(sendText)
        self.send_msg(sendText)

    def setCoinsPrice(self):
        for ticker in self.tickers_buy:
            # 코인별 매수 목표가 계산
            
            res = self.session.get_kline(
                category="linear",
                symbol=ticker,
                limit=5,
            )
            
            
            interval = float(res['result']['list'][1][2]) - float(res['result']['list'][1][3])
            k_range = interval * 0.5
            targetPrice = float(res['result']['list'][0][1]) + k_range  # 0번째 인덱스는 당일 데이터

            self.tickers_buy[ticker][TARGET_PRICE] = targetPrice
            self.tickers_buy[ticker][LOSS_PRICE] = min(float(res['result']['list'][0][3]),
                                                        float(res['result']['list'][1][3]),
                                                        float(res['result']['list'][2][3]),
                                                        float(res['result']['list'][3][3]),
                                                        float(res['result']['list'][4][3]))
            
            
            targetPrice = float(res['result']['list'][0][1]) - k_range  # 0번째 인덱스는 당일 데이터

            self.tickers_sell[ticker][TARGET_PRICE] = targetPrice
            self.tickers_sell[ticker][LOSS_PRICE] = min(float(res['result']['list'][0][2]),
                                                        float(res['result']['list'][1][2]),
                                                        float(res['result']['list'][2][2]),
                                                        float(res['result']['list'][3][2]),
                                                        float(res['result']['list'][4][2]))


            time.sleep(0.1)

        sendText = f"목표가 계산 -> 매수: {self.tickers_buy}, 매도: {self.tickers_sell}"
        self.log(sendText)
        self.send_msg(sendText)

    def sellAllCoin(self):
        self.checkNowMyTickers()

        count = 0
        for ticker in self.tickers:
            if self.tickers[ticker][HAVING_QTY] > 0:
                ret = self.upbit.sell_market_order(
                    ticker, self.tickers[ticker][HAVING_QTY])
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
    bybitAPI = BybitAPI()
