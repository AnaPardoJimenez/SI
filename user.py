from errno import errorcode
import pandas as pd
import os, uuid, asyncio, time
from quart import Quart, jsonify, request

Secret_uuid = uuid.UUID('00010203-0405-0607-0809-0a0b0c0d0e0f')
users_file = "resources/users.txt"
usr_lib_dir = "resources/files/"

def create_user(username, password):
    """
    Create a new user with the given username, email, and password.
    
    Args:
        username (str): The username of the new user.
        email (str): The email address of the new user.
        password (str): The password for the new user.

    Returns:
        tuple: (uid, token, was_created: bool) where was_created is True if new user was created
    """
    # Si el usuario ya existe, hacer login en su lugar
    uid, error_code = get_user_id(username)
    print(username)
    if error_code == 'OK':
        uid, token, login_error = login_user(username, password)
        if login_error != "OK":
            return None
        return uid, token, False  # No se creó, ya existía
    
    df = open_or_create_txt()

    uid = uuid.uuid4()
    uid = str(uid)

    df.loc[len(df)] = [username, password, uid]
    # Persistir el nuevo usuario en disco
    df.to_csv(users_file, sep="\t", index=False)

    df = pd.DataFrame(columns=["name", "visibility", "content"])
    usr_lib_name = usr_lib_dir + uid + ".txt"
    df.to_csv(usr_lib_name, sep="\t", index=False)

    return uid, uuid.uuid5(Secret_uuid, uid), True  # Se creó nuevo usuario

def login_user(username, password):
    """
    Logs the user in using the username and password.

    Args:
        username (str): user name
        password (str): password

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
    Retrieve the user ID for the given username.
    
    Args:
        username (str): The username of the user.

    Returns:
        tuple: (exists: bool, error_code: str)
            - (True, "OK") si el usuario existe
            - (False, "USER_NOT_FOUND") si el usuario no existe (pero el archivo se leyó bien)
            - (False, error_code) si hubo error al leer el archivo
    """

    df, error_code = open_users_txt()
    if error_code != "OK":
        return False, error_code

    usuario = df[df["username"] == username]

    if not usuario.empty:
        uid = usuario.iloc[0]["UID"]
        return uid, "OK"
    else:
        return False, "USER_NOT_FOUND"

def open_or_create_txt():
    """
    Opens the users file or creates it if it does not exist.

    Returns: 
        DataFrame: descriptor of the file
    """
    if os.path.exists(users_file):
        return pd.read_csv(users_file, sep="\t")
    
    df = pd.DataFrame(columns=["username", "password", "UID"])
    df.to_csv(users_file, sep="\t", index=False)
    return df

def open_users_txt():
    """
    Opens the users file. Fails if it does not exist.

    Returns:
        tuple: (DataFrame or None, error_code: str)
            - (df, "OK") si todo va bien
            - (None, "FILE_NOT_FOUND") si el archivo no existe
            - (None, "PERMISSION_DENIED") si no hay permisos para leer
            - (None, "FILE_CORRUPTED") si el archivo está corrupto o tiene formato inválido
            - (None, "UNKNOWN_ERROR") para otros errores inesperados
    """
    # Verificar si el archivo existe
    if not os.path.exists(users_file):
        return None, "FILE_NOT_FOUND"
    
    # Intentar leer el archivo, capturando diferentes tipos de errores
    try:
        df = pd.read_csv(users_file, sep="\t")
        return df, "OK"
    
    except PermissionError:
        # No tenemos permisos para leer el archivo
        return None, "PERMISSION_DENIED"
    
    except pd.errors.EmptyDataError:
        # El archivo está vacío o corrupto
        return None, "FILE_CORRUPTED"
    
    except pd.errors.ParserError:
        # El archivo tiene un formato inválido (no se puede parsear)
        return None, "FILE_CORRUPTED"
    
    except Exception as e:
        # Cualquier otro error inesperado
        print(f"Error inesperado al leer {users_file}: {type(e).__name__}: {e}")
        return None, "UNKNOWN_ERROR"

def change_pass(username: str, password: str, new_password: str):
    """
    Changes the pasword of the given user.

    Args:
        username (str): the name of the user
        password (str): the password of the user
        new_password (str): the new password
    
    Returns:
        tuple: (success: bool, error_code: str)
            - (True, "OK") si se cambió correctamente
            - (False, "NOT_FOUND") si el usuario no existe
            - (False, "UNAUTHORIZED") si la contraseña es incorrecta
            - (False, error_code) si hubo error al leer el archivo
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

    df.loc[df["username"] == username, "password"] = new_password
    df.to_csv(users_file, sep="\t", index=False)
    
    return True, "OK"

def change_username(username: str, password: str, new_username: str):
    """
    Changes the user name of a given user.

    Args:
        username (str): user name
        password (str): password of the user
        new_username (str): new user name

    Returns:
        tuple: (success: bool, error_code: str)
            - (True, "OK") si se cambió correctamente
            - (False, "NOT_FOUND") si el usuario no existe
            - (False, "UNAUTHORIZED") si la contraseña es incorrecta
            - (False, error_code) si hubo error al leer el archivo
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

    df.loc[df["username"] == username, "username"] = new_username
    df.to_csv(users_file, sep="\t", index=False)
    
    return True, "OK"

def delete_user(username: str, password: str):
    """
    Deletes the given user. _______________

    Args:
        username (str): user name
        password (str): password of the user

    Returns:
        tuple: (success: bool, error_code: str)
            - (True, "OK") si se eliminó correctamente
            - (False, "NOT_FOUND") si el usuario no existe
            - (False, "UNAUTHORIZED") si la contraseña es incorrecta
            - (False, error_code) si hubo error al leer el archivo
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



def handle_file_error(error_code):
    """
    Convierte códigos de error de archivo en respuestas HTTP apropiadas.
    
    Args:
        error_code (str): Código de error de open_users_txt()
    
    Returns:
        tuple: (jsonify response, http_status_code) o None si no hay error
    """
    if error_code == "FILE_NOT_FOUND":
        return jsonify({
            'status': 'ERROR', 
            'message': 'El archivo de usuarios no existe',
            'details': 'El servidor no tiene el archivo users.txt'
        }), 500
    
    elif error_code == "PERMISSION_DENIED":
        return jsonify({
            'status': 'ERROR', 
            'message': 'Error de permisos',
            'details': 'El servidor no tiene permisos para leer users.txt'
        }), 500
    
    elif error_code == "FILE_CORRUPTED":
        return jsonify({
            'status': 'ERROR', 
            'message': 'Archivo de usuarios corrupto',
            'details': 'El archivo users.txt tiene un formato inválido o está corrupto'
        }), 500
    
    elif error_code == "UNKNOWN_ERROR":
        return jsonify({
            'status': 'ERROR', 
            'message': 'Error inesperado del servidor',
            'details': 'Revisa los logs del servidor'
        }), 500
    
    return None  # No hay error


# --------------------------
# Servidor HTTP (Quart)
# --------------------------
app = Quart(__name__)


@app.route("/create_user/<username>", methods=["POST"])
async def http_create_user(username):
    """
    Crear usuario.
    - Body (JSON): {"password": "<password>"}
    - Comportamiento esperado: llamar a create_user(username, password)
    - Respuestas esperadas:
        201: {"status":"OK", "username": username, "UID": "<uid>"} - Usuario creado
        200: {"status":"OK", "username": username, "UID": "<uid>"} - Usuario ya existía, hizo login
        401: Credenciales incorrectas (si usuario existe pero contraseña es incorrecta)
        400: Parámetros faltantes
        500: Error interno
    """
    try:
        body = (await request.get_json(silent=True))
        if body is None:
            return jsonify({'status': 'ERROR', 'message': 'Body JSON requerido'}), 400
        
        password = body.get("password")
        if not password:
            return jsonify({'status': 'ERROR', 'message': 'Body JSON no contiene la clave "password"'}), 400

        result = create_user(username, password)
        if result is None:
            return jsonify({'status': 'ERROR', 'message': 'Credenciales incorrectas'}), 401

        uid, token, was_created = result
        
        # Si se creó un nuevo usuario, devolver 201 Created
        # Si ya existía y se hizo login, devolver 200 OK
        status_code = 201 if was_created else 200
        return jsonify({'status': 'OK', 'username': username, 'UID': uid, 'Token': token}), status_code

    except Exception as exc:
        return jsonify({'status': 'ERROR', 'message': str(exc)}), 500


@app.route("/login/<username>", methods=["GET"])
async def http_login(username):
    """
    Login de usuario.
    - Body (JSON): {"password": "<password>"}
    - Comportamiento esperado: llamar a login_user(username, password)
    - Respuestas esperadas:
        200: {"status":"OK", "UID":"<uid>"}
        401: credenciales inválidas
        400: parámetros faltantes
        500: error interno
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


@app.route("/get_user_id/<username>", methods=["GET"])
async def http_get_user_id(username):
    """
    Comprobar existencia de usuario / recuperar ID.
    - Query / Path: username
    - Comportamiento esperado: llamar a get_user_id(username)
    - Respuestas esperadas:
        200: {"exists": true/false, "username": "<username>"}
        500: error interno
    - Nota: get_user_id en el código actual devuelve True/False; aquí decidir si devolver UID real.
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


# -------------------
# Modificación de usuario
# -------------------

@app.route("/change_pass/<username>", methods=["POST"])
async def http_change_pass(username):
    """
    Cambiar contraseña de un usuario.
    - Body (JSON): {"password":"<current>", "new_password":"<nuevo>"}
    - Comportamiento esperado: invocar change_pass(username, password, new_password)
    - Respuestas esperadas:
        200: {"status":"OK"}
        400: parámetros faltantes
        401/403: credenciales inválidas
        500: error interno
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


@app.route("/change_username/<username>", methods=["POST"])
async def http_change_username(username):
    """
    Cambiar nombre de usuario.
    - Body (JSON): {"password":"<password>", "new_username":"<nuevo>"}
    - Comportamiento esperado: invocar change_username(username, password, new_username)
    - Respuestas esperadas:
        200: {"status":"OK"}
        400/401/403/500 según casos
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


@app.route("/delete_user/<username>", methods=["POST"])
async def http_delete_user(username):
    """
    Eliminar usuario.
    - Body (JSON): {"password":"<password>"}
    - Comportamiento esperado: invocar delete_user(username, password)
    - Respuestas esperadas:
        200: {"status":"OK"}
        400: parámetros faltantes
        401/403: credenciales inválidas
        404: usuario no encontrado
        500: error interno
    - ADVERTENCIA: operación destructiva — confirmar autenticación/autoridad.
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

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5050, debug=True)