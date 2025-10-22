"""
user.py - Sistema de Gestión de Usuarios con API REST

Este módulo implementa un sistema completo de gestión de usuarios con autenticación, 
expuesto a través de una API REST construida con Quart.

Funcionalidades principales:
    - Creación y autenticación de usuarios
    - Gestión de contraseñas y nombres de usuario
    - Almacenamiento persistente en archivos CSV
    - Generación de tokens de sesión con UUID
    - API REST con endpoints HTTP asíncronos

Estructura de datos:
    - Usuarios: almacenados en resources/users.txt
    - Bibliotecas de usuario: almacenadas en resources/files/<uid>.txt

Autor: Juan Larrondo Fernández de Córdoba y Ana Pardo Jiménez
Fecha de creación: 14-9-2025
Última modificación: 11-10-2025
Versión: 3.0.0
Python: 3.7+
Dependencias: pandas, quart

Uso:
    python user.py
    
El servidor se ejecutará en http://0.0.0.0:5050
"""

import pandas as pd
import os
import uuid
from quart import Quart, jsonify, request
from sqlalchemy.orm import declarative_base, sessionmaker, text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession

# =============================================================================
# CONFIGURACIÓN Y CONSTANTES
# =============================================================================

Secret_uuid = uuid.UUID('00010203-0405-0607-0809-0a0b0c0d0e0f')
users_file = "resources/users.txt"
usr_lib_dir = "resources/files/"

# =============================================================================
# FUNCIONES DE GESTIÓN DE USUARIOS
# =============================================================================

def create_user(username, password):
    """
    Crea un nuevo usuario con el nombre de usuario y contraseña dados.
    Si el usuario ya existe, intenta hacer login en su lugar.
    
    Args:
        username (str): El nombre de usuario del nuevo usuario.
        password (str): La contraseña del nuevo usuario.

    Returns:
        tuple or None: 
            - (uid, token, was_created: bool) donde was_created es True si se creó un nuevo usuario,
              False si el usuario ya existía y se hizo login exitosamente
            - None si el usuario existe pero las credenciales son incorrectas
    """
    # Si el usuario ya existe, hacer login en su lugar
    uid, error_code = get_user_id(username)
    if error_code == 'OK':
        return None, False  # No se creó, ya existía
    
    uid = uuid.uuid4()
    uid = str(uid)

    token = uuid.uuid5(Secret_uuid, uid)

    #TODO: Hacer la query y todo

    query = "INSERT INTO Usuario (user_id, name, password, token, balance, admin) \
                    VALUES (:user_id, :name, :password, :token, :balance, :admin)"
    params = {"user_id": uid, "name": username, "password": password, "token": token, "balance": 0, "admin": False}
    fetch_all(engine, query, params)

    return uid, True  # Se creó nuevo usuario

def login_user(username, password):
    """
    Inicia sesión de un usuario usando nombre de usuario y contraseña.

    Args:
        username (str): Nombre de usuario.
        password (str): Contraseña del usuario.

    Returns:
        tuple: (uid, token, error_code)
            - (uid, token, "OK") si el login es exitoso
            - (None, None, "FILE_NOT_FOUND") si el archivo no existe
            - (None, None, "PERMISSION_DENIED") si no hay permisos
            - (None, None, "FILE_CORRUPTED") si el archivo está corrupto
            - (None, None, "UNKNOWN_ERROR") si hay otro error inesperado
            - (None, None, "UNAUTHORIZED") si las credenciales son incorrectas
    """
    df, error_code = open_users_txt()
    # Si hubo error al abrir el archivo, devolver el error específico
    if error_code != "OK":
        return None, None, error_code
    
    # Buscar el usuario con las credenciales proporcionadas
    usuario = df[
        (df["username"].astype(str).str.strip() == str(username).strip()) &
        (df["password"].astype(str).str.strip() == str(password).strip())
    ]
    
    if not usuario.empty:
        uid = usuario.iloc[0]["UID"]
        return uid, uuid.uuid5(Secret_uuid, uid), "OK"
    
    return None, None, "UNAUTHORIZED"

def get_user_id(username):
    """
    Obtiene el ID de usuario (UID) para el nombre de usuario dado.
    
    Args:
        username (str): El nombre de usuario del usuario.

    Returns:
        tuple: (uid o False, error_code: str)
            - (uid, "OK") si el usuario existe
            - (False, "USER_NOT_FOUND") si el usuario no existe
    """

    query = "SELECT user_id FROM Usuario WHERE name = :name"
    params = {"name": username}
    data = fetch_all(engine, query, params)
    if data:
        return data[0]["user_id"], "OK"
    else:
        return False, "USER_NOT_FOUND"

# =============================================================================
# FUNCIONES DE MODIFICACIÓN DE USUARIOS
# =============================================================================

def delete_user(username: str, password: str):
    """
    Elimina el usuario dado y su archivo de biblioteca asociado.

    Args:
        username (str): El nombre del usuario.
        password (str): La contraseña del usuario.

    Returns:
        tuple: (success: bool, error_code: str)
            - (True, "OK") si se eliminó correctamente
            - (False, "NOT_FOUND") si el usuario no existe
            - (False, "UNAUTHORIZED") si la contraseña es incorrecta
            - (False, "FILE_SYSTEM_ERROR") si hay error accediendo al directorio de archivos
            - (False, error_code) si hubo error al leer el archivo (FILE_NOT_FOUND, PERMISSION_DENIED, FILE_CORRUPTED, UNKNOWN_ERROR)
    """
    df, error_code = open_users_txt()
    
    # Si hubo error al leer el archivo, devolver ese error
    if error_code != "OK":
        return False, error_code

    # Verificar que el DataFrame no esté vacío
    if df.empty:
        return False, "NOT_FOUND"

    # Verificar si el usuario existe
    usuario_existe = df[df["username"].astype(str).str.strip() == str(username).strip()]
    if usuario_existe.empty:
        return False, "NOT_FOUND"

    # Verificar si la contraseña es correcta
    usuario = df[
        (df["username"].astype(str).str.strip() == str(username).strip()) &
        (df["password"].astype(str).str.strip() == str(password).strip())
    ]
    if usuario.empty:
        return False, "UNAUTHORIZED"

    uid = df.loc[(df["username"] == username) & (df["password"] == password), "UID"].values[0]
    usr_lib_name = usr_lib_dir + uid + ".txt"

    if os.path.exists(usr_lib_dir):
        if os.path.exists(usr_lib_name):
            os.remove(usr_lib_name)

        df = df[~((df["username"] == username) & (df["password"] == password))]
        df.to_csv(users_file, sep="\t", index=False)

        return True, "OK"

    return False, "FILE_SYSTEM_ERROR"

# =============================================================================
# FUNCIONES AUXILIARES
# =============================================================================

def comprobar_token_admin(token):
    """
    Comprueba si el token es de administrador.
    """
    return True

async def fetch_all(engine, query, params={}):
    async with engine.connect() as conn:
        result = await conn.execute(text(query), params)
        rows = result. all()
        keys = result. keys()
        data = [dict(zip(keys, row)) for row in rows]
    return data

# =============================================================================
# SERVIDOR HTTP - API REST (QUART)
# =============================================================================

app = Quart(__name__)

DATABASE_URL = "postgresql+asyncpg://alumnodb:1234@localhost:9999/si1"
# --- Engine y sesión asíncronos ---
engine = create_async_engine(DATABASE_URL, echo=False)
async_session = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

# -----------------------------------------------------------------------------
# Endpoints de Autenticación y Creación
# -----------------------------------------------------------------------------

@app.route("/user", methods=["PUT"])
async def http_user(username):
    """
    Endpoint HTTP para crear un nuevo usuario.
    
    - Método: POST
    - Path: /create_user/<username>
    - Body (JSON): {"password": "<password>"}
    - Comportamiento: Llama a create_user(username, password). Si el usuario ya existe, 
                     intenta hacer login en su lugar.
    - Respuestas esperadas:
        201: {"status":"OK", "username": username, "UID": "<uid>", "Token": "<token>"} - Usuario creado
        200: {"status":"OK", "username": username, "UID": "<uid>", "Token": "<token>"} - Usuario ya existía, hizo login
        401: {"status":"ERROR", "message": "Credenciales incorrectas"} - Usuario existe pero contraseña incorrecta
        400: {"status":"ERROR", "message": "..."} - Parámetros faltantes o body inválido
        500: {"status":"ERROR", "message": "..."} - Error interno del servidor
    """
    try:
        body = (await request.get_json(silent=True))
        if body is None:
            return jsonify({'status': 'ERROR', 'message': 'Body JSON requerido'}), 400
        
        # --- Autenticación: Bearer token ---
        #TODO: Preguntar al profe si es correcto el await request.headers.get("Authorization", "")
        auth = await request.headers.get("Authorization", "")
        if not auth.startswith("Bearer "):
            return jsonify({"ok": False, "error": "Falta Authorization Bearer"}), 400

        token = auth.split(" ", 1)[1].strip()
        if not comprobar_token_admin(token):
            return jsonify({"ok": False, "error": "Token no válido"}), 401

        name = body.get("name")
        if not name:
            return jsonify({'status': 'ERROR', 'message': 'Body JSON no contiene la clave "name"'}), 400
        
        password = body.get("password")
        if not password:
            return jsonify({'status': 'ERROR', 'message': 'Body JSON no contiene la clave "password"'}), 400

        result = create_user(name, password)
        if result is None:
            return jsonify({'status': 'ERROR', 'message': 'Credenciales incorrectas'}), 401

        uid, token, was_created = result
        
        # Si se creó un nuevo usuario, devolver 201 Created
        # Si ya existía y se hizo login, devolver 200 OK
        status_code = 201 if was_created else 200
        return jsonify({'status': 'OK', 'username': username, 'uid': uid}), status_code

    except Exception as exc:
        return jsonify({'status': 'ERROR', 'message': str(exc)}), 500


@app.route("/login/<username>", methods=["POST"])
async def http_login(username):
    """
    Endpoint HTTP para inicio de sesión de usuario.
    
    - Método: POST
    - Path: /login/<username>
    - Body (JSON): {"password": "<password>"}
    - Comportamiento: Llama a login_user(username, password)
    - Respuestas esperadas:
        200: {"status":"OK", "UID":"<uid>", "Token": "<token>"} - Login exitoso
        401: {"status":"ERROR", "message": "Credenciales incorrectas"} - Credenciales inválidas
        400: {"status":"ERROR", "message": "..."} - Parámetros faltantes
        500: {"status":"ERROR", "message": "..."} - Error interno del servidor o problemas con el archivo
    """
    try:

        body = (await request.get_json(silent=True))
        if body is None:
            return jsonify({'status': 'ERROR', 'message': 'Body JSON requerido'}), 400

        password = body.get("password")
        if not password:
            return jsonify({'status': 'ERROR', 'message': 'Body JSON no contiene la clave "password"'}), 400

        uid, token, error_code = login_user(username, password)
        
        if error_code != "OK":
            # Credenciales incorrectas (error del cliente)
            if error_code == "UNAUTHORIZED":
                return jsonify({'status': 'ERROR', 'message': 'Credenciales incorrectas'}), 401
            
            # Errores del servidor (archivo)
            error_response = handle_file_error(error_code)
            if error_response:
                return error_response
            
            # Error desconocido
            return jsonify({'status': 'ERROR', 'message': 'Error inesperado del servidor'}), 500

        return jsonify({'status': 'OK', 'UID': uid, 'Token': token}), 200

    except Exception as exc:
        return jsonify({'status': 'ERROR', 'message': str(exc)}), 500

# -----------------------------------------------------------------------------
# Endpoints de Consulta de Usuarios
# -----------------------------------------------------------------------------

@app.route("/get_user_id/<username>", methods=["GET"])
async def http_get_user_id(username):
    """
    Endpoint HTTP para comprobar existencia de usuario y recuperar su ID.
    
    - Método: GET
    - Path: /get_user_id/<username>
    - Comportamiento: Llama a get_user_id(username)
    - Respuestas esperadas:
        200: {"status":"OK", "UID":"<uid>", "username": "<username>"} - Usuario encontrado
        404: {"status":"ERROR", "message": "Usuario no encontrado"} - Usuario no existe
        500: {"status":"ERROR", "message": "..."} - Error interno del servidor o problemas con el archivo
    """
    uid, error_code = get_user_id(username)
    
    # Si el usuario no fue encontrado (pero el archivo se leyó bien)
    if error_code == "USER_NOT_FOUND":
        return jsonify({'status': 'ERROR', 'message': 'Usuario no encontrado'}), 404
    
    # Si hubo error al leer el archivo
    if error_code != "OK":
        error_response = handle_file_error(error_code)
        if error_response:
            return error_response
        
        # Error desconocido
        return jsonify({'status': 'ERROR', 'message': 'Error inesperado del servidor'}), 500

    return jsonify({'status': 'OK', 'UID': uid, 'username': username}), 200

# -----------------------------------------------------------------------------
# Endpoints de Modificación de Usuarios
# -----------------------------------------------------------------------------

@app.route("/change_pass/<username>", methods=["PATCH"])
async def http_change_pass(username):
    """
    Endpoint HTTP para cambiar la contraseña de un usuario.
    
    - Método: PATCH
    - Path: /change_pass/<username>
    - Body (JSON): {"password":"<contraseña_actual>", "new_password":"<nueva_contraseña>"}
    - Comportamiento: Llama a change_pass(username, password, new_password)
    - Respuestas esperadas:
        200: {"status":"OK"} - Contraseña cambiada exitosamente
        400: {"status":"ERROR", "message": "..."} - Parámetros faltantes
        401: {"status":"ERROR", "message": "Credenciales incorrectas"} - Contraseña actual incorrecta
        404: {"status":"ERROR", "message": "Usuario no encontrado"} - Usuario no existe
        500: {"status":"ERROR", "message": "..."} - Error interno del servidor
    """
    try:
        body = (await request.get_json(silent=True))
        if body is None:
            return jsonify({'status': 'ERROR', 'message': 'Body JSON requerido'}), 400

        password = body.get("password")
        new_password = body.get("new_password")

        if not password:
            return jsonify({'status': 'ERROR', 'message': 'Body JSON no contiene la clave "password"'}), 400
        
        if not new_password:
            return jsonify({'status': 'ERROR', 'message': 'Body JSON no contiene la clave "new_password"'}), 400

        success, error_code = change_pass(username, password, new_password)
        
        if not success:
            # Errores de usuario
            if error_code == "NOT_FOUND":
                return jsonify({'status': 'ERROR', 'message': 'Usuario no encontrado'}), 404
            elif error_code == "UNAUTHORIZED":
                return jsonify({'status': 'ERROR', 'message': 'Credenciales incorrectas'}), 401
            
            # Errores del servidor (archivo)
            error_response = handle_file_error(error_code)
            if error_response:
                return error_response
            
            # Error desconocido
            return jsonify({'status': 'ERROR', 'message': 'Error inesperado del servidor'}), 500

        return jsonify({'status': 'OK'}), 200

    except Exception as exc:
        return jsonify({'status': 'ERROR', 'message': str(exc)}), 500


@app.route("/change_username/<username>", methods=["PATCH"])
async def http_change_username(username):
    """
    Endpoint HTTP para cambiar el nombre de usuario.
    
    - Método: PATCH
    - Path: /change_username/<username>
    - Body (JSON): {"password":"<contraseña>", "new_username":"<nuevo_nombre>"}
    - Comportamiento: Llama a change_username(username, password, new_username)
    - Respuestas esperadas:
        200: {"status":"OK"} - Nombre de usuario cambiado exitosamente
        400: {"status":"ERROR", "message": "..."} - Parámetros faltantes
        401: {"status":"ERROR", "message": "Credenciales incorrectas"} - Contraseña incorrecta
        404: {"status":"ERROR", "message": "Usuario no encontrado"} - Usuario no existe
        500: {"status":"ERROR", "message": "..."} - Error interno del servidor
    """
    try:
        body = (await request.get_json(silent=True))
        if body is None:
            return jsonify({'status': 'ERROR', 'message': 'Body JSON requerido'}), 400

        password = body.get("password")
        new_username = body.get("new_username")

        if not password:
            return jsonify({'status': 'ERROR', 'message': 'Body JSON no contiene la clave "password"'}), 400
        
        if not new_username:
            return jsonify({'status': 'ERROR', 'message': 'Body JSON no contiene la clave "new_username"'}), 400

        success, error_code = change_username(username, password, new_username)
        
        if not success:
            # Errores de usuario
            if error_code == "NOT_FOUND":
                return jsonify({'status': 'ERROR', 'message': 'Usuario no encontrado'}), 404
            elif error_code == "UNAUTHORIZED":
                return jsonify({'status': 'ERROR', 'message': 'Credenciales incorrectas'}), 401
            
            # Errores del servidor (archivo)
            error_response = handle_file_error(error_code)
            if error_response:
                return error_response
            
            # Error desconocido
            return jsonify({'status': 'ERROR', 'message': 'Error inesperado del servidor'}), 500
        
        return jsonify({'status': 'OK'}), 200

    except Exception as exc:
        return jsonify({'status': 'ERROR', 'message': str(exc)}), 500


@app.route("/delete_user/<username>", methods=["DELETE"])
async def http_delete_user(username):
    """
    Endpoint HTTP para eliminar un usuario.
    
    - Método: DELETE
    - Path: /delete_user/<username>
    - Body (JSON): {"password":"<contraseña>"}
    - Comportamiento: Llama a delete_user(username, password). Elimina el usuario y su archivo de biblioteca.
    - Respuestas esperadas:
        200: {"status":"OK"} - Usuario eliminado exitosamente
        400: {"status":"ERROR", "message": "..."} - Parámetros faltantes
        401: {"status":"ERROR", "message": "Credenciales incorrectas"} - Contraseña incorrecta
        404: {"status":"ERROR", "message": "Usuario no encontrado"} - Usuario no existe
        500: {"status":"ERROR", "message": "..."} - Error interno del servidor o del sistema de archivos
    
    ADVERTENCIA: Operación destructiva. Se elimina el usuario y todos sus archivos asociados.
    """
    try:
        body = (await request.get_json(silent=True))
        if body is None:
            return jsonify({'status': 'ERROR', 'message': 'Body JSON requerido'}), 400

        password = body.get("password")

        if not password:
            return jsonify({'status': 'ERROR', 'message': 'Body JSON no contiene la clave "password"'}), 400
        
        success, error_code = delete_user(username, password)
        
        if not success:
            # Errores de usuario
            if error_code == "NOT_FOUND":
                return jsonify({'status': 'ERROR', 'message': 'Usuario no encontrado'}), 404
            elif error_code == "UNAUTHORIZED":
                return jsonify({'status': 'ERROR', 'message': 'Credenciales incorrectas'}), 401
            
            # Error específico del sistema de archivos
            elif error_code == "FILE_SYSTEM_ERROR":
                return jsonify({'status': 'ERROR', 'message': 'Error en el sistema de archivos'}), 500
            
            # Errores del servidor (archivo)
            error_response = handle_file_error(error_code)
            if error_response:
                return error_response
            
            # Error desconocido
            return jsonify({'status': 'ERROR', 'message': 'Error inesperado del servidor'}), 500
        
        return jsonify({'status': 'OK'}), 200

    except Exception as exc:
        return jsonify({'status': 'ERROR', 'message': str(exc)}), 500

# =============================================================================
# PUNTO DE ENTRADA PRINCIPAL
# =============================================================================

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5050, debug=True)