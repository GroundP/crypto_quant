from pybit.unified_trading import HTTP
import math
import json
from datetime import datetime
from decimal import Decimal


class BackTesting():
    def __init__(self, symbol):
        self.session = HTTP()
        self.symbol = symbol
        self.period = 365
        res = self.session.get_kline(
            category="linear",
            symbol=self.symbol,
            interval='D',
            limit=self.period,
        )
        
        leverage = 10
        k = 0.5
        balance = 1000.0
        initBalance = balance
        profitRate = 0.06
        lossRate = 0.05
        for i in range(self.period - 1, 0, -1):
            prevHigh = float(res['result']['list'][i][2])
            prevLow = float(res['result']['list'][i][3])
            interval = (prevHigh - prevLow) * k
            t = float(res['result']['list'][i-1][0])
            open = float(res['result']['list'][i-1][1])
            high = float(res['result']['list'][i-1][2])
            low = float(res['result']['list'][i-1][3])
            close = float(res['result']['list'][i-1][4])
            targetPrice = open - interval
            profitPrice = targetPrice * (1 - profitRate)
            lossPrice = targetPrice * (1 + lossRate)
            dt_object = datetime.fromtimestamp(t / 1000)
            formatted_time = dt_object.strftime("%Y-%m-%d %H:%M:%S")
            
            # # 이동평균선 구하기
            # mvRes = self.session.get_kline(
            #     category="linear",
            #     symbol=self.symbol,
            #     interval='D',
            #     start=t - (20 * 24 * 60 * 1000),
            #     end=t,
            # )
            
            # closePrices = []
            # for elem in mvRes['result']['list']:
            #     closePrices.append(float(elem[4]))

            # MA5 = sum(closePrices[:5]) / 5
            # MA10 = sum(closePrices[:10]) / 10
            # MA15 = sum(closePrices[:15]) / 15
            
            # if open < max(MA5, MA10, MA15):
            #     continue
            
            if low < targetPrice:
                if low < profitPrice:
                    balance = balance * (1 + (profitRate * leverage))
                    print(f'익절(+)(d) -> balance({balance}), open({open}), high({high}), low({low}), '
                          f'target({targetPrice}), close({close}), time({formatted_time})')
                    continue

                if high > lossPrice:
                    balance = balance * (1 - (lossRate * leverage))
                    print(f'손절(-)(d) -> balance({balance}), open({open}), high({high}), low({low}), '
                        f'target({targetPrice}), close({close}), time({formatted_time})')
                    continue
               
                pl = (targetPrice - close) / targetPrice
                balance = balance * (1 + (pl * leverage))
                if pl > 0:
                    print(f'익절(+)(f) -> balance({balance}), open({open}), high({high}), low({low}), '
                        f'target({targetPrice}), close({close}), time({formatted_time})')
                else:
                    print(f'손절(-)(f) -> balance({balance}), open({open}), high({high}), low({low}), '
                        f'target({targetPrice}), close({close}), time({formatted_time})')
                
        print(f'최종 balance({balance}), 수익률({(balance - initBalance) / initBalance * 100})')


backTesting = BackTesting("BTCUSDT")


                
            
            
            
            
