"""
client.py - Cliente de Pruebas para Sistema de Gestión de Usuarios y Archivos

Este módulo implementa un cliente de pruebas completo para el sistema de gestión de usuarios 
y archivos, utilizando pytest para realizar pruebas automatizadas de todos los endpoints 
de la API REST.

Funcionalidades principales:
    - Pruebas de autenticación y gestión de usuarios (crear, login, modificar, eliminar)
    - Pruebas de gestión de archivos (crear, leer, modificar, eliminar, listar)
    - Pruebas de tokens de compartición temporal
    - Pruebas de permisos y autorización
    - Limpieza automática de archivos de prueba
    - Validación de respuestas HTTP y códigos de estado

Estructura de pruebas:
    - Test de creación de usuarios con diferentes escenarios
    - Test de autenticación y login
    - Test de modificación de datos de usuario
    - Test de gestión completa de archivos
    - Test de tokens de compartición con expiración
    - Test de permisos y acceso no autorizado

Autor: Juan Larrondo Fernández de Córdoba y Ana Pardo Jiménez
Fecha de creación: 14-9-2025
Última modificación: 11-10-2025
Versión: 3.0.0
Python: 3.7+
Dependencias: requests, pytest, json, time, os

Uso:
    python client.py
    o
    pytest client.py
    
Las pruebas requieren que los servidores user.py (puerto 5050) y file.py (puerto 5051) 
estén ejecutándose.
"""

import requests
import json
import time
import os
import pytest

# =============================================================================
# CONFIGURACIÓN Y CONSTANTES
# =============================================================================

# URLs base para los servidores (asumiendo que están ejecutándose localmente)
USER_URL = "http://0.0.0.0:5050"
FILE_URL = "http://0.0.0.0:5051"

# =============================================================================
# DATOS DE PRUEBA Y CONFIGURACIÓN
# =============================================================================

# Datos de prueba para usuarios
TEST_USERNAME = "testuser"
TEST_PASSWORD = "testpass"
TEST_NEW_PASSWORD = "newtestpass"
TEST_NEW_USERNAME = "newtestuser"
TEST_USERTOKEN = None
TEST_USERUID = None
TEST_UNAUTHORIZED_TOKEN = None
TEST_UNAUTHORIZED_UID = None
TEST_UNAUTHORIZED_USERNAME = "unauthorized_user"

# Rutas a recursos (para limpieza)
USERS_FILE = "resources/users.txt"
USER_LIB_DIR = "resources/files/"

# =============================================================================
# FUNCIONES AUXILIARES
# =============================================================================

def cleanup_files():
    """
    Función auxiliar para limpiar archivos de prueba antes y después de las pruebas.
    
    Elimina el archivo de usuarios y todos los archivos .txt dentro del directorio 
    de bibliotecas de usuario, pero preserva la estructura de directorios.

    Returns:
        None: La función no retorna valor, pero limpia los archivos en disco.
    """
    # Elimina el archivo de usuarios si existe
    if os.path.exists(USERS_FILE) and os.path.isfile(USERS_FILE):
        os.remove(USERS_FILE)
    
    # Elimina solo archivos .txt dentro del directorio de bibliotecas de usuario, 
    # pero no el directorio en sí
    if os.path.exists(USER_LIB_DIR) and os.path.isdir(USER_LIB_DIR):
        for file in os.listdir(USER_LIB_DIR):
            full_path = os.path.join(USER_LIB_DIR, file)
            if os.path.isfile(full_path) and file.endswith(".txt"):
                os.remove(full_path)

# =============================================================================
# CONFIGURACIÓN DE PRUEBAS (PYTEST FIXTURES)
# =============================================================================

@pytest.fixture(scope="module", autouse=True)
def setup_teardown():
    """
    Fixture de pytest para configuración y limpieza de pruebas.
    
    Se ejecuta automáticamente antes y después de todas las pruebas del módulo.
    Limpia archivos de prueba antes de comenzar y espera un momento para que 
    los servidores estén listos.

    Yields:
        None: La función no retorna valor, pero maneja el ciclo de vida de las pruebas.
    """
    # Limpia archivos antes de las pruebas
    cleanup_files()
    
    # Espera un momento para que el servidor esté listo (si es necesario)
    time.sleep(1)
    
    yield
    
    # Limpia archivos después de las pruebas (comentado para inspección manual)
    #cleanup_files()

# =============================================================================
# PRUEBAS DE GESTIÓN DE USUARIOS
# =============================================================================

def test_create_user():
    """
    Prueba la creación de usuarios y diferentes escenarios de error.
    
    Verifica:
    - Creación exitosa de usuario nuevo (código 201)
    - Intento de crear usuario existente (debe hacer login, código 200)
    - Errores de validación (sin body, sin contraseña, contraseña incorrecta)
    
    Actualiza las variables globales TEST_USERTOKEN y TEST_USERUID.
    """
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
    """
    Prueba el inicio de sesión de usuarios y diferentes escenarios de error.
    
    Verifica:
    - Login exitoso con credenciales válidas (código 200)
    - Errores de validación (sin body, sin contraseña)
    - Login fallido con credenciales incorrectas (código 401)
    """
    url = f"{USER_URL}/login/{TEST_USERNAME}"
    headers = {"Content-Type": "application/json"}
    payload = {"password": TEST_PASSWORD}
    response = requests.post(url, headers=headers, data=json.dumps(payload))
    #
    print("\n    Probando: Funcionamiento normal")
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    data = response.json()
    assert data["status"] == "OK"
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
    print("    Probando: Sin campo de constraseña en body")
    assert response.status_code == 400
    data = response.json()
    assert data["message"] == 'Body JSON no contiene la clave "password"'
    
    payload = {"password": "wrongpass"}
    response = requests.post(url, headers=headers, data=json.dumps(payload))
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
    """
    Prueba el cambio de contraseña de usuarios y diferentes escenarios de error.
    
    Verifica:
    - Cambio exitoso de contraseña (código 200)
    - Validación del cambio mediante nuevo login
    - Errores de validación (sin body, sin campos requeridos)
    - Cambio fallido con credenciales incorrectas (código 401)
    - Cambio fallido para usuario inexistente (código 404)
    """
    url = f"{USER_URL}/change_pass/{TEST_USERNAME}"
    payload = {"password": TEST_PASSWORD, "new_password": TEST_NEW_PASSWORD}
    headers = {"Content-Type": "application/json"}
    response = requests.patch(url, headers=headers, data=json.dumps(payload))
    
    print("\n    Probando: Funcionamiento normal")
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    data = response.json()
    assert data["status"] == "OK"
    # Verify by logging in with new password
    login_url = f"{USER_URL}/login/{TEST_USERNAME}"
    login_payload = {"password": TEST_NEW_PASSWORD}
    login_response = requests.post(login_url, headers=headers, data=json.dumps(login_payload))
    assert login_response.status_code == 200

    response = requests.patch(url, headers=headers)
    # Al no haber data, debe devolver 400 Bad request
    print("    Probando: Sin body")
    assert response.status_code == 400
    data = response.json()
    assert data["message"] == 'Body JSON requerido'

    payload = {"new_password": TEST_NEW_PASSWORD}  # No password
    response = requests.patch(url, headers=headers, data=json.dumps(payload))
    # Al no haber campo de contraseña, debe devolver 400 Bad request
    print("    Probando: Sin campo de constraseña en body")
    assert response.status_code == 400
    data = response.json()
    assert data["message"] == 'Body JSON no contiene la clave "password"'

    payload = {"password": TEST_PASSWORD}  # No new password
    response = requests.patch(url, headers=headers, data=json.dumps(payload))
    # Al no haber campo de contraseña, debe devolver 400 Bad request
    print("    Probando: Sin campo de nueva constraseña en body")
    assert response.status_code == 400
    data = response.json()
    assert data["message"] == 'Body JSON no contiene la clave "new_password"'
    
    payload = {"password": TEST_PASSWORD, "new_password": TEST_NEW_PASSWORD}
    response = requests.patch(url, headers=headers, data=json.dumps(payload))
    # 
    print("    Probando: Contraseña incorrecta")
    assert response.status_code == 401, f"Expected 401, got {response.status_code}"
    data = response.json()
    assert data["message"] == "Credenciales incorrectas"
    
    url = f"{USER_URL}/change_pass/usuario_inexistente"
    payload = {"password": "wrong", "new_password": "new"}
    response = requests.patch(url, headers=headers, data=json.dumps(payload))
    # El usuario no existe, debe devolver 404 Not found
    print("    Probando: Usuario no existente")
    assert response.status_code == 404
    data = response.json()
    assert data["message"] == "Usuario no encontrado"

def test_change_username():
    url = f"{USER_URL}/change_username/{TEST_USERNAME}"
    payload = {"password": TEST_NEW_PASSWORD, "new_username": TEST_NEW_USERNAME}
    headers = {"Content-Type": "application/json"}
    response = requests.patch(url, headers=headers, data=json.dumps(payload))
    
    print("\n    Probando: Funcionamiento normal")
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    data = response.json()
    assert data["status"] == "OK"

    # Verify by getting new username
    get_url = f"{USER_URL}/get_user_id/{TEST_NEW_USERNAME}"
    headers = {"Content-Type": "application/json"}
    get_response = requests.get(get_url, headers=headers)
    assert get_response.status_code == 200

    response = requests.patch(url, headers=headers)
    # Al no haber data, debe devolver 400 Bad request
    print("    Probando: Sin body")
    assert response.status_code == 400
    data = response.json()
    assert data["message"] == 'Body JSON requerido'

    payload = {"new_username": TEST_NEW_USERNAME}  # No password
    response = requests.patch(url, headers=headers, data=json.dumps(payload))
    # Al no haber campo de contraseña, debe devolver 400 Bad request
    print("    Probando: Sin campo de constraseña en body")
    assert response.status_code == 400
    data = response.json()
    assert data["message"] == 'Body JSON no contiene la clave "password"'

    payload = {"password": TEST_NEW_PASSWORD}  # No new username
    response = requests.patch(url, headers=headers, data=json.dumps(payload))
    # Al no haber campo de contraseña, debe devolver 400 Bad request
    print("    Probando: Sin campo de nuevo nombre de usuario en body")
    assert response.status_code == 400
    data = response.json()
    assert data["message"] == 'Body JSON no contiene la clave "new_username"'
    
    url = f"{USER_URL}/change_username/usuario_inexistente"
    payload = {"password": TEST_NEW_PASSWORD, "new_username": "new"}
    response = requests.patch(url, headers=headers, data=json.dumps(payload))
    # El usuario no existe, debe devolver 404 Not found
    print("    Probando: Usuario no existente")
    assert response.status_code == 404
    data = response.json()
    assert data["message"] == "Usuario no encontrado"
    
    url = f"{USER_URL}/change_username/{TEST_NEW_USERNAME}"
    payload = {"password": TEST_PASSWORD, "new_username": TEST_NEW_USERNAME}
    response = requests.patch(url, headers=headers, data=json.dumps(payload))
    # 
    print("    Probando: Contraseña incorrecta")
    assert response.status_code == 401, f"Expected 401, got {response.status_code}"
    data = response.json()
    assert data["message"] == "Credenciales incorrectas"

# =============================================================================
# PRUEBAS DE GESTIÓN DE ARCHIVOS
# =============================================================================

def test_create_private_file():
    """
    Prueba la creación de archivos privados.
    
    Verifica la creación exitosa de un archivo con visibilidad privada.
    """

    print("\n    Probando: Private file")

    url = FILE_URL + "/create_file"
    headers = {"Content-Type": "application/json", "Authorization": "Bearer " + TEST_USERTOKEN}
    data = {"uid": TEST_USERUID, "filename": "fichero_001.txt", "content": "texto de prueba del fichero"}
    response = requests.post(url, headers=headers, data=json.dumps(data))
    assert response.status_code == 200

    print("    Probando: Public file")

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

def test_unauthorized_private_file_read():
    """
    Prueba que usuarios no autorizados no pueden leer archivos privados de otros usuarios.
    
    Crea un usuario no autorizado e intenta leer un archivo privado de otro usuario.
    Verifica que se devuelve código 403 (Forbidden).
    """
    print("\n    Probando: Leer fichero normal")

    url = FILE_URL + "/read_file"
    headers = {}
    headers["Content-Type"] = "application/json"
    headers["Authorization"] = "Bearer " + TEST_USERTOKEN
    data = {}
    data["uid"] = TEST_USERUID
    data["filename"] = "fichero_002.txt"
    response = requests.get(url, headers=headers, data=json.dumps(data))
    assert response.status_code == 200

    print("    Probando: Leer fichero privado sin permiso")

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

    print("    Probando: Leer fichero publico sin permiso")

    url = FILE_URL + "/read_file"
    headers = {}
    headers["Content-Type"] = "application/json"
    headers["Authorization"] = "Bearer " + TEST_UNAUTHORIZED_TOKEN
    data = {}
    data["uid"] = TEST_USERUID
    data["filename"] = "fichero_002.txt"
    response = requests.get(url, headers=headers, data=json.dumps(data))
    
    assert response.status_code == 200

def test_modify_file():
    print("\n    Probando: Modificar con permiso")

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

    print("    Probando: modificar sin permiso")

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

def test_list_files():
    print("\n    Probando: Listar ficheros")

    url = FILE_URL + "/list_files"
    headers = {}
    headers["Content-Type"] = "application/json"
    headers["Authorization"] = "Bearer " + TEST_USERTOKEN
    data = {}
    data["uid"] = TEST_USERUID
    response = requests.get(url, headers=headers, data=json.dumps(data))
    assert response.status_code == 200

# =============================================================================
# PRUEBAS DE TOKENS DE COMPARTICIÓN
# =============================================================================

def test_create_and_use_share_token_private_read():
    """
    Prueba la creación y uso de tokens de compartición para archivos privados.
    
    Crea un archivo privado, genera un token de compartición y verifica que permite 
    leer el archivo privado usando el token de compartición en el header Authorization.
    """
    print("\n    Probando: Crear share token")

    url_create = FILE_URL + "/create_file"
    headers_owner = {
        "Content-Type": "application/json",
        "Authorization": "Bearer " + TEST_USERTOKEN,
    }
    file_name = "fichero_share_expira.txt"
    data_create = {"uid": TEST_USERUID, "filename": file_name, "content": "contenido temporal"}
    response = requests.post(url_create, headers=headers_owner, data=json.dumps(data_create))
    assert response.status_code == 200

    url_share = FILE_URL + "/create_share_token"
    data_share = {"uid": TEST_USERUID, "filename": file_name, "minutes": 5}
    response = requests.post(url_share, headers=headers_owner, data=json.dumps(data_share))
    assert response.status_code == 200
    share_token = response.json()["share_token"]

    print("    Probando: Leer con share token normal")

    url_read = FILE_URL + "/read_file"
    headers_share = {
        "Content-Type": "application/json",
        "Authorization": "Bearer " + share_token,
    }
    data_read = {"uid": TEST_USERUID, "filename": file_name}
    response = requests.get(url_read, headers=headers_share, data=json.dumps(data_read))
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"

    print("    Probando: Leer con share token caducado")

    # Asegura que el fichero existe
    url_create = FILE_URL + "/create_file"
    headers_owner = {
        "Content-Type": "application/json",
        "Authorization": "Bearer " + TEST_USERTOKEN,
    }
    file_name = "fichero_share_expira.txt"
    data_create = {"uid": TEST_USERUID, "filename": file_name, "content": "contenido temporal"}
    response = requests.post(url_create, headers=headers_owner, data=json.dumps(data_create))
    assert response.status_code == 200

    # Crea un share token con 0 minutos de validez (expira enseguida)
    url_share = FILE_URL + "/create_share_token"
    data_share = {"uid": TEST_USERUID, "filename": file_name, "minutes": 0}
    response = requests.post(url_share, headers=headers_owner, data=json.dumps(data_share))
    assert response.status_code == 200
    share_token = response.json()["share_token"]

    # Espera a que el timestamp actual supere el de exp (redondeado a segundos)
    time.sleep(2)

    # Intenta leer con el share token caducado
    url_read = FILE_URL + "/read_file"
    headers_share = {
        "Content-Type": "application/json",
        "Authorization": "Bearer " + share_token,
    }
    data_read = {"uid": TEST_USERUID, "filename": file_name}
    response = requests.get(url_read, headers=headers_share, data=json.dumps(data_read))
    assert response.status_code == 403, f"Expected 403, got {response.status_code}"

# =============================================================================
# PRUEBAS DE PERMISOS Y AUTORIZACIÓN
# =============================================================================

def test_remove_file():
    print("\n    Probando: Eliminar con permiso")

    url = FILE_URL + "/remove_file"
    headers = {}
    headers["Content-Type"] = "application/json"
    headers["Authorization"] = "Bearer " + TEST_USERTOKEN
    data = {}
    data["uid"] = TEST_USERUID
    data["filename"] = "fichero_001.txt"
    response = requests.delete(url, headers=headers, data=json.dumps(data))
    assert response.status_code == 200

    print("    Probando: Eliminar sin permiso")

    url = FILE_URL + "/remove_file"
    headers = {}
    headers["Content-Type"] = "application/json"
    headers["Authorization"] = "Bearer " + TEST_UNAUTHORIZED_TOKEN
    data = {}
    data["uid"] = TEST_USERUID
    data["filename"] = "fichero_002.txt"
    response = requests.delete(url, headers=headers, data=json.dumps(data))
    
    assert response.status_code == 403

def test_delete_user():
    url = f"{USER_URL}/delete_user/{TEST_NEW_USERNAME}"
    headers = {"Content-Type": "application/json"}
    response = requests.delete(url, headers=headers)
    # Al no haber data, debe devolver 400 Bad request
    print("\n    Probando: Sin body")
    assert response.status_code == 400
    data = response.json()
    assert data["message"] == 'Body JSON requerido'

    payload = {}  # No password
    response = requests.delete(url, headers=headers, data=json.dumps(payload))
    # Al no haber campo de contraseña, debe devolver 400 Bad request
    print("    Probando: Sin campo de constraseña en body")
    assert response.status_code == 400
    data = response.json()
    assert data["message"] == 'Body JSON no contiene la clave "password"'
    
    url = f"{USER_URL}/delete_user/usuario_inexistente"
    payload = {"password": TEST_NEW_PASSWORD, "new_username": "new"}
    response = requests.delete(url, headers=headers, data=json.dumps(payload))
    # El usuario no existe, debe devolver 404 Not found
    print("    Probando: Usuario no existente")
    assert response.status_code == 404
    data = response.json()
    assert data["message"] == "Usuario no encontrado"
    
    url = f"{USER_URL}/delete_user/{TEST_NEW_USERNAME}"
    payload = {"password": TEST_PASSWORD, "new_username": TEST_NEW_USERNAME}
    response = requests.delete(url, headers=headers, data=json.dumps(payload))
    # 
    print("    Probando: Contraseña incorrecta")
    assert response.status_code == 401, f"Expected 401, got {response.status_code}"
    data = response.json()
    assert data["message"] == "Credenciales incorrectas"

    url = f"{USER_URL}/delete_user/{TEST_NEW_USERNAME}"
    payload = {"password": TEST_NEW_PASSWORD}
    headers = {"Content-Type": "application/json"}
    response = requests.delete(url, headers=headers, data=json.dumps(payload))
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

# =============================================================================
# PUNTO DE ENTRADA PRINCIPAL
# =============================================================================

# Ejecutar pruebas si se ejecuta directamente
if __name__ == "__main__":
    pytest.main([__file__])