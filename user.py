import pandas as pd
import os, uuid
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
    lib_name = usr_lib_dir + uid + ".txt"
    df.to_csv(lib_name, sep="\t", index=False)

    return uid, uuid.uuid5(Secret_uuid, uid)

def login_user(username, password):
    """
    
    """
    df = open_or_create_txt()
    
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

    df = open_or_create_txt()

    usuario = df[df["username"] == username]

    if not usuario.empty:
        return True
    else:
        return False

def open_or_create_txt():
    # Si el archivo existe, lo abre; si no, lo crea vacío
    if os.path.exists(users_file):
        df = pd.read_csv(users_file, sep="\t")
    else:
        df = pd.DataFrame(columns=["username", "password", "UID"])
        df.to_csv(users_file, sep="\t", index=False)
    return df

def change_pass(username, password):
    """
    Changes the pasword of the given user.

    Args:
        username (str): the name of the user
        password (str): the password of the user
    
    Returns:
        bool: Ture if succes, False if failed.
    """
    pass

def change_usrname():
    pass

def delete_user():
    pass


# --------------------------
# Servidor HTTP (Quart)
# --------------------------
app = Quart(__name__)


@app.route("/create_user/<username>", methods=["POST"])
async def http_create_user(username):
    try:
        body = (await request.get_json(silent=True))
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


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5050, debug=True)


# Preguntar:  
#   get_user_id: solo con user_name vale, no?
#   Formato de guardado de los files (files.txt/JSON) y los users (users.txt/JSON) tiene que estar en JSON o en txt?
#   Que es Bearer token? y como interactuan los dos microservicios?