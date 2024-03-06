from pybit.unified_trading import HTTP
import time
import math
import json
import datetime
import telepot
import numpy as np
from decimal import Decimal

session = HTTP()
symbols = ["BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "XRPUSDT"]

noiseArr = []
for symbol in symbols:
    res = session.get_kline(
        category="linear",
        symbol=symbol,
        interval='D',
        limit=10,
        #start=1707955200000,
        #end=1708819200000
    )
    
    for elem in res['result']['list']:
        noiseArr.append(1 - abs(float(elem[1]) - float(elem[4])) / (float(elem[2]) - float(elem[3])))
        #print(elem[0])
    
    #print(noiseArr)
    
    print(f"[{len(noiseArr)}] symbol: {symbol}, noise: { round(np.mean(noiseArr), 2)}")
    noiseArr.clear()
