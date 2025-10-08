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
        str: The token for the newly created user.
    """
    if(get_user_id(username) is not False):
        return login_user(username, password)
    
    df = open_or_create_txt()

    uid = uuid.uuid4()
    uid = str(uid)

    df.loc[len(df)] = [username, password, uid]
    # Persistir el nuevo usuario en disco
    df.to_csv(users_file, sep="\t", index=False)

    df = pd.DataFrame(columns=["name", "visibility", "content"])
    usr_lib_name = usr_lib_dir + uid + ".txt"
    df.to_csv(usr_lib_name, sep="\t", index=False)

    return uid, uuid.uuid5(Secret_uuid, uid)

def login_user(username, password):
    """
    Logs the user in using the username and password.

    Args:
        username (str): user name
        password (str): password

    Returns:
        tuple (uid, token): uid id the user id, and token is the "access key", proof that the client is logged in.
        If the username/password are incorrect, returns None.
    """
    df = open_users_txt()
    if df is None: return None
    
    usuario = df[
        (df["username"].astype(str).str.strip() == str(username).strip()) &
        (df["password"].astype(str).str.strip() == str(password).strip())
    ]
    
    if not usuario.empty:
        uid = usuario.iloc[0]["UID"]
        return uid, uuid.uuid5(Secret_uuid, uid)
    
    return None

def get_user_id(username):
    """
    Retrieve the user ID for the given username.
    
    Args:
        username (str): The username of the user.

    Returns:
        bool: True if user exists, False otherwise.
    """

    df = open_users_txt()
    if df is None: return False

    usuario = df[df["username"] == username]

    if not usuario.empty:
        return True
    else:
        return False

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
        DataFrame: descriptor of the file
        None if it fails (or the return value of failed pd.read_csv())
    """
    if os.path.exists(users_file):
        return pd.read_csv(users_file, sep="\t")
    else:
        return None

def change_pass(username: str, password: str, new_password: str):
    """
    Changes the pasword of the given user.

    Args:
        username (str): the name of the user
        password (str): the password of the user
        new_password (str): the new password
    
    Returns:
        bool: True if success, False if failed.
    """
    df = open_users_txt()
    if df is None or df.empty: return False
    
    usuario = df[
        (df["username"].astype(str).str.strip() == str(username).strip()) &
        (df["password"].astype(str).str.strip() == str(password).strip())
    ]
    if usuario is None:
        return False

    df.loc[df["username"] == username, "password"] = new_password
    df.to_csv(users_file, sep="\t", index=False)
    
    return True

def change_username(username: str, password: str, new_username: str):
    """
    Changes the user name of a given user.

    Args:
        username (str): user name
        password (str): password of the user
        new_username (str): new user name

    Returns:
        bool: True if success, False if failed
    """
    df = open_users_txt()
    if df is None: return False
    
    usuario = df[
        (df["username"].astype(str).str.strip() == str(username).strip()) &
        (df["password"].astype(str).str.strip() == str(password).strip())
    ]
    if usuario is None:
        return False

    df.loc[df["username"] == username, "username"] = new_username
    df.to_csv(users_file, sep="\t", index=False)
    
    return True

def delete_user(username: str, password: str):
    """
    Deletes the given user. _______________

    Args:
        username (str): user name
        password (str): password of the user

    Returns:
        bool: True if success, False if failed
    """
    df = open_users_txt()
    if df is None: return False

    usuario = df[
        (df["username"].astype(str).str.strip() == str(username).strip()) &
        (df["password"].astype(str).str.strip() == str(password).strip())
    ]

    if usuario is None:
        return False

    uid = df.loc[(df["username"] == username) & (df["password"] == password), "UID"].values[0]
    usr_lib_name = usr_lib_dir + uid + ".txt"

    if os.path.exists(usr_lib_dir):
        os.remove(usr_lib_name)

        df = df[~((df["username"] == username) & (df["password"] == password))]
        df.to_csv(users_file, sep="\t", index=False)

        return True

    return False



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
        200: {"status":"OK", "username": username, "UID": "<uid>"}
        400: parámetros faltantes
        500: error interno
    """
    try:
        body = (await request.get_json(silent=True))
        if body is None:
            return jsonify({"status": "ERROR", "message": "body requerido"}), 401
        
        password = body.get("password")
        if not password:
            return jsonify({"status": "ERROR", "message": "password requerido"}), 400

        result = create_user(username, password)
        if result is None:
            return jsonify({"status": "ERROR", "message": "no se pudo crear/iniciar sesión"}), 400

        uid, _token = result
        return jsonify({"status": "OK", "username": username, "UID": uid}), 200

    except Exception as exc:
        return jsonify({"status": "ERROR", "message": str(exc)}), 500


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

        password = body.get("password")

        if not password:
            return jsonify({"status": "ERROR", "message": "password requerido"}), 400

        login = login_user(username, password)

        if login is None:
            return jsonify({"status": "ERROR", "message": "credenciales inválidas"}), 401

        uid, _token = login
        return jsonify({"status": "OK", "UID": uid}), 200

    except Exception as exc:
        return jsonify({"status": "ERROR", "message": str(exc)}), 500


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
    df = await asyncio.to_thread(open_users_txt)
    if df is None:
        return jsonify({"status": "ERROR", "message": "no hay usuarios"}), 400

    uid = await asyncio.to_thread(get_user_id, username)
    if uid is False:
        return jsonify({"status": "ERROR", "message": "usuario no encontrado"}), 404

    return jsonify({"status": "OK", "UID": uid}), 200


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

        password = body.get("password")
        new_password = body.get("new_password")

        if not password:
            return jsonify({"status": "ERROR", "message": "password requerido"}), 402
        
        if not new_password:
            return jsonify({"status": "ERROR", "message": "nueva contraseña requerida"}), 403

        result = change_pass(username, password, new_password)
        if result is False:
            return jsonify({"status": "ERROR", "message": "usuario no encontrado"}), 404

        return jsonify({"status": "OK"}), 200

    except Exception as exc:
        return jsonify({"status": "ERROR", "message": str(exc)}), 500


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

        password = body.get("password")
        new_username = body.get("new_username")

        if not password:
            return jsonify({"status": "ERROR", "message": "password requerido"}), 400
        
        if not new_username:
            return jsonify({"status": "ERROR", "message": "nuevo nombre de usuario requerido"}), 400

        result = change_username(username, password, new_username)
        if result is False:
            return jsonify({"status": "ERROR", "message": "usuario no encontrado"}), 404
        
        return jsonify({"status": "OK"}), 200

    except Exception as exc:
        return jsonify({"status": "ERROR", "message": str(exc)}), 500


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

        password = body.get("password")

        if not password:
            return jsonify({"status": "ERROR", "message": "password requerido"}), 400
        
        result = delete_user(username, password)
        if result is False:
            return jsonify({"status": "ERROR", "message": "Not Found"}), 404
        
        return jsonify({"status": "OK"}), 200

    except Exception as exc:
        return jsonify({"status": "ERROR", "message": str(exc)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5050, debug=True)


# Preguntar:  
#   get_user_id: solo con user_name vale, no?
#   Formato de guardado de los files (files.txt/JSON) y los users (users.txt/JSON) tiene que estar en JSON o en txt?
#   Que es Bearer token? y como interactuan los dos microservicios?