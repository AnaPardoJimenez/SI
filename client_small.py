import requests
import json
from hashlib import sha1

url_user = "http://localhost:5050/"
url_file = "http://localhost:5051/"

print()
print(" >>> EMPIEZA EL TEST DE user.py <<<")

print()
print("Creando usuario antonio con password 1234...")
print("Debe devolver OK")

url = url_user + "create_user/antonio"
headers = {"Content-Type": "application/json"}
data = {"password": "1234"}
response = requests.post(url, headers=headers, data=json.dumps(data))
print(response)
if response.status_code == 200:
    print(response.json())

print()

print("Creando usuario maria con password abduscan...")
print("Debe devolver OK")
url = url_user + "create_user/maria"
headers = {"Content-Type": "application/json"}
data = {"password": "abduscan"}
response = requests.post(url, headers=headers, data=json.dumps(data))
print(response)
if response.status_code == 200:
    print(response.json())

print()

print("Obteniendo UID de usuario antonio con password 1234...")
print("Debe devolver OK y además su UID")

url = url_user + "get_user_uid/antonio"
headers = {"Content-Type": "application/json"}
data = {"password": "1234"}
response = requests.get(url, headers=headers, data=json.dumps(data))
print(response)
if response.status_code == 200:
    print(response.json())

    UID = response.json()["UID"]
    token = sha1(UID.encode()).hexdigest()
else:
    raise Exception("Algo ha ido mal")

print()

print("Obteniendo UID de usuario maria con password abduscan...")
print("Debe devolver OK y además su UID")   

url = url_user + "get_user_uid/maria"
headers = {"Content-Type": "application/json"}
data = {"password": "abduscan"}
response = requests.get(url, headers=headers, data=json.dumps(data))
print(response)
if response.status_code == 200:
    print(response.json())

print()
print(" >>> TERMINA EL TEST DE user.py <<<")
print()
print(" >>> EMPIEZA EL TEST DE file.py <<<")

print()
print("Creando el fichero fichero_001.txt con el contenido 'texto de prueba del fichero'")
print("Debe devolver OK")

url = url_file + "create_file"
headers = {}
headers["Content-Type"] = "application/json"
headers["Authorization"] = "Bearer " + token
data = {}
data["uid"] = UID
data["filename"] = "fichero_001.txt"
data["content"] = "texto de prueba del fichero"
response = requests.post(url, headers=headers, data=json.dumps(data))
if response.status_code == 200:
    print(response.json())

print()
print(" >>> TERMINA EL TEST DE file.py <<<")
