import requests
import json
from hashlib import sha1

url_file = "http://localhost:5051/"
url_user = "http://localhost:5050/"

# Creamos un usuario (en caso de que no exista)
url = url_user + "create_user/antonio"
headers = {"Content-Type": "application/json"}
data = {"password": "1234"}
result = requests.post(url, headers=headers, data=json.dumps(data))

url = url_file + "create_file"
headers = {}
headers["Content-Type"] = "application/json"
headers["Authorization"] = "Bearer " + result.json()['Token']
data = {}
data["uid"] = result.json()['UID']
data["filename"] = "fichero_001.txt"
data["content"] = "texto de prueba del fichero"
response = requests.post(url, headers=headers, data=json.dumps(data))
if response.status_code == 200:
    print(response.json()['filename'])

url = url_file + "create_file"
headers = {}
headers["Content-Type"] = "application/json"
headers["Authorization"] = "Bearer " + result.json()['Token']
data = {}
data["uid"] = result.json()['UID']
data["filename"] = "fichero_002.txt"
data["content"] = "Fichero de prueba 002"
data["visibility"] = "public"
response = requests.post(url, headers=headers, data=json.dumps(data))
if response.status_code == 200:
    print(response.json()['filename'])

url = url_file + "modify_file"
headers = {}
headers["Content-Type"] = "application/json"
headers["Authorization"] = "Bearer " + result.json()['Token']
data = {}
data["uid"] = result.json()['UID']
data["filename"] = "fichero_002.txt"
data["new_content"] = "Modificacion del fichero 002"
data["visibility"] = "public"
response = requests.put(url, headers=headers, data=json.dumps(data))
if response.status_code == 200:
    print(response.json()['filename'])

url = url_file + "remove_file"
headers = {}
headers["Content-Type"] = "application/json"
headers["Authorization"] = "Bearer " + result.json()['Token']
data = {}
data["uid"] = result.json()['UID']
data["filename"] = "fichero_001.txt"
response = requests.delete(url, headers=headers, data=json.dumps(data))
if response.status_code == 200:
    print(response.json()['filename'])

url = url_file + "read_file"
headers = {}
headers["Content-Type"] = "application/json"
headers["Authorization"] = "Bearer " + result.json()['Token']
data = {}
data["uid"] = result.json()['UID']
data["filename"] = "fichero_002.txt"
response = requests.get(url, headers=headers, data=json.dumps(data))
if response.status_code == 200:
    print(response.json()['content'])

url = url_file + "list_files"
headers = {}
headers["Content-Type"] = "application/json"
headers["Authorization"] = "Bearer " + result.json()['Token']
data = {}
data["uid"] = result.json()['UID']
response = requests.get(url, headers=headers, data=json.dumps(data))
if response.status_code == 200:
    print(response.json()['files'])
