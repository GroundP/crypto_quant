from pybit.unified_trading import HTTP
import time
import math
import json
import datetime
import telepot
from decimal import Decimal

LONG = "long"
SHORT = "short"
SYMBOL = "symbol"

TARGET_PRICE = "target"
PROFIT_PRICE = "profit"
LOSS_PRICE = "loss"
AVG_PRICE = "average"
HAVING_QTY = "having"
UPL = "upl"
TICK_SIZE = "tickSize"
QTY_STEP = "qtyStep"
PROFIT_RATE = "rate"
MA_TARGET = "MA"

LEVERAGE = 10


class BybitAPI():
    def __init__(self):
        # 목표가 계산(사이드 결정(Long, Short)
        # 이동평균 계산
        # 보유현황 확인
        # Polling하면서 매수, 매도 진행
        
        now = datetime.datetime.now()
        self.check_fail = 'logs/' + now.strftime('%Y-%m-%d') + '.log'

        self.symbols = ["BTCUSDT", "ETHUSDT"]
        self.info = [{SYMBOL: "BTCUSDT", TICK_SIZE: 0, QTY_STEP: 0,
                      LONG:  {TARGET_PRICE: 0, PROFIT_PRICE: 0, LOSS_PRICE: 0, MA_TARGET: 0, HAVING_QTY: 0, UPL: 0, PROFIT_RATE : 0},
                      SHORT: {TARGET_PRICE: 0, PROFIT_PRICE: 0, LOSS_PRICE: 0, MA_TARGET: 0, HAVING_QTY: 0, UPL: 0, PROFIT_RATE : 0}},
                     {SYMBOL: "ETHUSDT", TICK_SIZE: 0, QTY_STEP: 0,
                      LONG: { TARGET_PRICE: 0, PROFIT_PRICE: 0, LOSS_PRICE: 0, MA_TARGET: 0, HAVING_QTY: 0, UPL: 0, PROFIT_RATE : 0},
                      SHORT: {TARGET_PRICE: 0, PROFIT_PRICE: 0, LOSS_PRICE: 0, MA_TARGET: 0, HAVING_QTY: 0, UPL: 0, PROFIT_RATE : 0}}]
        
        # [매수/매도 목표가, 손절가, 매수/매도가, 보유수, UPL, 틱사이즈, 수량단위]
        self.count = len(self.symbols)  # 매수/매도 코인 개수
        self.chkTime = int(datetime.datetime.now().strftime('%M'))
        self.USDTBalance = {}   # 코인별 매수/매도 금액

        sendText = "[bybit-perp] 변동성 돌파 전략을 시작합니다."
        self.log(sendText)
        self.send_msg(sendText)

        with open("keys.json", 'r') as file:
            data = json.load(file)
            apiKey = data["api-key"]
            secret = data["secret"]
            isMainnet = data["is-mainnet"]

        if isMainnet:
            self.bybit = HTTP(
                #endpoint="https://api.bybit.com",
                api_key=apiKey,
                api_secret=secret
            )
        else:
            self.bybit = HTTP(
                # endpoint="https://api-testnet.bybit.com",
                testnet=True,
                api_key=apiKey,
                api_secret=secret
            )
            
        self.session = HTTP()
        
        self.setTickSize()  # 틱사이즈, 호가단위 계산
        self.setCoinsPrice()    # 목표가, 익절가, 손절가, 이평선 계산
        self.checkNowMyTickers()    # 보유 현황 확인
        
        # while True:
        #     try:
        #         for ticker in self.tickers_buy:
        #             res = self.session.get_tickers(
        #                 category="linear",
        #                 symbol=ticker,
        #             )
                    
        #             nowPrice = float(res['result']['list'][0]['lastPrice'])

        #             # 보유수량이 없는 상태이므로 목표가와 현재가격 비교 후 포지션 오픈
        #             if self.tickers_buy[ticker][AVG_PRICE] == 0:
        #                 if nowPrice > int(self.tickers_buy[ticker][TARGET_PRICE]):
        #                     # 레버리지
        #                     qty = round(self.USDTBalance[ticker] / nowPrice /
        #                                 self.tickers_buy[ticker][QTY_STEP] * LEVERAGE) * self.tickers_buy[ticker][QTY_STEP]
        #                     res = self.bybit.place_order(
        #                         category="linear",
        #                         symbol=ticker,
        #                         side="Buy",
        #                         orderType="Market",
        #                         qty=Decimal(str(qty)),
        #                         timeInForce="GTC",
        #                         positionIdx=0,
        #                     )
                            
        #                     sendText = f"변동성 돌파! [{ticker}] Long 진입 -> 현재가: {nowPrice} > 목표가: {self.tickers_buy[ticker][TARGET_PRICE]}, 수량: {self.USDTBalance[ticker]}$({qty}), 응답: {res}"
        #                     self.log(sendText)
        #                     self.send_msg(sendText)

        #                     time.sleep(1)
        #                     self.checkNowMyTickers()
        #             else:   # 보유수량이 있으므로 손절가와 현재가 비교 후 청산
        #                 if nowPrice < float(self.tickers_buy[ticker][LOSS_PRICE]):
        #                     res = self.bybit.place_order(
        #                         category="linear",
        #                         symbol=ticker,
        #                         side="Sell",
        #                         orderType="Market",
        #                         qty=self.tickers_buy[ticker][HAVING_QTY],
        #                         timeInForce="GTC",
        #                         positionIdx=0,
        #                     )
                            
        #                     self.tickers_buy[ticker][AVG_PRICE] = 0
        #                     self.tickers_buy[ticker][HAVING_QTY] = 0
        #                     self.tickers_buy[ticker][UPL] = 0
        #                     sendText = f"변동성 돌파! [{ticker}] Long 청산 -> 현재가: {nowPrice} < 손절가: {self.tickers_buy[ticker][LOSS_PRICE]}, 수량: {self.tickers_buy[ticker][HAVING_QTY]}, 응답: {res}"
        #                     self.log(sendText)
        #                     self.send_msg(sendText)

        #                     time.sleep(1)
        #                     self.checkNowMyTickers()
                            
                            
        #             # 보유수량이 없는 상태이므로 목표가와 현재가격 비교 후 오픈 포지션
        #             if self.tickers_sell[ticker][AVG_PRICE] == 0:
        #                 if nowPrice < int(self.tickers_sell[ticker][TARGET_PRICE]):
        #                     # 레버리지
        #                     qty = round(self.USDTBalance[ticker] / nowPrice /
        #                                 self.tickers_sell[ticker][QTY_STEP] * LEVERAGE) * self.tickers_sell[ticker][QTY_STEP]
        #                     res = self.bybit.place_order(
        #                         category="linear",
        #                         symbol=ticker,
        #                         side="Sell",
        #                         orderType="Market",
        #                         qty=Decimal(str(qty)),
        #                         timeInForce="GTC",
        #                         positionIdx=0,
        #                     )

        #                     sendText = f"변동성 돌파! [{ticker}] Short 진입 -> 현재가: {nowPrice} < 목표가: {self.tickers_sell[ticker][TARGET_PRICE]}, 수량: {self.USDTBalance[ticker]}$({qty}), 응답: {res}"
        #                     self.log(sendText)
        #                     self.send_msg(sendText)

        #                     time.sleep(1)
        #                     self.checkNowMyTickers()
        #             else:   # 보유수량이 있으므로 손절가와 현재가 비교 후 청산
        #                 if nowPrice > float(self.tickers_sell[ticker][LOSS_PRICE]):
        #                     res = self.bybit.place_order(
        #                         category="linear",
        #                         symbol=ticker,
        #                         side="Buy",
        #                         orderType="Market",
        #                         qty=self.tickers_sell[ticker][HAVING_QTY],
        #                         timeInForce="GTC",
        #                         positionIdx=0,
        #                     )

        #                     self.tickers_sell[ticker][AVG_PRICE] = 0
        #                     self.tickers_sell[ticker][HAVING_QTY] = 0
        #                     self.tickers_sell[ticker][UPL] = 0
        #                     sendText = f"변동성 돌파! [{ticker}] Short 청산 -> 현재가: {nowPrice} > 손절가: {self.tickers_sell[ticker][LOSS_PRICE]}, 수량: {self.tickers_sell[ticker][HAVING_QTY]}, 응답: {res}"
        #                     self.log(sendText)
        #                     self.send_msg(sendText)

        #                     time.sleep(1)
        #                     self.checkNowMyTickers()

        #         nowMin = int(datetime.datetime.now().strftime('%M'))
        #         if nowMin > self.chkTime:
        #             if nowMin == 1:
        #                 sendText = f"매매 대기 중 - {int(datetime.datetime.now().strftime('%H'))}"
        #                 self.log(sendText)
        #                 self.checkNowMyTickers()

        #             if nowMin == 59:
        #                 self.chkTime = -1
        #             else:
        #                 self.chkTime = nowMin

        #         if int(datetime.datetime.now().strftime('%H%M')) == 859:
        #             sendText = "거래종료 및 전량청산"
        #             self.log(sendText)
        #             self.send_msg(sendText)

        #             self.closeAllCoin()  # 전체 매도

        #             quit()

        #         time.sleep(0.15)
        #     except Exception as e:
        #         sendText = f"예외 발생 : {e}"
        #         self.log(sendText)


    def adjustTickSize(self, value, tickSize):
        return round(value / tickSize) * tickSize

    def setTickSize(self):
        for info in self.info:
            res = self.session.get_instruments_info(
                category="linear",
                symbol=info[SYMBOL]
            )
            
            info[TICK_SIZE] = float(res['result']['list'][0]['priceFilter']['tickSize'])
            info[QTY_STEP] = float(res['result']['list'][0]['lotSizeFilter']['qtyStep'])
    
    def checkNowMyTickers(self):
        res = self.bybit.get_coins_balance(
            accountType="CONTRACT"
        )
        
        #print(res)
        USDTBalance = 0
        for balance in res['result']['balance']:
            if balance['coin'] == 'USDT':
                USDTBalance += float(balance['transferBalance'])
                
        res = self.bybit.get_positions(
            category="linear",
            settleCoin="USDT",
        )
        
        for position in res['result']['list']:
            symbol = position['symbol']
            if symbol == 'BTCUSDT' or symbol == 'ETHUSDT':
                USDTBalance += float(position['positionBalance'])
                price = float(position['avgPrice'])
                size = float(position['size'])
                upl = float(position['unrealisedPnl'])
                if (position['side'] == 'Buy'):
                    for info in self.info:
                        if info[SYMBOL] == symbol:
                            info[LONG]["average"] = price
                            info[LONG][HAVING_QTY] = size
                            info[LONG][UPL] = upl
                else:
                    for info in self.info:
                        if info[SYMBOL] == symbol:
                            info[SHORT]["average"] = price
                            info[SHORT][HAVING_QTY] = size
                            info[SHORT][UPL] = upl

        nowPrices = []
        for info in self.info:
            res = self.session.get_tickers(
                category="linear",
                symbol=info[SYMBOL],
            )
            
            nowPrices.append({info[SYMBOL]: float(res['result']['list'][0]['lastPrice'])})
            balance = float(USDTBalance) / self.count  # 코인 갯수별 균등 매매
            self.USDTBalance[info[SYMBOL]] = (math.trunc(balance/10) * 10)

        # myCoin = {}
        # myCoin["BTCUSDT"] = {}
        # myCoin["BTCUSDT"]["LONG"] = self.info[SYMBOL][:-2]
        # myCoin["BTCUSDT"]["SHORT"] = self.tickers_sell["BTCUSDT"][:-2]
        # myCoin["ETHUSDT"] = {}
        # myCoin["ETHUSDT"]["LONG"] = self.tickers_buy["ETHUSDT"][:-2]
        # myCoin["ETHUSDT"]["SHORT"] = self.tickers_sell["ETHUSDT"][:-2]
        # sendText = f"현재가: {nowPrices}\n\n보유코인 현황 -> {myCoin} \n\n보유 자산 : {int(USDTBalance)}$(코인별 거래금액 : {self.USDTBalance})\n"
        sendText = f"현재가: {nowPrices}\n\n보유코인 현황 -> {self.info} \n\n보유 자산 : {int(USDTBalance)}$(코인별 거래금액 : {self.USDTBalance})\n"
        self.log(sendText)
        self.send_msg(sendText)

    def setCoinsPrice(self):
        for info in self.info:
            # 코인별 매수 목표가 계산
            
            res = self.session.get_kline(
                category="linear",
                symbol=info[SYMBOL],
                interval='D',
                limit=20,
            )
            
            
            interval = float(res['result']['list'][1][2]) - float(res['result']['list'][1][3])
            k_range = interval * 0.5
            targetPrice = float(res['result']['list'][0][1]) + k_range  # 0번째 인덱스는 당일 데이터
            targetPrice = int(targetPrice / self.info[TICK_SIZE]) * self.info[TICK_SIZE]

            self.info[LONG][TARGET_PRICE] = targetPrice
            
            targetPrice = float(res['result']['list'][0][1]) - k_range  # 0번째 인덱스는 당일 데이터
            targetPrice = int(targetPrice / self.info[TICK_SIZE]) * self.info[TICK_SIZE]

            self.info[SHORT][TARGET_PRICE] = targetPrice


            closePrices = []
            for elem in res['result']['list']:
                closePrices.insert(elem[4])
            
                
            # 이동평균선 구하기
            MA5 = self.adjustTickSize(sum(closePrices[:5]) / 5, info[TICK_SIZE])
            MA10 = self.adjustTickSize(sum(closePrices[:10]) / 10, info[TICK_SIZE])
            MA20 = self.adjustTickSize(sum(closePrices[:20]) / 20, info[TICK_SIZE])
            
            self.log(f"MA5: {MA5}, MA10: {MA10}, MA20: {MA20}")
            
            longMATarget = max(MA5, MA10, MA20)
            shortMATarget = min(MA5, MA10, MA20)
            
            self.info[LONG][MA_TARGET] = longMATarget
            self.info[SHORT][MA_TARGET] = shortMATarget

            time.sleep(0.1)

        sendText = f"목표가 계산 -> {self.info}"
        self.log(sendText)
        self.send_msg(sendText)

    def closeAllCoin(self):
        self.checkNowMyTickers()

        count = 0
        for ticker in self.tickers_buy:
            if self.tickers_buy[ticker][HAVING_QTY] > 0:
                res = self.bybit.place_order(
                    category="linear",
                    symbol=ticker,
                    side="Sell",
                    orderType="Market",
                    qty=self.tickers_buy[ticker][HAVING_QTY],
                    timeInForce="GTC",
                    positionIdx=0,
                    reduceOnly=True
                )
                
                sendText = f"{ticker} Close Long 요청 -> 응답: {res}"
                self.log(sendText)
                self.send_msg(sendText)
                count += 1

                time.sleep(1)
                
            if self.tickers_sell[ticker][HAVING_QTY] > 0:
                res = self.bybit.place_order(
                    category="linear",
                    symbol=ticker,
                    side="Buy",
                    orderType="Market",
                    qty=self.tickers_sell[ticker][HAVING_QTY],
                    timeInForce="GTC",
                    positionIdx=0,
                    reduceOnly=True
                )

                sendText = f"{ticker} Close Short 요청 -> 응답: {res}"
                self.log(sendText)
                self.send_msg(sendText)
                count += 1

                time.sleep(1)

        text = f"전량청산 완료({count})"
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
