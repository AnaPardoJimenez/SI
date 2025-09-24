import pandas as pd
import os, uuid
from quart import Quart, jsonify, request

Secret_uuid = uuid.UUID('00010203-0405-0607-0809-0a0b0c0d0e0f')
user_file = "users.txt"

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
    df.to_csv(user_file, sep="\t", index=False)

    return uid, uuid.uuid5(Secret_uuid, uid)

def login_user(username, password):
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
    if os.path.exists(user_file):
        df = pd.read_csv(user_file, sep="\t")
    else:
        df = pd.DataFrame(columns=["username", "password", "UID"])
        df.to_csv(user_file, sep="\t", index=False)
    return df


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


@app.route("/get_user_uid/<username>", methods=["GET"])
async def http_get_user_uid(username):
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