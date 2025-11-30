"""
user.py - Sistema de Gestión de Usuarios con API REST

Este módulo implementa un sistema completo de gestión de usuarios con autenticación, 
expuesto a través de una API REST construida con Quart.

Funcionalidades principales:
    - Creación y autenticación de usuarios
    - Gestión de contraseñas y nombres de usuario con hashing seguro (SHA-512)
    - Almacenamiento persistente en base de datos PostgreSQL
    - Generación de tokens de sesión con UUID
    - Control de acceso basado en roles (administrador/usuarios)
    - API REST con endpoints HTTP asíncronos
    - Gestión de carritos de compra por usuario

Seguridad de contraseñas:
    - Las contraseñas se hashean usando SHA-512 con un salt único antes de almacenarse
    - El hashing se realiza en los endpoints HTTP, antes de pasar a las funciones internas
    - Las contraseñas en texto plano nunca se almacenan ni se pasan a funciones internas
    - El salt es una constante compartida para garantizar consistencia en el hashing
    - Formato: SHA-512(password + SALT) → hash hexadecimal de 128 caracteres

Estructura de datos:
    - Usuarios: almacenados en base de datos PostgreSQL (tabla Usuario)
    - Carritos: almacenados en base de datos PostgreSQL (tabla Carrito)
    - Tokens: generados mediante UUID v5 basado en el user_id
    - Contraseñas: almacenadas como hashes SHA-512 en VARCHAR(255)

Autor: Juan Larrondo Fernández de Córdoba y Ana Pardo Jiménez
Fecha de creación: 14-9-2025
Última modificación: 28-10-2025
Versión: 3.1.0
Python: 3.7+
Dependencias: quart, sqlalchemy, asyncpg, hashlib (estándar)

Uso:
    python user.py
    
El servidor se ejecutará en http://0.0.0.0:5050

Endpoints principales:
    GET  /user           - Autenticar usuario (login)
    PUT  /user           - Crear nuevo usuario (requiere token admin)
    DELETE /user/<uid>   - Eliminar usuario (requiere token admin)
"""

import os
import uuid
import hashlib
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

# Salt único para hashing de contraseñas
# El salt es un valor adicional que se concatena con la contraseña antes de hashear.
# Esto previene ataques de diccionario y rainbow tables, ya que incluso contraseñas
# idénticas producirán hashes diferentes si se usa un salt diferente.
# En este sistema, se usa un salt fijo compartido para garantizar consistencia
# en el hashing (misma contraseña → mismo hash, permitiendo verificación).
SALT = "a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6"

# =============================================================================
# FUNCIONES AUXILIARES
# =============================================================================

async def comprobar_token_admin(token):
    """
    Comprueba si el token pertenece a un usuario administrador.
    
    Args:
        token (str): Token de autenticación a verificar.
    
    Returns:
        bool: True si el token pertenece a un administrador, False o None en caso contrario
    """
    query = """
                SELECT admin
                FROM Usuario
                WHERE token LIKE :token
            """
    params = {"token": token}
    data = await fetch_all(engine, query, params)
    if data and len(data) > 0:
        return data[0]["admin"]
    else:
        return None

async def get_uid_by_token(token):
    """
    Devuelve el UID asociado a un token siempre que el usuario siga activo.

    Args:
        token (str): Token de autenticación.

    Returns:
        str | None: UID si existe y el usuario está activo, None en caso contrario.
    """
    query = "SELECT user_id FROM Usuario WHERE token LIKE :token AND active = TRUE"
    params = {"token": token}
    data = await fetch_all(engine, query, params)
    if data:
        return data[0]["user_id"]
    return None

async def user_exists(uid):
    """
    Comprueba si existe un usuario activo con el UID proporcionado.

    Args:
        uid (str): Identificador del usuario.

    Returns:
        tuple: (is_active: bool, status: str)
            - (True, "OK") si el usuario existe y está activo
            - (False, "NOT_FOUND") si no existe o está desactivado
    """
    query = "SELECT * FROM Usuario WHERE user_id LIKE :uid"
    params = {"uid": uid}
    data = await fetch_all(engine, query, params)

    if data and len(data) > 0:
        if "active" in data[0]:
            return data[0]["active"], "OK"
    return False, "NOT_FOUND"

async def fetch_all(engine, query, params={}):
    """
    Ejecuta una consulta SQL de forma asíncrona.
    
    Maneja tanto consultas de lectura (SELECT) como de modificación (INSERT, UPDATE, DELETE).
    Para consultas de modificación, usa transacciones con commit automático.
    
    Args:
        engine: Motor de SQLAlchemy para la conexión.
        query (str): Consulta SQL a ejecutar.
        params (dict, optional): Parámetros para la consulta preparada.
    
    Returns:
        Para SELECT:
            - list: Lista de diccionarios con los resultados
            - None: Si no hay resultados o hay un error
        Para INSERT/UPDATE/DELETE:
            - True: Si la operación afectó filas
            - None: Si no se afectaron filas o hay un error
    """
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

async def create_user(username, password, nationality):
    """
    Crea un nuevo usuario con el nombre de usuario y contraseña dados.
    Si el usuario ya existe, intenta hacer login en su lugar.
    
    NOTA: Esta función recibe la contraseña ya hasheada (SHA-512 + salt).
    El hashing se realiza en los endpoints HTTP antes de llamar a esta función.
    
    Args:
        username (str): El nombre de usuario del nuevo usuario.
        password (str): El hash SHA-512 de la contraseña (ya hasheada en el endpoint).
        nationality (str): Nacionalidad del usuario.

    Returns:
        tuple or None: 
            - (uid, token, was_created: bool) donde was_created es True si se creó un nuevo usuario,
              False si el usuario ya existía y se hizo login exitosamente
            - None si el usuario existe pero las credenciales son incorrectas
    """
    # Si el usuario ya existe, hacer login en su lugar
    uid, error_code = await get_user_id(username)
    print(uid, error_code)
    if error_code == 'OK':
        return None, False  # No se creó, ya existía
    
    uid = uuid.uuid4()
    uid = str(uid)

    token = str(uuid.uuid5(Secret_uuid, uid))

    query = "INSERT INTO Usuario (user_id, name, password, token, balance, admin, nationality) \
                    VALUES (:user_id, :name, :password, :token, :balance, :admin, :nationality)"
    params = {"user_id": uid, "name": username, "password": password, "token": token, "balance": 0, "admin": False, "nationality": nationality}
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

    NOTA: Esta función recibe la contraseña ya hasheada (SHA-512 + salt).
    El hashing se realiza en los endpoints HTTP antes de llamar a esta función.
    Compara el hash recibido con el hash almacenado en la base de datos.

    Args:
        username (str): Nombre de usuario.
        password (str): El hash SHA-512 de la contraseña (ya hasheada en el endpoint).

    Returns:
        tuple: (uid, token, error_code)
            - (uid, token, "OK") si el login es exitoso (usuario activo)
            - (None, None, "ERROR") si el user no existe, está desactivado o la contraseña es incorrecta
    """
    query = "SELECT user_id, token FROM Usuario WHERE name ILIKE :name and password = :password AND active = TRUE;"
    params = {"name": username, "password": password}
    data = await fetch_all(engine, query, params)

    if data and len(data) > 0:
        return data[0]["user_id"], data[0]["token"], "OK"
    else:
        return None, None, "ERROR"
    
async def get_user_id(username):
    """
    Obtiene el ID de usuario (UID) para el nombre de usuario dado siempre que esté activo.
    
    Args:
        username (str): El nombre de usuario del usuario.

    Returns:
        tuple: (uid o False, error_code: str)
            - (uid, "OK") si el usuario existe y está activo
            - (False, "USER_NOT_FOUND") si el usuario no existe o está desactivado
    """
    query = "SELECT user_id FROM Usuario WHERE name ILIKE :name AND active = TRUE;"
    params = {"name": username}
    data = await fetch_all(engine, query, params)
    if data and len(data) > 0:
        return data[0]["user_id"], "OK"
    else:
        return False, "USER_NOT_FOUND"

# =============================================================================
# FUNCIONES DE MODIFICACIÓN DE USUARIOS
# =============================================================================

async def update_user(uid, username=None, password=None, nationality=None):
    """
    Actualiza el nombre, la contraseña y/o la nacionalidad de un usuario dado.

    NOTA: La contraseña debe llegar ya hasheada (SHA-512 + salt). El hashing se
    realiza en el endpoint HTTP antes de llamar a esta función.

    Args:
        uid (str): ID del usuario a actualizar.
        username (str | None): Nuevo nombre de usuario (None para mantener).
        password (str | None): Nuevo hash de contraseña (None para mantener).
        nationality (str | None): Nueva nacionalidad (None para mantener).

    Returns:
        tuple: (success: bool, error_code: str)
            - (True, "OK") si se actualizó al menos un campo.
            - (False, "NOT_FOUND") si el usuario no existe o no se actualizó.
            - (False, "NO_FIELDS") si no se envió ningún campo a actualizar.
    """
    if username is None and password is None and nationality is None:
        return False, "NO_FIELDS"

    active, status = await user_exists(uid)
    if status != "OK" or not active:
        return False, "NOT_FOUND"

    fields = []
    params = {"uid": uid}
    if username is not None:
        fields.append("name = :username")
        params["username"] = username
    if password is not None:
        fields.append("password = :password")
        params["password"] = password
    if nationality is not None:
        fields.append("nationality = :nationality")
        params["nationality"] = nationality

    query = f"UPDATE Usuario SET {', '.join(fields)} WHERE user_id LIKE :uid"
    data = await fetch_all(engine, query, params)

    if not data:
        return False, "NOT_FOUND"

    return True, "OK"

async def delete_user(uid: str):
    """
    Elimina el usuario dado y su carrito asociado.

    Args:
        uid (str): El ID del usuario a eliminar.

    Returns:
        tuple: (success: bool, error_code: str)
            - (True, "OK") si se eliminó correctamente
            - (False, "NOT_FOUND") si el usuario no existe
            - (False, "FORBIDDEN") si se intenta eliminar un administrador
    """
    # NOTE: en lugar de borra el usuario, si tiene admin True no se puede borrar
    # ademas si tiene peliculas en el carrito no se puede borrar tampoco (mensaje)
    # si no tiene peliculas en el carrito y ademas no ha realizado pedidos se puede borrar
    # en caso contrario poner su bool de activo a False (no se puede loguear ni comprar)
    query = "SELECT admin FROM Usuario WHERE user_id LIKE :uid"
    params = {"uid": uid}
    data = await fetch_all(engine, query, params)
    print(f"345 - {data}")
    if data and len(data) > 0:
        print("347 ", len(data))
        if data[0]["admin"]:
            return False, "FORBIDDEN"

    # Verificar si el usuario existe y esta activo (si no esta activo es como si no existiera)
    active, status = await user_exists(uid)
    print(f"353 - {active}, {status}")
    if status != "OK" or not active:
        print(f"355")
        return False, "NOT_FOUND"

    # Comprobar si el carrito del usuario tiene películas
    query = """
            SELECT COUNT(*) AS movie_count 
            FROM Carrito_Pelicula cp
            JOIN Carrito c ON cp.cart_id = c.cart_id
            WHERE c.user_id LIKE :uid
            """
    params = {"uid": uid}
    data = await fetch_all(engine, query, params)
    print(f"367 - {data}")

    # Si el carrito no está vacío, no se puede eliminar el usuario
    if data and data[0]["movie_count"] > 0:
        print(f"370")
        return False, "NOT_EMPTY_CART"
    
    # Comprobar si el usuario ha realizado pedidos
    query = """
            SELECT COUNT(*) AS order_count
            FROM Pedido
            WHERE user_id LIKE :uid
            """
    params = {"uid": uid}
    data = await fetch_all(engine, query, params)
    print(f"382 - {data}")

    if data and data[0]["order_count"] > 0:
        print(f"385")
        # Si ha realizado pedidos, marcar como inactivo en lugar de eliminar
        query = "UPDATE Usuario SET active = FALSE WHERE user_id LIKE :uid"
        params = {"uid": uid}
        await fetch_all(engine, query, params)
        print(f"390")
        return True, "OK"

    # Eliminar usuario de la base de datos
    query = "DELETE FROM Usuario WHERE user_id LIKE :uid"
    params = {"uid": uid}
    await fetch_all(engine, query, params)
    print(f"397")

    return True, "OK"

# =============================================================================
# FUNCIONES DE DESCUENTO DE USUARIOS
# =============================================================================

async def add_discount(uid, discount):
    """
    Asigna un porcentaje de descuento a un usuario concreto.

    Args:
        uid (str): UID del usuario al que se aplica el descuento.
        discount (int): Porcentaje de descuento (1-100).

    Returns:
        tuple:
            - (True, "OK") si se actualiza correctamente.
            - (False, "BAD_REQUEST") si el porcentaje no está en rango.
            - (False, "USER_NOT_FOUND") si el usuario no existe.
            - (False, "ERROR") en cualquier otro fallo.
    """
    if discount <= 0 or discount > 100:
        return False, "BAD_REQUEST"
    
    active, status = await user_exists(uid)
    if status != "OK" or not active:
        return False, "USER_NOT_FOUND"
    
    query = "UPDATE Usuario SET discount = :discount WHERE user_id LIKE :target_uid"
    params = {"discount": discount, "target_uid": uid}

    data = await fetch_all(engine, query, params)

    if not data:
        return False, "ERROR"
    
    return True, "OK"

async def get_discount(uid):
    """
    Recupera el porcentaje de descuento actual de un usuario.

    Args:
        uid (str): UID del usuario.

    Returns:
        tuple:
            - (discount:int, "OK") con el porcentaje aplicado.
            - (None, "USER_NOT_FOUND") si el usuario no existe.
            - (None, "ERROR") en caso de fallo al consultar.
    """
    active, status = await user_exists(uid)
    if status != "OK" or not active:
        return False, "USER_NOT_FOUND"
    
    query = "SELECT discount FROM Usuario WHERE user_id LIKE :target_uid"
    params = {"target_uid": uid}

    data = await fetch_all(engine, query, params)

    if not data:
        return None, "ERROR"
    
    return data[0]["discount"], "OK"

async def remove_discount(uid):
    """
    Elimina el descuento asignado a un usuario (lo deja en 0%).

    Args:
        uid (str): UID del usuario al que se le retira el descuento.

    Returns:
        tuple:
            - (True, "OK") si se eliminó correctamente.
            - (False, "USER_NOT_FOUND") si el usuario no existe.
            - (False, "ERROR") en otros fallos.
    """
    active, status = await user_exists(uid)
    if status != "OK" or not active:
        return False, "USER_NOT_FOUND"
    
    query = "UPDATE Usuario SET discount = 0 WHERE user_id LIKE :target_uid"
    params = {"target_uid": uid}

    data = await fetch_all(engine, query, params)

    if not data:
        return False, "ERROR"
    
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
    
    - Método: PUT
    - Path: /user
    - Headers: Authorization: Bearer <token_admin>
    - Body (JSON): {"name": "<username>", "password": "<password>"}
    - Comportamiento: Llama a create_user(username, password). Solo usuarios administradores
                     pueden crear nuevos usuarios.
    - Respuestas esperadas:
        HTTPStatus.OK: {"status":"OK", "username": username, "uid": "<uid>"} - Usuario creado exitosamente
        HTTPStatus.UNAUTHORIZED: {"status":"ERROR", "message": "Token no válido"} - Token no válido o no es admin
        HTTPStatus.UNAUTHORIZED: {"status":"ERROR", "message": "Credenciales incorrectas"} - Usuario existe pero contraseña incorrecta
        HTTPStatus.BAD_REQUEST: {"status":"ERROR", "message": "..."} - Parámetros faltantes o body inválido
        HTTPStatus.INTERNAL_SERVER_ERROR: {"status":"ERROR", "message": "..."} - Error interno del servidor
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
        # Hashear la contraseña
        password = hashlib.sha512((password + SALT).encode('utf-8')).hexdigest()

        nationality = body.get("nationality")
        if not nationality:
            return jsonify({'status': 'ERROR', 'message': 'Body JSON no contiene la clave "nationality"'}), HTTPStatus.BAD_REQUEST
        
        result = await create_user(name, password, nationality)
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
    
    - Método: GET
    - Path: /user
    - Body (JSON): {"name": "<username>", "password": "<password>"}
    - Comportamiento: Llama a login_user(username, password)
    - Respuestas esperadas:
        HTTPStatus.OK: {"status":"OK", "uid":"<uid>", "token": "<token>"} - Login exitoso
        HTTPStatus.UNAUTHORIZED: {"status":"ERROR", "message": "Credenciales incorrectas"} - Credenciales inválidas
        HTTPStatus.BAD_REQUEST: {"status":"ERROR", "message": "..."} - Parámetros faltantes
        HTTPStatus.INTERNAL_SERVER_ERROR: {"status":"ERROR", "message": "..."} - Error interno del servidor
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
        # Hashear la contraseña
        password = hashlib.sha512((password + SALT).encode('utf-8')).hexdigest()
        
        uid, token, error_code = await login_user(username, password)
        if error_code != "OK":
            # Credenciales incorrectas (error del cliente)
            if error_code == "UNAUTHORIZED":
                return jsonify({'status': 'ERROR', 'message': 'Credenciales incorrectas'}), HTTPStatus.UNAUTHORIZED
            # Error desconocido
            return jsonify({'status': 'ERROR', 'message': 'Error inesperado del servidor'}), HTTPStatus.INTERNAL_SERVER_ERROR

        return jsonify({'status': 'OK', 'uid': uid, 'token': token}), HTTPStatus.OK

    except Exception as exc:
        return jsonify({'status': 'ERROR', 'message': str(exc)}), HTTPStatus.INTERNAL_SERVER_ERROR

# -----------------------------------------------------------------------------
# Endpoints de Modificación de Usuarios
# -----------------------------------------------------------------------------

@app.route("/user/<uid>", methods=["PUT"])
async def http_update_user(uid):
    """
    Endpoint HTTP para actualizar datos de un usuario.
    
    - Método: PUT
    - Path: /user/<uid>
    - Headers: Authorization: Bearer <token_admin>
    - Body (JSON): {"name": "<nuevo_nombre>", "password": "<nueva_password>"}
                   Ambos campos son opcionales, pero se debe enviar al menos uno.
    - Comportamiento: Verifica token admin, hashea password si viene y llama a update_user(uid, ...).
    - Respuestas esperadas:
        HTTPStatus.OK: {"status": "OK"} - Usuario actualizado.
        HTTPStatus.BAD_REQUEST: falta Authorization, body o no se envió ningún campo.
        HTTPStatus.UNAUTHORIZED: token no válido o no admin.
        HTTPStatus.NOT_FOUND: usuario no existe o no se actualizó.
        HTTPStatus.INTERNAL_SERVER_ERROR: error inesperado.
    """
    try:
        auth = request.headers.get("Authorization", "")
        if not auth.startswith("Bearer "):
            return jsonify({"ok": False, "error": "Falta Authorization Bearer"}), HTTPStatus.BAD_REQUEST


        token = auth.split(" ", 1)[1].strip()
        if not await comprobar_token_admin(token):
            return jsonify({"ok": False, "error": "Token no válido"}), HTTPStatus.UNAUTHORIZED
        
       
        body = (await request.get_json(silent=True))
        if body is None:
            return jsonify({'status': 'ERROR', 'message': 'Body JSON requerido'}), HTTPStatus.BAD_REQUEST
        
        username = body.get("name")
        password = body.get("password")
        nationality = body.get("nationality")

        if username is None and password is None and nationality is None:
            return jsonify({'status': 'ERROR', 'message': 'Debe proporcionarse al menos un campo a actualizar'}), HTTPStatus.BAD_REQUEST

        if password is not None:
            password = hashlib.sha512((password + SALT).encode('utf-8')).hexdigest()

        success, error_code = await update_user(uid, username, password, nationality)
        if not success:
            if error_code == "NOT_FOUND":
                return jsonify({'status': 'ERROR', 'message': 'Usuario no encontrado'}), HTTPStatus.NOT_FOUND
            if error_code == "NO_FIELDS":
                return jsonify({'status': 'ERROR', 'message': 'No se proporcionaron campos a actualizar'}), HTTPStatus.BAD_REQUEST
            return jsonify({'status': 'ERROR', 'message': 'Error inesperado del servidor'}), HTTPStatus.INTERNAL_SERVER_ERROR
        
        return jsonify({'status': 'OK'}), HTTPStatus.OK

    except Exception as exc:
        return jsonify({'status': 'ERROR', 'message': str(exc)}), HTTPStatus.INTERNAL_SERVER_ERROR

@app.route("/user/<uid>", methods=["DELETE"])
async def http_delete_user(uid):
    """
    Endpoint HTTP para eliminar un usuario.
    
    - Método: DELETE
    - Path: /user/<uid>
    - Headers: Authorization: Bearer <token_admin>
    - Comportamiento: Llama a delete_user(uid). Solo usuarios administradores pueden eliminar usuarios.
                     Elimina el usuario, su carrito y todas sus relaciones (CASCADE).
    - Respuestas esperadas:
        HTTPStatus.OK: {"status":"OK"} - Usuario eliminado exitosamente
        HTTPStatus.BAD_REQUEST: {"status":"ERROR", "message": "..."} - Falta Authorization Bearer
        HTTPStatus.UNAUTHORIZED: {"status":"ERROR", "message": "Token no válido"} - Token no válido o no es admin
        HTTPStatus.NOT_FOUND: {"status":"ERROR", "message": "Usuario no encontrado"} - Usuario no existe
        HTTPStatus.FORBIDDEN: {"status":"ERROR", "message": "No se puede eliminar el usuario administrador"} - Intento de eliminar admin
        HTTPStatus.INTERNAL_SERVER_ERROR: {"status":"ERROR", "message": "..."} - Error interno del servidor
    
    ADVERTENCIA: Operación destructiva. Se elimina el usuario, su carrito y todas sus relaciones.
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
            return jsonify({'status': 'ERROR', 'message': 'Soy una tetera, no puedo hacer café'}), HTTPStatus.IM_A_TEAPOT
        
        return jsonify({'status': 'OK'}), HTTPStatus.OK

    except Exception as exc:
        return jsonify({'status': 'ERROR', 'message': str(exc)}), HTTPStatus.INTERNAL_SERVER_ERROR

# -----------------------------------------------------------------------------
# Endpoints de Descuento de Usuarios
# -----------------------------------------------------------------------------

@app.route("/user/<uid>/discount", methods=["PUT"])
async def http_add_discount(uid):
    """
    Endpoint HTTP para asignar un descuento a un usuario.
    
    - Método: PUT
    - Path: /user/<uid>/discount
    - Headers: Authorization: Bearer <token_admin>
    - Body (JSON): {"discount": <int entre 1 y 100>}
    - Comportamiento: Verifica token admin y llama a add_discount(uid, discount).
    - Respuestas esperadas:
        HTTPStatus.OK: {"status": "OK"} - Descuento aplicado.
        HTTPStatus.BAD_REQUEST: faltan headers/body o discount fuera de rango/formato.
        HTTPStatus.UNAUTHORIZED: token no válido o no admin.
        HTTPStatus.NOT_FOUND: usuario no existe.
        HTTPStatus.INTERNAL_SERVER_ERROR: error inesperado.
    """
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        return jsonify({"ok": False, "error": "Falta Authorization Bearer"}), HTTPStatus.BAD_REQUEST

    token = auth.split(" ", 1)[1].strip()
    if not await comprobar_token_admin(token):
        return jsonify({"ok": False, "error": "Token no válido"}), HTTPStatus.UNAUTHORIZED
    
    body = (await request.get_json(silent=True))
    if body is None:
        return jsonify({'status': 'ERROR', 'message': 'Body JSON requerido'}), HTTPStatus.BAD_REQUEST
    
    discount = body.get("discount")
    if discount is None:
        return jsonify({'status': 'ERROR', 'message': 'Body JSON no contiene la clave "discount"'}), HTTPStatus.BAD_REQUEST
    try:
        discount = int(discount)
    except ValueError:
        return jsonify({'status': 'ERROR', 'message': 'El valor de "discount" debe ser un entero'}), HTTPStatus.BAD_REQUEST
    
    success, error_code = await add_discount(uid, discount)
    if not success:
        if error_code == "BAD_REQUEST":
            return jsonify({'status': 'ERROR', 'message': 'El porcentaje de descuento debe estar entre 1 y 100'}), HTTPStatus.BAD_REQUEST
        elif error_code == "USER_NOT_FOUND":
            return jsonify({'status': 'ERROR', 'message': 'Usuario no encontrado'}), HTTPStatus.NOT_FOUND
        else:
            return jsonify({'status': 'ERROR', 'message': 'Error inesperado del servidor'}), HTTPStatus.INTERNAL_SERVER_ERROR
    
    return jsonify({'status': 'OK'}), HTTPStatus.OK
        
@app.route("/user/<uid>/discount", methods=["DELETE"])
async def http_remove_discount(uid):
    """
    Endpoint HTTP para eliminar el descuento de un usuario (ponerlo a 0).
    
    - Método: DELETE
    - Path: /user/<uid>/discount
    - Headers: Authorization: Bearer <token_admin>
    - Comportamiento: Verifica token admin y llama a remove_discount(uid).
    - Respuestas esperadas:
        HTTPStatus.OK: {"status": "OK"} - Descuento eliminado.
        HTTPStatus.BAD_REQUEST: falta Authorization Bearer.
        HTTPStatus.UNAUTHORIZED: token no válido o no admin.
        HTTPStatus.NOT_FOUND: usuario no existe.
        HTTPStatus.INTERNAL_SERVER_ERROR: error inesperado.
    """
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        return jsonify({"ok": False, "error": "Falta Authorization Bearer"}), HTTPStatus.BAD_REQUEST


    token = auth.split(" ", 1)[1].strip()
    if not await comprobar_token_admin(token):
        return jsonify({"ok": False, "error": "Token no válido"}), HTTPStatus.UNAUTHORIZED
    
    success, error_code = await remove_discount(uid)
    if not success:
        if error_code == "USER_NOT_FOUND":
            return jsonify({'status': 'ERROR', 'message': 'Usuario no encontrado'}), HTTPStatus.NOT_FOUND
        else:
            return jsonify({'status': 'ERROR', 'message': 'Error inesperado del servidor'}), HTTPStatus.INTERNAL_SERVER_ERROR
    
    return jsonify({'status': 'OK'}), HTTPStatus.OK

@app.route("/user/<uid>/discount", methods=["GET"])
async def http_get_discount(uid):
    """
    Endpoint HTTP para consultar el descuento actual de un usuario.
    
    - Método: GET
    - Path: /user/<uid>/discount
    - Headers: Authorization: Bearer <token_usuario>
    - Comportamiento: Verifica que el token pertenezca al mismo usuario (uid) y llama a get_discount(uid).
    - Respuestas esperadas:
        HTTPStatus.OK: {"status": "OK", "discount": <int>} - Descuento devuelto.
        HTTPStatus.BAD_REQUEST: falta Authorization Bearer.
        HTTPStatus.UNAUTHORIZED: token no coincide con el usuario.
        HTTPStatus.NOT_FOUND: usuario no existe.
        HTTPStatus.INTERNAL_SERVER_ERROR: error inesperado.
    """
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        return jsonify({"ok": False, "error": "Falta Authorization Bearer"}), HTTPStatus.BAD_REQUEST

    token = auth.split(" ", 1)[1].strip()
    if (token_uid := await get_uid_by_token(token)) != uid:
        return jsonify({'status': 'ERROR', 'message': 'Token no válido para este usuario'}), HTTPStatus.UNAUTHORIZED

    discount, error_code = await get_discount(uid)
    if discount is None:
        if error_code == "USER_NOT_FOUND":
            return jsonify({'status': 'ERROR', 'message': 'Usuario no encontrado'}), HTTPStatus.NOT_FOUND
        else:
            return jsonify({'status': 'ERROR', 'message': 'Error inesperado del servidor'}), HTTPStatus.INTERNAL_SERVER_ERROR
    
    return jsonify({'status': 'OK', 'discount': discount}), HTTPStatus.OK


# =============================================================================
# PUNTO DE ENTRADA PRINCIPAL
# =============================================================================

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5050)
