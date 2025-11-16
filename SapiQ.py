import sys
import requests
import configparser
import time
from datetime import datetime
import os


class ExpiredToken(Exception):
    '''Raised in case of expired token'''
    pass

def resource_path(relative_path):
    #Get absolute path to resource, works for dev and for PyInstaller
        try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
            base_path = sys._MEIPASS
        except Exception:
            base_path = os.path.abspath(".")
        return os.path.join(base_path, relative_path)

#GraphQL query that requests last known location for all devices
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
        temperature
        }
}
'''
#Read the configuration file and build the credentials payload
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

##INITIAL MESSAGE
print("Integración API Quadminds V1.0")
print(f"Cliente: {client_quad}")
time.sleep(1)


#FUNCTIONS: 
def get_course(direction):
    '''Convert cardinal direction to degrees
        Args:
            direction (str): Cardinal direction (e.g., "Norte", "Sur", etc.)
        Returns:
            int: Corresponding degree value or "Undefined direction" if not found
    '''
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

def login_satrack(uri, credentials):
    '''Obtain OAuth token from Satrack API
        Args:
            uri (str): The URL to request the token from
            credentials (dict): The credentials payload for the token request
        Returns:
            str: The access token if the request is successful
        Raises:
            Exception: If the request fails or returns an unexpected status code
        '''
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    response = requests.post(uri, data = credentials)
    if response.status_code == 200:
        content = response.json()
        token = content['access_token']
        return token
    else:
        raise Exception(f"-> {now}: API-Satrack, Codigo de Estatus inesperado: {response.content}")

def run_satrack_query(uri, query, headers):
    '''Run a GraphQL query against the Satrack API
        Args:
            uri (str): The URL to send the query to
            query (str): The GraphQL query string
            headers (dict): The headers for the request, including authorization
        Returns:
            dict: The JSON response from the API if the request is successful'''
    response=requests.post(uri, json={'query':query}, headers=headers)
    if response.status_code == 200:
        return response.json()
    elif response.status_code == 401:
        raise ExpiredToken
    else:
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        raise Exception(f"-> {now}: API-Satrack, Codigo de Estatus inesperado: {response.content}")
    

def run_quad(url, payload, headers):
    '''Send data to Quadminds API
        Args:
            url (str): The URL to send the data to
            payload (dict): The data payload to send
            headers (dict): The headers for the request, including authorization
        Returns:
            None
        '''
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    response = requests.post(url, json=payload, headers=headers)
    status = response.json()
    if status["status"] == 'ok':
        #print(end='\x1b[2K')
        print(f"-> {now}: Monitoreando...", end="\r")
    else:
        print(f"-> {now}: API-Quadminds, Estatus inesperado: {response.content}")
        
#INITIAL TOKEN REQUEST
get_token = login_satrack(url_token, param_list)
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
    #Try to obtain last known locations from Satrack
    try:
        location = run_satrack_query(url_loc, query_loc,  header_token)
    #Update token in case of expiration
    except ExpiredToken:
        get_token = login_satrack(url_token, param_list)
        header_token={"Authorization":"Bearer " + get_token}
        time.sleep(2)
        continue
    #Build payload for Quadminds
    events = location['data']['last']
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
            "holder_domain": str(v["serviceCode"]),
            "temperature": v["temperature"]
            },)
        id_count+=1
    #Send data to Quadminds
    run_quad(url_quad, quad_json, header_quad)
    time.sleep(60)    






