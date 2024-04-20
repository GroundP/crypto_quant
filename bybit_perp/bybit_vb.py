from pybit.unified_trading import HTTP
import time
import math
import json
import datetime
import telepot
from decimal import Decimal

LONG = "LONG"
SHORT = "SHORT"
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
IS_CHECK = "isCheck"
IS_PROFIT = "isProfit"

LEVERAGE = 10

class BybitAPI():
    def __init__(self):
        now = datetime.datetime.now()
        self.logPath = 'logs/' + now.strftime('%Y-%m-%d') + '.log'
        
        self.symbols = ["BTCUSDT", "ETHUSDT"]
        self.info = [{SYMBOL: "BTCUSDT", TICK_SIZE: 0, QTY_STEP: 0,
                    LONG:  {IS_CHECK: True, TARGET_PRICE: 0, PROFIT_PRICE: 0, LOSS_PRICE: 0, MA_TARGET: 0, AVG_PRICE: 0, HAVING_QTY: 0, UPL: 0, PROFIT_RATE: 0, IS_PROFIT: False},
                    SHORT: {IS_CHECK: True, TARGET_PRICE: 0, PROFIT_PRICE: 0, LOSS_PRICE: 0, MA_TARGET: 0, AVG_PRICE: 0, HAVING_QTY: 0, UPL: 0, PROFIT_RATE: 0, IS_PROFIT: False}},
                    {SYMBOL: "ETHUSDT", TICK_SIZE: 0, QTY_STEP: 0,
                    LONG:  {IS_CHECK: True, TARGET_PRICE: 0, PROFIT_PRICE: 0, LOSS_PRICE: 0, MA_TARGET: 0, AVG_PRICE: 0, HAVING_QTY: 0, UPL: 0, PROFIT_RATE: 0, IS_PROFIT: False},
                    SHORT: {IS_CHECK: True, TARGET_PRICE: 0, PROFIT_PRICE: 0, LOSS_PRICE: 0, MA_TARGET: 0, AVG_PRICE: 0, HAVING_QTY: 0, UPL: 0, PROFIT_RATE: 0, IS_PROFIT: False}}]

        self.count = len(self.symbols)  # 매수/매도 코인 개수
        self.chkTime = int(datetime.datetime.now().strftime('%M'))
        self.USDTBalance = {}   # 코인별 매수/매도 금액

        sendText = "[bybitVB] 변동성 돌파 전략을 시작합니다."
        self.log(sendText)
        
        with open("keys.json", 'r') as file:
            data = json.load(file)
            apiKey = data["api-key"]
            secret = data["secret"]
            isMainnet = data["is-mainnet"]

        if isMainnet:
            self.bybit = HTTP(
                # endpoint="https://api.bybit.com",
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
        
        # __init__
        self.setTickSize()  # 틱사이즈, 호가단위 계산
        self.setCoinsPrice()  # 목표가, 익절가, 손절가, 이평선 계산
        self.checkMA()  # 타겟 Side 판단
        self.checkMyInfo()    # 보유 현황 확인

    def setTickSize(self):
        for info in self.info:
            res = self.session.get_instruments_info(
                category="linear",
                symbol=info[SYMBOL]
            )

            info[TICK_SIZE] = float(res['result']['list'][0]['priceFilter']['tickSize'])
            info[QTY_STEP] = float(res['result']['list'][0]['lotSizeFilter']['qtyStep'])
            
    def countDecimalDigits(self, number):
        # 숫자를 문자열로 변환하여 소수 부분을 추출
        decimal_part = str(number).split('.')[1] if '.' in str(number) else ''

        # 소수 부분의 자릿수 반환
        return len(decimal_part)

    def adjustSize(self, value, size):
        digits = self.countDecimalDigits(size)
        return round(round(value / size) * size, digits)
    
    def checkLongSide(self, nowPrice, symbol, longD, qtyStep):
        if longD[IS_CHECK] == False:
            return
        
        # 보유수량이 없는 상태이므로 목표가와 현재가격 비교 후 포지션 오픈
        if longD[HAVING_QTY] == 0:
            if longD[IS_PROFIT] == False:
                if nowPrice > longD[TARGET_PRICE]:
                    qty = self.adjustSize(self.USDTBalance[symbol] / nowPrice * LEVERAGE, qtyStep)
                    res = self.bybit.place_order(
                        category="linear",
                        symbol=symbol,
                        side="Buy",
                        orderType="Market",
                        qty=Decimal(str(qty)),
                        timeInForce="GTC",
                        positionIdx=0,
                    )

                    sendText = f"변동성 돌파! [{symbol}] Long 진입 -> 현재가: {nowPrice} > 목표가: {longD[TARGET_PRICE]}, 수량: {self.USDTBalance[symbol]}$({qty}), 응답: {res}"
                    self.log(sendText)
                    self.send_msg(sendText)

                    time.sleep(1)
                    self.checkMyInfo()
        # else:   # 보유수량이 있으므로 억절가/손절가와 현재가 비교 후 청산
        #     if nowPrice > longD[PROFIT_PRICE]:
        #         res = self.bybit.place_order(
        #             category="linear",
        #             symbol=symbol,
        #             side="Sell",
        #             orderType="Market",
        #             qty=longD[HAVING_QTY],
        #             timeInForce="GTC",
        #             positionIdx=0
        #         )

        #         longD[AVG_PRICE] = 0
        #         longD[HAVING_QTY] = 0
        #         longD[UPL] = 0
        #         longD[IS_PROFIT] = True
        #         sendText = f"익절^^ [{symbol}] Long 청산 -> 현재가: {nowPrice} > 익절가: {longD[PROFIT_PRICE]}, 수량: {longD[HAVING_QTY]}, 응답: {res}"
        #         self.log(sendText)
        #         self.send_msg(sendText)

        #         time.sleep(1)
        #         self.checkMyInfo()

        #     if nowPrice < longD[LOSS_PRICE]:
        #         res = self.bybit.place_order(
        #             category="linear",
        #             symbol=symbol,
        #             side="Sell",
        #             orderType="Market",
        #             qty=longD[HAVING_QTY],
        #             timeInForce="GTC",
        #             positionIdx=0
        #         )

        #         longD[AVG_PRICE] = 0
        #         longD[HAVING_QTY] = 0
        #         longD[UPL] = 0
        #         sendText = f"손절ㅠㅠ [{symbol}] Long 청산 -> 현재가: {nowPrice} < 손절가: {longD[LOSS_PRICE]}, 수량: {longD[HAVING_QTY]}, 응답: {res}"
        #         self.log(sendText)
        #         self.send_msg(sendText)

        #         time.sleep(1)
        #         self.checkMyInfo()
     
    def checkShortSide(self, nowPrice, symbol, shortD, qtyStep):
        if shortD[IS_CHECK] == False:
            return

        # 보유수량이 없는 상태이므로 목표가와 현재가격 비교 후 오픈 포지션
        if shortD[HAVING_QTY] == 0:
            if shortD[IS_PROFIT] == False:
                if nowPrice < shortD[TARGET_PRICE]:
                    qty = self.adjustSize(
                        self.USDTBalance[symbol] / nowPrice * LEVERAGE, qtyStep)

                    res = self.bybit.place_order(
                        category="linear",
                        symbol=symbol,
                        side="Sell",
                        orderType="Market",
                        qty=Decimal(str(qty)),
                        timeInForce="GTC",
                        positionIdx=0,
                    )

                    sendText = f"변동성 돌파! [{symbol}] Short 진입 -> 현재가: {nowPrice} < 목표가: {shortD[TARGET_PRICE]}, 수량: {self.USDTBalance[symbol]}$({qty}), 응답: {res}"
                    self.log(sendText)
                    self.send_msg(sendText)

                    time.sleep(1)
                    self.checkMyInfo()
        # else:   # 보유수량이 있으므로 익절가/손절가와 현재가 비교 후 청산
        #     if nowPrice < shortD[PROFIT_PRICE]:
        #         res = self.bybit.place_order(
        #             category="linear",
        #             symbol=symbol,
        #             side="Sell",
        #             orderType="Market",
        #             qty=shortD[HAVING_QTY],
        #             timeInForce="GTC",
        #             positionIdx=0
        #         )

        #         shortD[AVG_PRICE] = 0
        #         shortD[HAVING_QTY] = 0
        #         shortD[UPL] = 0
        #         shortD[IS_PROFIT] = True
        #         sendText = f"익절^^ [{symbol}] Short 청산 -> 현재가: {nowPrice} < 익절가: {shortD[PROFIT_PRICE]}, 수량: {shortD[HAVING_QTY]}, 응답: {res}"
        #         self.log(sendText)
        #         self.send_msg(sendText)

        #         time.sleep(1)
        #         self.checkMyInfo()

        #     if nowPrice > shortD[LOSS_PRICE]:
        #         res = self.bybit.place_order(
        #             category="linear",
        #             symbol=symbol,
        #             side="Buy",
        #             orderType="Market",
        #             qty=shortD[HAVING_QTY],
        #             timeInForce="GTC",
        #             positionIdx=0
        #         )

        #         shortD[AVG_PRICE] = 0
        #         shortD[HAVING_QTY] = 0
        #         shortD[UPL] = 0
        #         sendText = f"손절ㅠㅠ [{symbol}] Short 청산 -> 현재가: {nowPrice} > 손절가: {shortD[LOSS_PRICE]}, 수량: {shortD[HAVING_QTY]}, 응답: {res}"
        #         self.log(sendText)
        #         self.send_msg(sendText)

        #         time.sleep(1)
        #         self.checkMyInfo()
               
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
            targetPrice = self.adjustSize(targetPrice, info[TICK_SIZE])

            info[LONG][TARGET_PRICE] = targetPrice
            info[LONG][PROFIT_PRICE] = self.adjustSize(targetPrice * 1.04, info[TICK_SIZE])
            info[LONG][LOSS_PRICE] = self.adjustSize(targetPrice * 0.97, info[TICK_SIZE])

            targetPrice = float(res['result']['list'][0][1]) - k_range  # 0번째 인덱스는 당일 데이터
            targetPrice = self.adjustSize(targetPrice, info[TICK_SIZE])

            info[SHORT][TARGET_PRICE] = targetPrice
            info[SHORT][PROFIT_PRICE] = self.adjustSize(targetPrice * 0.96, info[TICK_SIZE])
            info[SHORT][LOSS_PRICE] = self.adjustSize(targetPrice * 1.03, info[TICK_SIZE])

            closePrices = []
            for elem in res['result']['list']:
                closePrices.append(float(elem[4]))

            # 이동평균선 구하기
            MA5 = self.adjustSize(sum(closePrices[:5]) / 5, info[TICK_SIZE])
            MA10 = self.adjustSize(sum(closePrices[:10]) / 10, info[TICK_SIZE])
            MA15 = self.adjustSize(sum(closePrices[:15]) / 15, info[TICK_SIZE])

            self.log(f"[{info[SYMBOL]}] MA5: {MA5}, MA10: {MA10}, MA15: {MA15}")

            longMATarget = max(MA5, MA10, MA15)
            shortMATarget = min(MA5, MA10, MA15)

            info[LONG][MA_TARGET] = longMATarget
            info[SHORT][MA_TARGET] = shortMATarget

            time.sleep(0.1)

        sendText = f"목표가 계산 -> {self.info}"
        self.log(sendText)
        self.send_msg(sendText)
           
    def checkMA(self):
        for info in self.info:
            try:
                symbol = info[SYMBOL]
                longD = info[LONG]
                shortD = info[SHORT]

                res = self.session.get_tickers(
                    category="linear",
                    symbol=symbol,
                )

                nowPrice = float(res['result']['list'][0]['lastPrice'])

                if nowPrice < longD[MA_TARGET]:
                    sendText = f"[{symbol}][long] 현재가({nowPrice})가 이평선 타겟 가격({longD[MA_TARGET]})보다 낮습니다. skip합니다."
                    longD[IS_CHECK] = False
                    self.log(sendText)
                    self.send_msg(sendText)

                    if longD[HAVING_QTY] > 0:
                        res = self.bybit.place_order(
                            category="linear",
                            symbol=symbol,
                            side="Sell",
                            orderType="Market",
                            qty=shortD[HAVING_QTY],
                            timeInForce="GTC",
                            positionIdx=0
                        )

                        sendText = f"잔여 포지션 청산 -> [{symbol}] Long 청산 -> 현재가: {nowPrice}, UPL: {longD[UPL]}, Rate: {longD[PROFIT_RATE]} 수량: {longD[HAVING_QTY]}, 응답: {res}"
                        self.log(sendText)
                        self.send_msg(sendText)

                if nowPrice > shortD[MA_TARGET]:
                    sendText = f"[{symbol}][short] 현재가({nowPrice})가 이평선 타겟 가격({shortD[MA_TARGET]})보다 높습니다. skip합니다."
                    shortD[IS_CHECK] = False
                    self.log(sendText)
                    self.send_msg(sendText)

                    if shortD[HAVING_QTY] > 0:
                        res = self.bybit.place_order(
                            category="linear",
                            symbol=symbol,
                            side="Buy",
                            orderType="Market",
                            qty=shortD[HAVING_QTY],
                            timeInForce="GTC",
                            positionIdx=0
                        )

                        sendText = f"잔여 포지션 청산 -> [{symbol}] Short 청산 -> 현재가: {nowPrice}, UPL: {shortD[UPL]}, Rate: {shortD[PROFIT_RATE]} 수량: {shortD[HAVING_QTY]}, 응답: {res}"
                        self.log(sendText)
                        self.send_msg(sendText)

            except Exception as e:
                sendText = f"예외 발생 : {e}"
                self.log(sendText)
                
    def closeAllPositions(self):
        self.checkMyInfo()

        count = 0
        for info in self.info:
            symbol = info[SYMBOL]
            longD = info[LONG]
            shortD = info[SHORT]

            res = self.session.get_tickers(
                category="linear",
                symbol=symbol,
            )

            # nowPrice = float(res['result']['list'][0]['lastPrice'])

            if longD[HAVING_QTY] > 0:
                res = self.bybit.place_order(
                    category="linear",
                    symbol=info[SYMBOL],
                    side="Sell",
                    orderType="Market",
                    qty=longD[HAVING_QTY],
                    timeInForce="GTC",
                    positionIdx=0
                )

                sendText = f"{info[SYMBOL]} Close Long 요청 -> 응답: {res}"
                self.log(sendText)
                self.send_msg(sendText)
                count += 1

                time.sleep(1)

            if shortD[HAVING_QTY] > 0:
                res = self.bybit.place_order(
                    category="linear",
                    symbol=info[SYMBOL],
                    side="Buy",
                    orderType="Market",
                    qty=shortD[HAVING_QTY],
                    timeInForce="GTC",
                    positionIdx=0
                )

                sendText = f"{info[SYMBOL]} Close Short 요청 -> 응답: {res}"
                self.log(sendText)
                self.send_msg(sendText)
                count += 1

                time.sleep(1)

        text = f"전량청산 완료({count})"
        self.log(text)
        self.send_msg(text)
        
    def checkMyInfo(self):
        res = self.bybit.get_coins_balance(
            accountType="CONTRACT"
        )

        # print(res)
        curBalance = 0
        for balance in res['result']['balance']:
            if balance['coin'] == 'USDT':
                curBalance += float(balance['transferBalance'])

        res = self.bybit.get_positions(
            category="linear",
            settleCoin="USDT",
        )

        for position in res['result']['list']:
            symbol = position['symbol']
            if symbol == 'BTCUSDT' or symbol == 'ETHUSDT':
                curBalance += float(position['positionBalance'])
                price = float(position['avgPrice'])
                size = float(position['size'])
                upl = float(position['unrealisedPnl'])
                if (position['side'] == 'Buy'):
                    for info in self.info:
                        if info[SYMBOL] == symbol:
                            info[LONG][AVG_PRICE] = price
                            info[LONG][HAVING_QTY] = size
                            info[LONG][UPL] = upl
                else:
                    for info in self.info:
                        if info[SYMBOL] == symbol:
                            info[SHORT][AVG_PRICE] = price
                            info[SHORT][HAVING_QTY] = size
                            info[SHORT][UPL] = upl

        nowPrices = []
        for info in self.info:
            res = self.session.get_tickers(
                category="linear",
                symbol=info[SYMBOL],
            )

            nowPrices.append({info[SYMBOL]: float(res['result']['list'][0]['lastPrice'])})
            balance = float(curBalance) / self.count  # 코인 갯수별 균등 매매
            self.USDTBalance[info[SYMBOL]] = (math.trunc(balance/10) * 10)

        strInfo = ""
        for info in self.info:
            for key, value in info.items():
                if key == SYMBOL:
                    strInfo += f"[{value}] "

                if key == LONG or key == SHORT:
                    if value[IS_CHECK] == True:
                        strInfo += f"{key} - "
                        for a, b in value.items():

                            if a != IS_CHECK and b != 0:
                                v = str(b)
                                strInfo += f"{a} : {v}, "

                        strInfo += "\n"

        sendText = f"현재가: {nowPrices}\n\n보유코인 현황 -> {strInfo} \n\n보유 자산 : {int(curBalance)}$(코인별 거래금액 : {self.USDTBalance})\n"
        self.log(sendText)
        self.send_msg(sendText)
        
    def log(self, msg):
        now = datetime.datetime.now()
        curTime = now.strftime('%Y-%m-%d %H:%M:%S')
        sendText = curTime + ' - ' + msg
        print(sendText)
        file = open(self.logPath, 'a', encoding='UTF8')
        file.write(sendText + '\n')
        file.close()

    # 텔레그램 메시지 전송
    def send_msg(self, msg):
        with open('telepot.json', 'r') as file:
            data = json.load(file)
            api = data['api_key']
            chatId = data['id']
        bot = telepot.Bot(api)
        bot.sendMessage(chatId, msg)

if __name__ == "__main__":
    bybitAPI = BybitAPI()

