import sys
import requests
import configparser
import time
from datetime import datetime
import json
import os

class ExpiredToken(Exception):
    "Raised in case invalid token"
    pass

def resource_path(relative_path):
    #Get absolute path to resource, works for dev and for PyInstaller
        try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
            base_path = sys._MEIPASS
        except Exception:
            base_path = os.path.abspath(".")
        return os.path.join(base_path, relative_path)


query_loc ='''
{
    last(serviceCodes:[]){
        unifiedEventCode
        generationDateGMT
        ignition
        latitude
        longitude
        speed
        direction
        serviceCode
        }
}
'''

config_path=resource_path('vars.conf')
try:
    config = configparser.ConfigParser()
    config.read(config_path)
    url_token = config['s_endpoint']['url_token']
    url_loc = config['s_endpoint']['url_loc']
    username = config['user_st']['client_id']
    userpass = config['user_st']['client_secret']
    access_type = config['user_st']['grant_type']
    url_quad = config['q_endpoint']['url_quad']
    client_quad = config['q_endpoint']['client_quad']
    q_key = config['q_endpoint']['q_key']
except KeyError as error:
    print("Check config file. Missing key:", error)

param_list = {"client_id": username,  "client_secret": userpass, "grant_type": access_type }

print("Integración APIs Satrack-Quadminds V1.0")
while True:
    text = input("Presione Enter para iniciar monitoreo: ")
    if text == "":
        break
    else:
        time.sleep(1)

###################################################################################################################

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

def login(uri, credentials):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    response = requests.post(uri, data = credentials)
    if response.status_code == 200:
        content = response.json()
        token = content['access_token']
        print(f"-> {now}: Obtenido Token de acceso a Satrack exitosamente")
        return token
    else:
        raise Exception(f"-> {now}: API-Satrack, Codigo de Estatus inesperado: {response.content}")

def run_query(uri, query, headers):
    response=requests.post(uri, json={'query':query}, headers=headers)
    if response.status_code == 200:
        return response.json()
    elif response.status_code == 401:
        raise ExpiredToken
    else:
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        raise Exception(f"-> {now}: API-Satrack, Codigo de Estatus inesperado: {response.content}")
    

def run_quad(url, payload, headers):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    response = requests.post(url, json=payload, headers=headers)
    status = response.json()
    if status["status"] == 'ok':
        print(end='\x1b[2K')
        print(f"-> {now}: Monitoreando...", end="\r")
    else:    
        print(f"-> {now}: API-Quadminds, Estatus inesperado: {response.content}")
        

get_token = login(url_token, param_list)
header_token={"Authorization":"Bearer " + get_token}
header_quad ={
    "accept": "application/json",
    "content-type": "application/json",
    "x-saas-apikey": q_key
}

#MAIN LOOP

while True:
    quad_json = {"provider": client_quad, "data":[]}
    id_count=0
    now = datetime.now().strftime("%Y%m%d%H%M%S")
    try:
        get_loc = run_query(url_loc, query_loc,  header_token)
        
    except ExpiredToken:
        
        get_token = login(url_token, param_list)
        header_token={"Authorization":"Bearer " + get_token}
        time.sleep(2)
        continue
    
    events = get_loc['data']['last']
    for v in events:
        quad_json["data"].append(
            {
            "id": (now) + str(id_count), 
            "event_id": 4,
            "reportDate": str(v["generationDateGMT"]), 
            "ignition": v["ignition"], 
            "latitude": v["latitude"],  
            "longitude": v["longitude"],  
            "speed": v["speed"],  
            "course": get_course(str(v["direction"])), 
            "holder_domain": str(v["serviceCode"])
            },)
        id_count+=1
    
    run_quad(url_quad, quad_json, header_quad)
    time.sleep(60)    




