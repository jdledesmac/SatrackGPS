import json

f =open("example.json")
data =json.load(f)

for i in data['data']['last']:
    print(i)

f.close()