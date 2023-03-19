import requests
import configparser
import json

query_loc ='''
{
    last(serviceCodes:[]){
        latitude
        longitude
        speed
        town
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

def login(uri, credentials):
    response = requests.post(uri, data = credentials)
    return response.json()

def run_query(uri, query, status_code, headers):
    request=requests.post(uri, json={'query':query}, headers=headers)
    if request.status_code == status_code:
        print(request.content)
        return request.json
    else:
        raise Exception(f"Unexpected status code: {request.content}")

get_token = login(url_token, param_list)

token = get_token['access_token']
header={"Authorization":"Bearer " + token}

get_loc = run_query(url_loc, query_loc, 200, header)

#print(get_loc)

#print("url: " + url)
#response= requests.post(url_token, data= param_list)
#print("status code: " + str(response.status_code))




#print(response.content)
 


