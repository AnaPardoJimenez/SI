import requests
import json
import time
import os
import pytest

# Base URL for the server (assuming it's running locally)
USER_URL = "http://0.0.0.0:5050"
FILE_URL = "http://0.0.0.0:5051"

# Test data
TEST_USERNAME = "testuser"
TEST_PASSWORD = "testpass"
TEST_NEW_PASSWORD = "newtestpass"
TEST_NEW_USERNAME = "newtestuser"
TEST_USERTOKEN = None
TEST_USERUID = None
TEST_UNAUTHORIZED_TOKEN = None
TEST_UNAUTHORIZED_UID = None
TEST_UNAUTHORIZED_USERNAME = "unauthorized_user"

# Paths to resources (for cleanup)
USERS_FILE = "resources/users.txt"
USER_LIB_DIR = "resources/files/"

# Helper function to clean up test files before and after tests
def cleanup_files():
    # Remove the users file if it exists
    if os.path.exists(USERS_FILE) and os.path.isfile(USERS_FILE):
        os.remove(USERS_FILE)
    # Remove only .txt files inside the user library directory, but not the directory itself
    if os.path.exists(USER_LIB_DIR) and os.path.isdir(USER_LIB_DIR):
        for file in os.listdir(USER_LIB_DIR):
            full_path = os.path.join(USER_LIB_DIR, file)
            if os.path.isfile(full_path) and file.endswith(".txt"):
                os.remove(full_path)

@pytest.fixture(scope="module", autouse=True)
def setup_teardown():
    # Clean up before tests
    cleanup_files()
    # Wait a bit for server to be ready (if needed)
    time.sleep(1)
    yield
    # Clean up after tests
    #cleanup_files()

def test_create_user():
    global TEST_USERTOKEN, TEST_USERUID
    url = f"{USER_URL}/create_user/{TEST_USERNAME}"
    headers = {"Content-Type": "application/json"}
    payload = {"password": TEST_PASSWORD}
    response = requests.post(url, headers=headers, data=json.dumps(payload))

    TEST_USERTOKEN = response.json()['Token']
    TEST_USERUID = response.json()['UID']
    
    # Al crear un usuario nuevo, debe devolver 201 Created
    print("\n    Probando: Funcionamiento normal")
    assert response.status_code == 201, f"Expected 201, got {response.status_code}"
    data = response.json()
    assert data["status"] == "OK"
    assert data["username"] == TEST_USERNAME
    assert "UID" in data

    response = requests.post(url, headers=headers, data=json.dumps(payload))
    # Al no crear un usuario nuevo, debe devolver 200 OK
    print("    Probando: Usuario ya existe -> Hace log in")
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    data = response.json()
    assert data["status"] == "OK"
    assert data["username"] == TEST_USERNAME
    assert "UID" in data

    response = requests.post(url, headers=headers)
    # Al no haber data, debe devolver 400 Bad request
    print("    Probando: Sin body")
    assert response.status_code == 400
    data = response.json()
    assert data["message"] == 'Body JSON requerido'

    payload = {}  # No password
    response = requests.post(url, headers=headers, data=json.dumps(payload))
    # Al no haber campo de contraseña, debe devolver 400 Bad request
    print("    Probando: Sin campo de contraseña en body")
    assert response.status_code == 400
    data = response.json()
    assert data["message"] == 'Body JSON no contiene la clave "password"'

    payload = {"password": "INCORRECT_PASSWORD"}
    response = requests.post(url, headers=headers, data=json.dumps(payload))
    # Al ser contraseña incorrecta, debe devolver 401 Unauthorized
    print("    Probando: Contraseña incorrecta")
    assert response.status_code == 401
    data = response.json()
    assert data["message"] == 'Credenciales incorrectas'

def test_login_user():
    url = f"{USER_URL}/login/{TEST_USERNAME}"
    headers = {"Content-Type": "application/json"}
    payload = {"password": TEST_PASSWORD}
    response = requests.get(url, headers=headers, data=json.dumps(payload))
    #
    print("\n    Probando: Funcionamiento normal")
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    data = response.json()
    assert data["status"] == "OK"
    assert "UID" in data

    response = requests.get(url, headers=headers)
    # Al no haber data, debe devolver 400 Bad request
    print("    Probando: Sin body")
    assert response.status_code == 400
    data = response.json()
    assert data["message"] == 'Body JSON requerido'

    payload = {}  # No password
    response = requests.get(url, headers=headers, data=json.dumps(payload))
    # Al no haber campo de contraseña, debe devolver 400 Bad request
    print("    Probando: Sin campo de constraseña en body")
    assert response.status_code == 400
    data = response.json()
    assert data["message"] == 'Body JSON no contiene la clave "password"'
    
    payload = {"password": "wrongpass"}
    response = requests.get(url, headers=headers, data=json.dumps(payload))
    #
    print("    Probando: Contraseña incorrecta")
    assert response.status_code == 401
    data = response.json()
    assert data["message"] == 'Credenciales incorrectas'

def test_get_user_id():
    url = f"{USER_URL}/get_user_id/{TEST_USERNAME}"
    headers = {"Content-Type": "application/json"}
    response = requests.get(url, headers=headers)
    # 
    print("\n    Probando: Funcionamiento normal")
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    data = response.json()
    assert data["status"] == "OK"
    assert "UID" in data
    
    print("    Probando: Usuario no existente")
    url = f"{USER_URL}/get_user_id/nonexistentuser"
    response = requests.get(url, headers=headers)
    assert response.status_code == 404

def test_change_password():
    url = f"{USER_URL}/change_pass/{TEST_USERNAME}"
    payload = {"password": TEST_PASSWORD, "new_password": TEST_NEW_PASSWORD}
    headers = {"Content-Type": "application/json"}
    response = requests.post(url, headers=headers, data=json.dumps(payload))
    
    print("\n    Probando: Funcionamiento normal")
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    data = response.json()
    assert data["status"] == "OK"
    # Verify by logging in with new password
    login_url = f"{USER_URL}/login/{TEST_USERNAME}"
    login_payload = {"password": TEST_NEW_PASSWORD}
    login_response = requests.get(login_url, headers=headers, data=json.dumps(login_payload))
    assert login_response.status_code == 200

    response = requests.post(url, headers=headers)
    # Al no haber data, debe devolver 400 Bad request
    print("    Probando: Sin body")
    assert response.status_code == 400
    data = response.json()
    assert data["message"] == 'Body JSON requerido'

    payload = {"new_password": TEST_NEW_PASSWORD}  # No password
    response = requests.post(url, headers=headers, data=json.dumps(payload))
    # Al no haber campo de contraseña, debe devolver 400 Bad request
    print("    Probando: Sin campo de constraseña en body")
    assert response.status_code == 400
    data = response.json()
    assert data["message"] == 'Body JSON no contiene la clave "password"'

    payload = {"password": TEST_PASSWORD}  # No new password
    response = requests.post(url, headers=headers, data=json.dumps(payload))
    # Al no haber campo de contraseña, debe devolver 400 Bad request
    print("    Probando: Sin campo de nueva constraseña en body")
    assert response.status_code == 400
    data = response.json()
    assert data["message"] == 'Body JSON no contiene la clave "new_password"'
    
    payload = {"password": TEST_PASSWORD, "new_password": TEST_NEW_PASSWORD}
    response = requests.post(url, headers=headers, data=json.dumps(payload))
    # 
    print("    Probando: Contraseña incorrecta")
    assert response.status_code == 401, f"Expected 401, got {response.status_code}"
    data = response.json()
    assert data["message"] == "Credenciales incorrectas"
    
    url = f"{USER_URL}/change_pass/usuario_inexistente"
    payload = {"password": "wrong", "new_password": "new"}
    response = requests.post(url, headers=headers, data=json.dumps(payload))
    # El usuario no existe, debe devolver 404 Not found
    print("    Probando: Usuario no existente")
    assert response.status_code == 404
    data = response.json()
    assert data["message"] == "Usuario no encontrado"

def test_change_username():
    url = f"{USER_URL}/change_username/{TEST_USERNAME}"
    payload = {"password": TEST_NEW_PASSWORD, "new_username": TEST_NEW_USERNAME}
    headers = {"Content-Type": "application/json"}
    response = requests.post(url, headers=headers, data=json.dumps(payload))
    
    print("\n    Probando: Funcionamiento normal")
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    data = response.json()
    assert data["status"] == "OK"

    # Verify by getting new username
    get_url = f"{USER_URL}/get_user_id/{TEST_NEW_USERNAME}"
    headers = {"Content-Type": "application/json"}
    get_response = requests.get(get_url, headers=headers)
    assert get_response.status_code == 200

    response = requests.post(url, headers=headers)
    # Al no haber data, debe devolver 400 Bad request
    print("    Probando: Sin body")
    assert response.status_code == 400
    data = response.json()
    assert data["message"] == 'Body JSON requerido'

    payload = {"new_username": TEST_NEW_USERNAME}  # No password
    response = requests.post(url, headers=headers, data=json.dumps(payload))
    # Al no haber campo de contraseña, debe devolver 400 Bad request
    print("    Probando: Sin campo de constraseña en body")
    assert response.status_code == 400
    data = response.json()
    assert data["message"] == 'Body JSON no contiene la clave "password"'

    payload = {"password": TEST_NEW_PASSWORD}  # No new username
    response = requests.post(url, headers=headers, data=json.dumps(payload))
    # Al no haber campo de contraseña, debe devolver 400 Bad request
    print("    Probando: Sin campo de nuevo nombre de usuario en body")
    assert response.status_code == 400
    data = response.json()
    assert data["message"] == 'Body JSON no contiene la clave "new_username"'
    
    url = f"{USER_URL}/change_username/usuario_inexistente"
    payload = {"password": TEST_NEW_PASSWORD, "new_username": "new"}
    response = requests.post(url, headers=headers, data=json.dumps(payload))
    # El usuario no existe, debe devolver 404 Not found
    print("    Probando: Usuario no existente")
    assert response.status_code == 404
    data = response.json()
    assert data["message"] == "Usuario no encontrado"
    
    url = f"{USER_URL}/change_username/{TEST_NEW_USERNAME}"
    payload = {"password": TEST_PASSWORD, "new_username": TEST_NEW_USERNAME}
    response = requests.post(url, headers=headers, data=json.dumps(payload))
    # 
    print("    Probando: Contraseña incorrecta")
    assert response.status_code == 401, f"Expected 401, got {response.status_code}"
    data = response.json()
    assert data["message"] == "Credenciales incorrectas"

# File tests
def test_create_private_file():
    url = FILE_URL + "/create_file"
    headers = {"Content-Type": "application/json", "Authorization": "Bearer " + TEST_USERTOKEN}
    data = {"uid": TEST_USERUID, "filename": "fichero_001.txt", "content": "texto de prueba del fichero"}
    response = requests.post(url, headers=headers, data=json.dumps(data))
    assert response.status_code == 200

def test_create_public_file():
    url = FILE_URL + "/create_file"
    headers = {}
    headers["Content-Type"] = "application/json"
    headers["Authorization"] = "Bearer " + TEST_USERTOKEN
    data = {}
    data["uid"] = TEST_USERUID
    data["filename"] = "fichero_002.txt"
    data["content"] = "Fichero de prueba 002"
    data["visibility"] = "public"
    response = requests.post(url, headers=headers, data=json.dumps(data))
    assert response.status_code == 200

def test_modify_file():
    url = FILE_URL + "/modify_file"
    headers = {}
    headers["Content-Type"] = "application/json"
    headers["Authorization"] = "Bearer " + TEST_USERTOKEN
    data = {}
    data["uid"] = TEST_USERUID
    data["filename"] = "fichero_002.txt"
    data["new_content"] = "Modificacion del fichero 002"
    data["visibility"] = "public"
    response = requests.put(url, headers=headers, data=json.dumps(data))
    assert response.status_code == 200

def test_read_file():
    url = FILE_URL + "/read_file"
    headers = {}
    headers["Content-Type"] = "application/json"
    headers["Authorization"] = "Bearer " + TEST_USERTOKEN
    data = {}
    data["uid"] = TEST_USERUID
    data["filename"] = "fichero_002.txt"
    response = requests.get(url, headers=headers, data=json.dumps(data))
    assert response.status_code == 200

def test_list_files():
    url = FILE_URL + "/list_files"
    headers = {}
    headers["Content-Type"] = "application/json"
    headers["Authorization"] = "Bearer " + TEST_USERTOKEN
    data = {}
    data["uid"] = TEST_USERUID
    response = requests.get(url, headers=headers, data=json.dumps(data))
    assert response.status_code == 200

def test_unauthorized_private_file_read():
    global TEST_UNAUTHORIZED_TOKEN, TEST_UNAUTHORIZED_UID
    url = f"{USER_URL}/create_user/{TEST_UNAUTHORIZED_USERNAME}"
    headers = {"Content-Type": "application/json"}
    data = {"password": "password"}
    response = requests.post(url, headers=headers, data=json.dumps(data))

    TEST_UNAUTHORIZED_TOKEN = response.json()['Token']
    TEST_UNAUTHORIZED_UID = response.json()['UID']

    url = FILE_URL + "/read_file"
    headers = {}
    headers["Content-Type"] = "application/json"
    headers["Authorization"] = "Bearer " + TEST_UNAUTHORIZED_TOKEN
    data = {}
    data["uid"] = TEST_USERUID
    data["filename"] = "fichero_001.txt"
    response = requests.get(url, headers=headers, data=json.dumps(data))
    
    assert response.status_code == 403

def test_unauthorized_public_file_read():
    url = FILE_URL + "/read_file"
    headers = {}
    headers["Content-Type"] = "application/json"
    headers["Authorization"] = "Bearer " + TEST_UNAUTHORIZED_TOKEN
    data = {}
    data["uid"] = TEST_USERUID
    data["filename"] = "fichero_002.txt"
    response = requests.get(url, headers=headers, data=json.dumps(data))
    
    assert response.status_code == 200

def test_unauthorized_file_modification():
    url = FILE_URL + "/modify_file"
    headers = {}
    headers["Content-Type"] = "application/json"
    headers["Authorization"] = "Bearer " + TEST_UNAUTHORIZED_TOKEN
    data = {}
    data["uid"] = TEST_USERUID
    data["filename"] = "fichero_002.txt"
    data["new_content"] = "Intento de modificacion no autorizado"
    data["visibility"] = "public"
    response = requests.put(url, headers=headers, data=json.dumps(data))
    
    assert response.status_code == 403

def test_unauthorized_file_removal():
    url = FILE_URL + "/remove_file"
    headers = {}
    headers["Content-Type"] = "application/json"
    headers["Authorization"] = "Bearer " + TEST_UNAUTHORIZED_TOKEN
    data = {}
    data["uid"] = TEST_USERUID
    data["filename"] = "fichero_002.txt"
    response = requests.delete(url, headers=headers, data=json.dumps(data))
    
    assert response.status_code == 403

def test_remove_file():
    url = FILE_URL + "/remove_file"
    headers = {}
    headers["Content-Type"] = "application/json"
    headers["Authorization"] = "Bearer " + TEST_USERTOKEN
    data = {}
    data["uid"] = TEST_USERUID
    data["filename"] = "fichero_001.txt"
    response = requests.delete(url, headers=headers, data=json.dumps(data))
    assert response.status_code == 200

def test_delete_user():
    url = f"{USER_URL}/delete_user/{TEST_NEW_USERNAME}"
    headers = {"Content-Type": "application/json"}
    response = requests.post(url, headers=headers)
    # Al no haber data, debe devolver 400 Bad request
    print("\n    Probando: Sin body")
    assert response.status_code == 400
    data = response.json()
    assert data["message"] == 'Body JSON requerido'

    payload = {}  # No password
    response = requests.post(url, headers=headers, data=json.dumps(payload))
    # Al no haber campo de contraseña, debe devolver 400 Bad request
    print("    Probando: Sin campo de constraseña en body")
    assert response.status_code == 400
    data = response.json()
    assert data["message"] == 'Body JSON no contiene la clave "password"'
    
    url = f"{USER_URL}/delete_user/usuario_inexistente"
    payload = {"password": TEST_NEW_PASSWORD, "new_username": "new"}
    response = requests.post(url, headers=headers, data=json.dumps(payload))
    # El usuario no existe, debe devolver 404 Not found
    print("    Probando: Usuario no existente")
    assert response.status_code == 404
    data = response.json()
    assert data["message"] == "Usuario no encontrado"
    
    url = f"{USER_URL}/delete_user/{TEST_NEW_USERNAME}"
    payload = {"password": TEST_PASSWORD, "new_username": TEST_NEW_USERNAME}
    response = requests.post(url, headers=headers, data=json.dumps(payload))
    # 
    print("    Probando: Contraseña incorrecta")
    assert response.status_code == 401, f"Expected 401, got {response.status_code}"
    data = response.json()
    assert data["message"] == "Credenciales incorrectas"

    url = f"{USER_URL}/delete_user/{TEST_NEW_USERNAME}"
    payload = {"password": TEST_NEW_PASSWORD}
    headers = {"Content-Type": "application/json"}
    response = requests.post(url, headers=headers, data=json.dumps(payload))
    # 
    print("    Probando: Funcionamiento normal")
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    data = response.json()
    assert data["status"] == "OK"

    # Verify deletion by trying to get user
    get_url = f"{USER_URL}/get_user_id/{TEST_NEW_USERNAME}"
    headers = {"Content-Type": "application/json"}
    get_response = requests.get(get_url, headers=headers)
    assert get_response.status_code == 404  # Should not exist now

# Run tests if executed directly
if __name__ == "__main__":
    pytest.main([__file__])