from pybit.unified_trading import HTTP
from datetime import datetime


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
        profitRate = 0.04
        lossRate = 0.04
        profitCount = 0
        lossCount = 0
        for i in range(self.period - 1, 0, -1):
            prevHigh = float(res['result']['list'][i][2])
            prevLow = float(res['result']['list'][i][3])
            interval = (prevHigh - prevLow) * k
            t = float(res['result']['list'][i-1][0])
            open = float(res['result']['list'][i-1][1])
            high = float(res['result']['list'][i-1][2])
            low = float(res['result']['list'][i-1][3])
            close = float(res['result']['list'][i-1][4])
            targetPrice = open + interval
            profitPrice = targetPrice * (1 + profitRate);
            lossPrice = targetPrice * (1 - lossRate);
            dt_object = datetime.fromtimestamp(t / 1000)
            formatted_time = dt_object.strftime("%Y-%m-%d %H:%M:%S")
            
            if high > targetPrice:
                if high > profitPrice:
                    balance = balance * (1 + (0.04 * leverage))
                    print(f'익절(+)(d) -> balance({balance}), open({open}), high({high}), low({low}), '
                          f'target({targetPrice}), close({close}), time({formatted_time})')
                    profitCount += 1
                    continue

                if low < lossPrice:
                    balance = balance * (1 - (0.03 * leverage))
                    print(f'손절(-)(d) -> balance({balance}), open({open}), high({high}), low({low}), '
                        f'target({targetPrice}), close({close}), time({formatted_time})')
                    lossCount += 1
                    continue
               
                pl = (close - targetPrice) / targetPrice
                balance = balance * (1 + (pl * leverage))
                if pl > 0:
                    print(f'익절(+)(f) -> balance({balance}), open({open}), high({high}), low({low}), '
                        f'target({targetPrice}), close({close}), time({formatted_time})')
                    profitCount += 1
                else:
                    print(f'손절(-)(f) -> balance({balance}), open({open}), high({high}), low({low}), '
                        f'target({targetPrice}), close({close}), time({formatted_time})')
                    lossCount += 1

        print(f'최종 balance({balance}), 수익률({(balance - initBalance) / initBalance * 100}), count({profitCount}/{lossCount})')


backTesting = BackTesting("BTCUSDT")


                
            
            
            
            
