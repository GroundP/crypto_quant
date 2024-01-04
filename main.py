import json
import pyupbit
file_path = "keys.json"

with open(file_path, 'r') as file:
    data = json.load(file)
    
apiKey = data["api-key"]
secret = data["secret"]

print(apiKey)
print(secret)

print(pyupbit.get_tickers())
