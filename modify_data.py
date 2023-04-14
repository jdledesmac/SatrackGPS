import json
from datetime import datetime

f =open("example.json")
data =json.load(f)
event = data['data']['last']
id_count=0
f.close()

def get_course(direction):
    case = {
        "Norte":0,
        "Sur":180,
        "Oriente":90,
        "Occidente":270,
        "Nor-Occidente": 315,
        "Nor-Oriente":45,
        "Sur-Oriente":135,
        "Sur-Occidente":225
        }
    return case.get(direction, "Undefined direction")
    

quad_json = {"provider": "TELLEVAMOS", "data":[]}
now = datetime.now().strftime("%Y%m%d%H%M%S")
for v in event:
    quad_json["data"].append(
        {
        "id": (now) + str(id_count), 
        "event_id": str(v["unifiedEventCode"]),
        "reportDate": str(v["generationDateGMT"]), 
        "ignition": v["ignition"], 
        "latitude": v["latitude"],  
        "longitude": v["longitude"],  
        "speed": v["speed"],  
        "course": get_course(str(v["direction"])), 
        "holder_domain": str(v["serviceCode"])
        },)
    id_count+=1



   
print(json.dumps(quad_json))


        
