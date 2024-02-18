import json

data = [{'symbol': 'BTCUSDT', 'tickSize': 0.1, 'qtyStep': 0.001, 
            'long': {'isCheck': True, 'target': 52466.9, 'profit': 53516.200000000004, 'loss': 51942.200000000004, 'MA': 51854.100000000006, 'average': 0, 'having': 0, 'upl': 0, 'rate': 0, 'isProfit': False}, 
            'short': {'isCheck': False, 'target': 50919.200000000004, 'profit': 49900.8, 'loss': 51428.4, 'MA': 46737.100000000006, 'average': 0, 'having': 0, 'upl': 0, 'rate': 0, 'isProfit': False}}, 
        {'symbol': 'ETHUSDT', 'tickSize': 0.01, 'qtyStep': 0.01, 
            'long': {'isCheck': True, 'target': 2832.64, 'profit': 2889.29, 'loss': 2804.31, 'MA': 2796.51, 'average': 0, 'having': 0, 'upl': 0, 'rate': 0, 'isProfit': False}, 
            'short': {'isCheck': False, 'target': 2743.88, 'profit': 2689.0, 'loss': 2771.32, 'MA': 2505.32, 'average': 0, 'having': 0, 'upl': 0, 'rate': 0, 'isProfit': False}}]

str1 = ""
for entry in data:
    for key, value in entry.items():
        if key == 'symbol':
            str1 += f"[{value}] "
            
        if key == 'long' or key == 'short':
            if value["isCheck"] == True:
                str1 += f"{key} - "
                for a,b in value.items():
                    
                    if a != "isCheck" and b > 0:
                        str1 += f"{a} : {b}, "
                
                #print(f"Symbol: {entry['symbol']}, {a}, {b}")
                
                str1 += "\n"


print(str1)


def format_float(num):
    # 소수점 이하 값이 없으면 정수로 출력
    if num == int(num):
        return str(int(num))
    else:
        return str(num)


# 예시 데이터
nums = [51919.20000000000004, 1618186.165484915615, 51919.245000000000000007]

for num in nums:
    print(format_float(num))
