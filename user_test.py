import requests
import json
import time
import os
import pytest

# Base URL for the server (assuming it's running locally)
BASE_URL = "http://0.0.0.0:5050"

# Test data
TEST_USERNAME = "testuser"
TEST_PASSWORD = "testpass"
TEST_NEW_PASSWORD = "newtestpass"
TEST_NEW_USERNAME = "newtestuser"

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
    url = f"{BASE_URL}/create_user/{TEST_USERNAME}"
    headers = {"Content-Type": "application/json"}
    payload = {"password": TEST_PASSWORD}
    response = requests.post(url, headers=headers, data=json.dumps(payload))
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
    url = f"{BASE_URL}/login/{TEST_USERNAME}"
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
    url = f"{BASE_URL}/get_user_id/{TEST_USERNAME}"
    headers = {"Content-Type": "application/json"}
    response = requests.get(url, headers=headers)
    # 
    print("\n    Probando: Funcionamiento normal")
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    data = response.json()
    assert data["status"] == "OK"
    assert "UID" in data
    
    print("    Probando: Usuario no existente")
    url = f"{BASE_URL}/get_user_id/nonexistentuser"
    response = requests.get(url, headers=headers)
    assert response.status_code == 404

def test_change_password():
    url = f"{BASE_URL}/change_pass/{TEST_USERNAME}"
    payload = {"password": TEST_PASSWORD, "new_password": TEST_NEW_PASSWORD}
    headers = {"Content-Type": "application/json"}
    response = requests.post(url, headers=headers, data=json.dumps(payload))
    
    print("\n    Probando: Funcionamiento normal")
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    data = response.json()
    assert data["status"] == "OK"
    # Verify by logging in with new password
    login_url = f"{BASE_URL}/login/{TEST_USERNAME}"
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
    
    url = f"{BASE_URL}/change_pass/usuario_inexistente"
    payload = {"password": "wrong", "new_password": "new"}
    response = requests.post(url, headers=headers, data=json.dumps(payload))
    # El usuario no existe, debe devolver 404 Not found
    print("    Probando: Usuario no existente")
    assert response.status_code == 404
    data = response.json()
    assert data["message"] == "Usuario no encontrado"

def test_change_username():
    url = f"{BASE_URL}/change_username/{TEST_USERNAME}"
    payload = {"password": TEST_NEW_PASSWORD, "new_username": TEST_NEW_USERNAME}
    headers = {"Content-Type": "application/json"}
    response = requests.post(url, headers=headers, data=json.dumps(payload))
    
    print("\n    Probando: Funcionamiento normal")
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    data = response.json()
    assert data["status"] == "OK"

    # Verify by getting new username
    get_url = f"{BASE_URL}/get_user_id/{TEST_NEW_USERNAME}"
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
    
    url = f"{BASE_URL}/change_username/usuario_inexistente"
    payload = {"password": TEST_NEW_PASSWORD, "new_username": "new"}
    response = requests.post(url, headers=headers, data=json.dumps(payload))
    # El usuario no existe, debe devolver 404 Not found
    print("    Probando: Usuario no existente")
    assert response.status_code == 404
    data = response.json()
    assert data["message"] == "Usuario no encontrado"
    
    url = f"{BASE_URL}/change_username/{TEST_NEW_USERNAME}"
    payload = {"password": TEST_PASSWORD, "new_username": TEST_NEW_USERNAME}
    response = requests.post(url, headers=headers, data=json.dumps(payload))
    # 
    print("    Probando: Contraseña incorrecta")
    assert response.status_code == 401, f"Expected 401, got {response.status_code}"
    data = response.json()
    assert data["message"] == "Credenciales incorrectas"

def test_delete_user():
    url = f"{BASE_URL}/delete_user/{TEST_NEW_USERNAME}"
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
    
    url = f"{BASE_URL}/change_username/usuario_inexistente"
    payload = {"password": TEST_NEW_PASSWORD, "new_username": "new"}
    response = requests.post(url, headers=headers, data=json.dumps(payload))
    # El usuario no existe, debe devolver 404 Not found
    print("    Probando: Usuario no existente")
    assert response.status_code == 404
    data = response.json()
    assert data["message"] == "Usuario no encontrado"
    
    url = f"{BASE_URL}/change_username/{TEST_NEW_USERNAME}"
    payload = {"password": TEST_PASSWORD, "new_username": TEST_NEW_USERNAME}
    response = requests.post(url, headers=headers, data=json.dumps(payload))
    # 
    print("    Probando: Contraseña incorrecta")
    assert response.status_code == 401, f"Expected 401, got {response.status_code}"
    data = response.json()
    assert data["message"] == "Credenciales incorrectas"

    url = f"{BASE_URL}/delete_user/{TEST_NEW_USERNAME}"
    payload = {"password": TEST_NEW_PASSWORD}
    headers = {"Content-Type": "application/json"}
    response = requests.post(url, headers=headers, data=json.dumps(payload))
    # 
    print("    Probando: Funcionamiento normal")
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    data = response.json()
    assert data["status"] == "OK"

    # Verify deletion by trying to get user
    get_url = f"{BASE_URL}/get_user_id/{TEST_NEW_USERNAME}"
    headers = {"Content-Type": "application/json"}
    get_response = requests.get(get_url, headers=headers)
    assert get_response.status_code == 404  # Should not exist now

# Run tests if executed directly
if __name__ == "__main__":
    pytest.main([__file__])