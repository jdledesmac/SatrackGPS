import requests
import configparser
import time
import json

query_loc ='''
{
    last(serviceCodes:[]){
        address
        batteryLevel
        description
        deviceType
        id
        ignition
        latitude
        longitude
        locationStatus
        samePlaceMinutes
        serviceCode
        speed
        town
        generationDateGMT
        direction
        unifiedEventCode
        }
}
'''
try:
    config = configparser.ConfigParser()
    config.read('vars.conf')
    url_token = config['s_endpoint']['url_token']
    url_loc = config['s_endpoint']['url_loc']
    username = config['user_st']['client_id']
    userpass = config['user_st']['client_secret']
    access_type = config['user_st']['grant_type']

except KeyError as error:
    print("Check config file. Missing key:", error)

param_list = {"client_id": username,  "client_secret": userpass, "grant_type": access_type }

###################################################################################################################
class ExpiredToken(Exception):
    "Raised in case invalid token"
    pass

def login(uri, credentials):
    response = requests.post(uri, data = credentials)
    if response.status_code == 200:
        content = response.json()
        token = content['access_token']
        return token
    else:
        raise Exception(f"Unexpected status code: {response.content}")

def run_query(uri, query, headers):
    response=requests.post(uri, json={'query':query}, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        raise ExpiredToken
###################################################################################################################

get_token = login(url_token, param_list)
header_token={"Authorization":"Bearer " + get_token}

while True:
    try:
        get_loc = run_query(url_loc, query_loc,  header_token)
        print(get_loc)
        time.sleep(10)
    except ExpiredToken:
        get_token = login(url_token, param_list)
        header_token={"Authorization":"Bearer " + get_token}
        




