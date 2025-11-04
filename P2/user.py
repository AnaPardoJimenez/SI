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

import os
import uuid
from quart import Quart, jsonify, request
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from http import HTTPStatus

# =============================================================================
# CONFIGURACIÓN Y CONSTANTES
# =============================================================================

DATABASE_URL = "postgresql+asyncpg://alumnodb:1234@db:5432/si1"
# --- Engine y sesión asíncronos ---
engine = create_async_engine(DATABASE_URL, echo=False)
async_session = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

Secret_uuid = uuid.UUID('00010203-0405-0607-0809-0a0b0c0d0e0f')

# =============================================================================
# FUNCIONES AUXILIARES
# =============================================================================

async def comprobar_token_admin(token):
    """
    Comprueba si el token es de administrador.
    """
    query = "SELECT admin FROM Usuario WHERE token LIKE :token"
    params = {"token": token}
    data = await fetch_all(engine, query, params)
    if data and len(data) > 0:
        return data[0]["admin"]
    else:
        return None

async def fetch_all(engine, query, params={}):
    async with engine.connect() as conn:
        # Verificar si la query es de modificación (INSERT/UPDATE/DELETE) o solo lectura (SELECT)
        query_upper = query.strip().upper()
        is_modification = query_upper.startswith(('INSERT', 'UPDATE', 'DELETE'))
        
        if is_modification:
            # Para operaciones de modificación, usar transacción con commit automático
            async with conn.begin():
                result = await conn.execute(text(query), params)
                if result.rowcount > 0:
                    return True  # Operación exitosa
                else:
                    return None  # No se afectaron filas
        else:
            # Para SELECT, solo leer datos sin commit
            result = await conn.execute(text(query), params)
            rows = result.all()
            if len(rows) > 0:
                keys = result.keys()
                data = [dict(zip(keys, row)) for row in rows]
                return data
            else:
                return None

# =============================================================================
# FUNCIONES DE GESTIÓN DE USUARIOS
# =============================================================================

async def create_user(username, password):
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
    uid, error_code = await get_user_id(username)
    if error_code == 'OK':
        return None, False  # No se creó, ya existía
    
    uid = uuid.uuid4()
    uid = str(uid)

    token = str(uuid.uuid5(Secret_uuid, uid))

    query = "INSERT INTO Usuario (user_id, name, password, token, balance, admin) \
                    VALUES (:user_id, :name, :password, :token, :balance, :admin)"
    params = {"user_id": uid, "name": username, "password": password, "token": token, "balance": 100, "admin": False}
    await fetch_all(engine, query, params)

    query = "INSERT INTO Carrito (user_id) \
                    VALUES (:user_id)"
    params = {"user_id": uid}
    await fetch_all(engine, query, params
)
    return uid, True  # Se creó nuevo usuario y su carrito

async def login_user(username, password):
    """
    Inicia sesión de un usuario usando nombre de usuario y contraseña.

    Args:
        username (str): Nombre de usuario.
        password (str): Contraseña del usuario.

    Returns:
        tuple: (uid, token, error_code)
            - (uid, token, "OK") si el login es exitoso
            - (None, None, "ERROR") si el user no existe o la contraseña es incorrecta
    """
    query = "SELECT user_id, token FROM Usuario WHERE name ILIKE :name and password LIKE :password;"
    params = {"name": username, "password": password}
    data = await fetch_all(engine, query, params)

    if len(data) > 0:
        return data[0]["user_id"], data[0]["token"], "OK"
    else:
        return None, None, "ERROR"
    
async def get_user_id(username):
    """
    Obtiene el ID de usuario (UID) para el nombre de usuario dado.
    
    Args:
        username (str): El nombre de usuario del usuario.

    Returns:
        tuple: (uid o False, error_code: str)
            - (uid, "OK") si el usuario existe
            - (False, "USER_NOT_FOUND") si el usuario no existe
    """
    query = "SELECT user_id FROM Usuario WHERE name ILIKE :name"
    params = {"name": username}
    data = await fetch_all(engine, query, params)
    if data and len(data) > 0:
        return data[0]["user_id"], "OK"
    else:
        return False, "USER_NOT_FOUND"

# =============================================================================
# FUNCIONES DE MODIFICACIÓN DE USUARIOS
# =============================================================================

async def delete_user(uid: str):
    """
    Elimina el usuario dado y su archivo de biblioteca asociado.

    Args:
        username (str): El nombre del usuario.
        password (str): La contraseña del usuario.

    Returns:
        tuple: (success: bool, error_code: str)
            - (True, "OK") si se eliminó correctamente
            - (False, "NOT_FOUND") si el usuario no existe
    """
    query = "SELECT admin FROM Usuario WHERE user_id LIKE :uid"
    params = {"uid": uid}
    data = await fetch_all(engine, query, params)
    if data and len(data) > 0:
        if data[0]["admin"]:
            return False, "FORBIDDEN"

    query = "SELECT name FROM Usuario WHERE user_id LIKE :uid"
    params = {"uid": uid}
    data = await fetch_all(engine, query, params)

    if not data or len(data) == 0:
        return False, "NOT_FOUND"
    
    # Eliminar usuario de la base de datos
    query = "DELETE FROM Usuario WHERE user_id LIKE :uid"
    params = {"uid": uid}
    await fetch_all(engine, query, params)

    return True, "OK"

# =============================================================================
# SERVIDOR HTTP - API REST (QUART)
# =============================================================================

app = Quart(__name__)

# -----------------------------------------------------------------------------
# Endpoints de Autenticación y Creación
# -----------------------------------------------------------------------------

@app.route("/user", methods=["PUT"])
async def http_create_user():
    """
    Endpoint HTTP para crear un nuevo usuario.
    
    - Método: POST
    - Path: /create_user/<username>
    - Body (JSON): {"password": "<password>"}
    - Comportamiento: Llama a create_user(username, password). Si el usuario ya existe, 
                     intenta hacer login en su lugar.
    - Respuestas esperadas:
        HTTPStatus.OK: {"status":"OK", "username": username, "UID": "<uid>", "Token": "<token>"} - Usuario ya existía, hizo login
        HTTPStatus.UNAUTHORIZED: {"status":"ERROR", "message": "Credenciales incorrectas"} - Usuario existe pero contraseña incorrecta
        HTTPStatus.BAD_REQUEST: {"status":"ERROR", "message": "..."} - Parámetros faltantes o body inválido
        HTTPStatus.INTERNAL_SERVER_ERROR.BAD_REQUEST: {"status":"ERROR", "message": "..."} - Error interno del servidor
    """
    try:
        body = (await request.get_json(silent=True))
        if body is None:
            return jsonify({'status': 'ERROR', 'message': 'Body JSON requerido'}), HTTPStatus.BAD_REQUEST

        
        # --- Autenticación: Bearer token ---
        auth = request.headers.get("Authorization", "")
        if not auth.startswith("Bearer "):
            return jsonify({"status": 'ERROR', 'message': 'Falta Authorization Bearer'}), HTTPStatus.BAD_REQUEST


        token = auth.split(" ", 1)[1].strip()
        if not await comprobar_token_admin(token):
            return jsonify({"status": 'ERROR', 'message': 'Token no válido'}), HTTPStatus.UNAUTHORIZED


        name = body.get("name")
        if not name:
            return jsonify({'status': 'ERROR', 'message': 'Body JSON no contiene la clave "name"'}), HTTPStatus.BAD_REQUEST
        
        password = body.get("password")
        if not password:
            return jsonify({'status': 'ERROR', 'message': 'Body JSON no contiene la clave "password"'}), HTTPStatus.BAD_REQUEST

        result = await create_user(name, password)
        if result is None:
            return jsonify({'status': 'ERROR', 'message': 'Credenciales incorrectas'}), HTTPStatus.UNAUTHORIZED

        uid, was_created = result
        
        # Si ya existía y se hizo login, devolver HTTPStatus.OK OK
        if was_created:
            status_code = HTTPStatus.OK
        else:
            return jsonify({'status': 'ERROR', 'message': 'Credenciales incorrectas'}), HTTPStatus.UNAUTHORIZED
        
        return jsonify({'status': 'OK', 'username': name, 'uid': uid}), status_code

    except Exception as exc:
        return jsonify({'status': 'ERROR', 'message': str(exc)}), HTTPStatus.INTERNAL_SERVER_ERROR


@app.route("/user", methods=["GET"])
async def http_login():
    """
    Endpoint HTTP para inicio de sesión de usuario.
    
    - Método: POST
    - Path: /login/<username>
    - Body (JSON): {"password": "<password>"}
    - Comportamiento: Llama a login_user(username, password)
    - Respuestas esperadas:
        HTTPStatus.OK: {"status":"OK", "UID":"<uid>", "Token": "<token>"} - Login exitoso
        HTTPStatus.UNAUTHORIZED: {"status":"ERROR", "message": "Credenciales incorrectas"} - Credenciales inválidas
        HTTPStatus.BAD_REQUEST: {"status":"ERROR", "message": "..."} - Parámetros faltantes
        HTTPStatus.INTERNAL_SERVER_ERROR.BAD_REQUEST: {"status":"ERROR", "message": "..."} - Error interno del servidor o problemas con el archivo
    """
    try:
        body = (await request.get_json(silent=True))
        if body is None:
            return jsonify({'status': 'ERROR', 'message': 'Body JSON requerido'}), HTTPStatus.BAD_REQUEST

        username = body.get("name")
        if not username:
            return jsonify({'status': 'ERROR', 'message': 'Body JSON no contiene la clave "name"'}), HTTPStatus.BAD_REQUEST
        password = body.get("password")
        if not password:
            return jsonify({'status': 'ERROR', 'message': 'Body JSON no contiene la clave "password"'}), HTTPStatus.BAD_REQUEST
        uid, token, error_code = await login_user(username, password)
        if error_code != "OK":
            # Credenciales incorrectas (error del cliente)
            if error_code == "UNAUTHORIZED":
                return jsonify({'status': 'ERROR', 'message': 'Credenciales incorrectas'}), HTTPStatus.UNAUTHORIZED
            # Error desconocido
            return jsonify({'status': 'ERROR', 'message': 'Error inesperado del servidor'}), HTTPStatus.INTERNAL_SERVER_ERROR.BAD_REQUEST

        return jsonify({'status': 'OK', 'uid': uid, 'token': token}), HTTPStatus.OK

    except Exception as exc:
        return jsonify({'status': 'ERROR', 'message': str(exc)}), HTTPStatus.INTERNAL_SERVER_ERROR.BAD_REQUEST

# -----------------------------------------------------------------------------
# Endpoints de Modificación de Usuarios
# -----------------------------------------------------------------------------

@app.route("/user/<uid>", methods=["DELETE"])
async def http_delete_user(uid):
    """
    Endpoint HTTP para eliminar un usuario.
    
    - Método: DELETE
    - Path: /delete_user/<username>
    - Body (JSON): {"password":"<contraseña>"}
    - Comportamiento: Llama a delete_user(username, password). Elimina el usuario y su archivo de biblioteca.
    - Respuestas esperadas:
        HTTPStatus.OK: {"status":"OK"} - Usuario eliminado exitosamente
        HTTPStatus.BAD_REQUEST: {"status":"ERROR", "message": "..."} - Parámetros faltantes
        HTTPStatus.UNAUTHORIZED: {"status":"ERROR", "message": "Credenciales incorrectas"} - Contraseña incorrecta
        HTTPStatus.NOT_FOUND: {"status":"ERROR", "message": "Usuario no encontrado"} - Usuario no existe
        HTTPStatus.INTERNAL_SERVER_ERROR.BAD_REQUEST: {"status":"ERROR", "message": "..."} - Error interno del servidor o del sistema de archivos
    
    ADVERTENCIA: Operación destructiva. Se elimina el usuario y todos sus archivos asociados.
    """
    try:
        auth = request.headers.get("Authorization", "")
        if not auth.startswith("Bearer "):
            return jsonify({"ok": False, "error": "Falta Authorization Bearer"}), HTTPStatus.BAD_REQUEST


        token = auth.split(" ", 1)[1].strip()
        if not await comprobar_token_admin(token):
            return jsonify({"ok": False, "error": "Token no válido"}), HTTPStatus.UNAUTHORIZED
        
       
        success, error_code = await delete_user(uid)
        if not success:
            # Errores de usuario
            if error_code == "NOT_FOUND":
                return jsonify({'status': 'ERROR', 'message': 'Usuario no encontrado'}), HTTPStatus.NOT_FOUND

            elif error_code == "FORBIDDEN":
                return jsonify({'status': 'ERROR', 'message': 'No se puede eliminar el usuario administrador'}), HTTPStatus.FORBIDDEN
            # Error desconocido
            return jsonify({'status': 'ERROR', 'message': 'Error inesperado del servidor'}), HTTPStatus.INTERNAL_SERVER_ERROR.BAD_REQUEST
        
        return jsonify({'status': 'OK'}), HTTPStatus.OK

    except Exception as exc:
        return jsonify({'status': 'ERROR', 'message': str(exc)}), HTTPStatus.INTERNAL_SERVER_ERROR.BAD_REQUEST

# =============================================================================
# PUNTO DE ENTRADA PRINCIPAL
# =============================================================================

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5050, debug=True)