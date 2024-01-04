import pyupbit
import time
import math
import datetime
import telepot

class UpbitPy():
    def __init__(self):
        now = datetime.datetime.now()
        self.check_fail = 'logs/' + now.strftime('%Y-%m-%d_%H%M%S') + '.log'
        file = open(self.check_fail, 'w', encoding="UTF8")
        file.close()
        
if __name__ == "__main__":
    upbitPy = UpbitPy()
    
        