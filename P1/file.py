import pandas as pd
import os, uuid
import re
from quart import Quart, jsonify, request
from datetime import datetime, timedelta, timezone

Secret_uuid = uuid.UUID('00010203-0405-0607-0809-0a0b0c0d0e0f')
path = "resources/files/"

def create_file(uid, token, filename, content, visibility="private"):
    """
        Add a new file to the library of the user identified by uid.
        If the file already exists, update its content and/or visibility.

        Args:
            uid (str): The user ID of the user.
            filename (str): The name of the file to be created.
            content (str): The content of the file.
            visibility (str, optional): The visibility of the file. Can be "public" or "private". Defaults to "private".
    """

    # Excluye a los usuarios no dueños del fichero
    if uuid.UUID(token) != uuid.uuid5(Secret_uuid, uid):
        print("Token inválido")
        return
    
    df = _open_library(uid)

    if filename in df['name'].values:
        df.loc[df['name'] == filename, 'content'] = content
        if visibility is not None:
            df.loc[df['name'] == filename, 'visibility'] = visibility
    else:
        nueva_fila = {'name': filename, 'visibility': visibility, 'content': content}
        df.loc[len(df)] = nueva_fila
    
    df.to_csv(path + uid + ".txt", sep="\t", index=False)

def list_files(uid, token = None):
    """
        List all files in the user's library.
        If the token is provided all the files (public and private are listed).

        Args:
            uid (str): The user ID of the user.
            token (str, optional): The authentication token of the user. Defaults to None.

        Returns:
            list: A list of filenames in the user's library.
    """
    if token is not None and uuid.UUID(token) == uuid.uuid5(Secret_uuid, uid):
        df = _open_library(uid)
        return df['name'].tolist()
    else:
        return None

# Hay que permitir acceso con token o con contraseña para ficheros privados
def read_file(uid, filename, token = None):
    """
        Read the content of a file in the user's library.
        If the token is provided the user can read both public and private files.
        If the token is not provided the user can only read public files unless it provides
        a valid share token.

        Args:
            uid (str): The user ID of the user.
            filename (str): The name of the file to be read.
            token (str, optional): The authentication token of the user. Defaults to None.

        Returns:
            str: The content of the file.
    """
    df = _open_library(uid)

    file_row = df[df['name'] == filename]

    if file_row.empty:
        print("El fichero no existe")
        return None
    elif file_row.iloc[0]['visibility'] == 'public':
        print("El fichero es público")
        return file_row.iloc[0]['content']
    elif file_row.iloc[0]['visibility'] == 'private' and token is not None:
        token = token.strip()

        if token.count(".") >= 3 and _check_share_token(filename, token, uid):
            print("El fichero es privado pero puedes leerlo (share token)")
            return file_row.iloc[0]['content']

        try:
            if token.count(".") < 3 and uuid.UUID(token) == uuid.uuid5(Secret_uuid, uid):
                print("El fichero es privado pero puedes leerlo (owner)")
                return file_row.iloc[0]['content']
        except Exception:
            pass

        print("No tienes permiso para leer este fichero")
        print(token)
        return None
    else:
        print("No tienes permiso para leer este fichero")
        return None

def modify_file(uid, filename, new_content, token, visibility=None):
    """
        Modify the content of a file in the user's library.
        The user must provide a valid token to modify a file.

        Args:
            uid (str): The user ID of the user.
            filename (str): The name of the file to be modified.
            new_content (str): The new content of the file.
            token (str): The authentication token of the user.
        Returns:
            bool: True if the file was modified successfully, False otherwise.
    """
    if uuid.UUID(token) != uuid.uuid5(Secret_uuid, uid):
        print("Token inválido")
        return False
    
    df = _open_library(uid)

    if filename in df['name'].values:
        df.loc[df['name'] == filename, 'content'] = new_content
        if visibility is not None:
            df.loc[df['name'] == filename, 'visibility'] = visibility
        df.to_csv(path + uid + ".txt", sep="\t", index=False)
        return True
    else:
        print("El fichero no existe")
        return False

def remove_file(uid, filename, token):
    """
        Remove a file from the user's library.
        The user must provide a valid token to remove a file.

        Args:
            uid (str): The user ID of the user.
            filename (str): The name of the file to be removed.
            token (str): The authentication token of the user.
            
        Returns:
            bool: True if the file was removed successfully, False otherwise.
    """
    if uuid.UUID(token) != uuid.uuid5(Secret_uuid, uid):
        print("Token inválido")
        return False
    
    df = _open_library(uid)

    if filename in df['name'].values:
        df.drop(df[df['name'] == filename].index, inplace=True)
        df.to_csv(path + uid + ".txt", sep="\t", index=False)
        return True
    else:
        print("El fichero no existe")
        return False

def _open_library(uid):
    """
        Open the user's library file.
        If the library file does not exist, create a new one.

        Args:
            uid (str): The user ID of the user.

        Returns:
            pd.DataFrame: The user's library as a pandas DataFrame.
    """
    lib_name = os.path.join(path, uid + ".txt")
    if not os.path.exists(lib_name):
        return pd.DataFrame(columns=["name", "visibility", "content"])
    return pd.read_csv(lib_name, sep="\t")


def _create_share_token(minutes: int, uid: str, login_token: str, filename: str) -> str:
    """
        Private function to create a share token 

        Args:
            minutes (int): number of minutes that the link will be valid
            uid (str): id of the user
            login_token (str): token of the user 
            filename (str): name of the file to share

        Returns:
            The shared token with format UID.nombre.exp.hash where hash 
            is the previous information as sha-1
    """
    if uuid.UUID(login_token) != uuid.uuid5(Secret_uuid, uid):
        return None
    df = _open_library(uid)
    if df[df['name'] == filename].empty:
        return None  # no existe el fichero

    exp_ts = int((datetime.now(timezone.utc) + timedelta(minutes=minutes)).timestamp())
    signature = uuid.uuid5(Secret_uuid, f"{uid}.{filename}.{exp_ts}")
    return f"{uid}.{filename}.{exp_ts}.{signature}"

def _check_share_token(file_name: str, share_token: str, user: str) -> bool:
    """
        Function to check if a share token is valid

        Args: 
            file_name (str): name of the file to share
            share_token (str): the share token
            user (str): uid of the owner of the file
        
        Returns: 
            True if valid, False otherwise
    """
    share_token = share_token.strip()

    first_dot = share_token.find(".")
    if first_dot <= 0:
        return False
    uid_tk = share_token[:first_dot]
    rest = share_token[first_dot + 1:]

    try:
        filename_tk, exp_str, sig_str = rest.rsplit(".", 2)
        exp_ts = int(exp_str)
    except Exception:
        return False  

    if uid_tk != user or filename_tk != file_name:
        return False

    df = _open_library(uid_tk)
    if df[df['name'] == filename_tk].empty:
        return False

    now_ts = int(datetime.now(timezone.utc).timestamp())
    if now_ts > exp_ts:
        return False

    expected = uuid.uuid5(Secret_uuid, f"{uid_tk}.{filename_tk}.{exp_ts}")
    try:
        provided = uuid.UUID(sig_str.strip())
    except Exception:
        return False

    return str(expected) == str(provided)

# --------------------------
# Servidor HTTP (Quart)
# --------------------------
app = Quart(__name__)

@app.route("/create_file", methods=["POST"])
async def http_create_file():
    """
        Create a new file in the user's library.
        The user must provide a valid token to create a file.
        The request must be a JSON object with the following fields:
            - uid: The user ID of the user.
            - filename: The name of the file to be created.
            - content: The content of the file.
            - visibility: The visibility of the file. Can be "public" or "private". Defaults to "private".
        Returns a JSON object with the following fields:
            - ok: True if the file was created successfully, False otherwise.
            - uid: The user ID of the user.
            - filename: The name of the file.
            - visibility: The visibility of the file.
    """
    # --- Autenticación: Bearer token ---
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        return jsonify({"ok": False, "error": "Falta Authorization Bearer"}), 401

    token = auth.split(" ", 1)[1].strip()

    # --- Cuerpo JSON ---
    try:
        body = (await request.get_json(silent=True))
        
        uid = body.get("uid")
        filename = body.get("filename")
        content = body.get("content")
        visibility = body.get("visibility")
        if(visibility is None):
            visibility = "private"

    except Exception as exc:
        return jsonify({"status": "ERROR", "message": str(exc)}), 400
    
    if not uid or not filename or content is None:
        return jsonify({
            "ok": False,
            "error": "Campos requeridos: uid, filename, content"
        }), 401

    try:
        create_file(uid, token, filename, content, visibility)
        return jsonify({
            "ok": True,
            "uid": uid,
            "filename": filename,
            "visibility": visibility
        }), 200
    except Exception as e:
        # Cualquier error no controlado
        return jsonify({"ok": False, "error": str(e)}), 500
    
@app.route("/modify_file", methods=["PUT"])
async def http_modify_file():
    """
        Modify the content of a file in the user's library.
        The user must provide a valid token to modify a file.
        The request must be a JSON object with the following fields:
            - uid: The user ID of the user.
            - filename: The name of the file to be modified.
            - new_content: The new content of the file.
            - visibility: The visibility of the file. Can be "public" or "private". Defaults to "private".
        Returns a JSON object with the following fields:
            - ok: True if the file was modified successfully, False otherwise.
            - uid: The user ID of the user.
            - filename: The name of the file.
            - visibility: The visibility of the file.
    """
    # --- Autenticación: Bearer token ---
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        return jsonify({"ok": False, "error": "Falta Authorization Bearer"}), 401

    token = auth.split(" ", 1)[1].strip()
    
    # --- Cuerpo JSON ---
    try:
        body = (await request.get_json(silent=True))
        
        uid = body.get("uid")
        filename = body.get("filename")
        new_content = body.get("new_content")
        visibility = body.get("visibility")
        if(visibility is None):
            visibility = "private"

    except Exception as exc:
        return jsonify({"status": "ERROR", "message": str(exc)}), 400
    
    if not uid or not filename or new_content is None:
        return jsonify({
            "ok": False,
            "error": "Campos requeridos: uid, filename, content"
        }), 401

    try:
        rst = modify_file(uid, filename, new_content, token, visibility)
        if rst is False:
            return jsonify({
                "ok": False,
                "error": "No tienes permiso para modificar este fichero o no existe"
            }), 403
        return jsonify({
            "ok": True,
            "uid": uid,
            "filename": filename,
            "visibility": visibility
        }), 200
    except Exception as e:
        # Cualquier error no controlado
        return jsonify({"ok": False, "error": str(e)}), 500
    
@app.route("/remove_file", methods=["DELETE"])
async def http_remove_file():
    """
        Remove a file from the user's library.
        The user must provide a valid token to remove a file.
        The request must be a JSON object with the following fields:
            - uid: The user ID of the user.
            - filename: The name of the file to be removed.
        Returns a JSON object with the following fields:
            - ok: True if the file was removed successfully, False otherwise.
            - uid: The user ID of the user.
            - filename: The name of the file.
    """
    # --- Autenticación: Bearer token ---
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        return jsonify({"ok": False, "error": "Falta Authorization Bearer"}), 401

    token = auth.split(" ", 1)[1].strip()
    
    # --- Cuerpo JSON ---
    try:
        body = (await request.get_json(silent=True))
        
        uid = body.get("uid")
        filename = body.get("filename")

    except Exception as exc:
        return jsonify({"status": "ERROR", "message": str(exc)}), 400
    
    if not uid or filename is None:
        return jsonify({
            "ok": False,
            "error": "Campos requeridos: uid, filename, content"
        }), 401

    try:
        rst = remove_file(uid, filename, token)
        if rst is False:
            return jsonify({
                "ok": False,
                "error": "No tienes permiso para eliminar este fichero o no existe"
            }), 403
        return jsonify({
            "ok": True,
            "uid": uid,
            "filename": filename,
        }), 200
    except Exception as e:
        # Cualquier error no controlado
        return jsonify({"ok": False, "error": str(e)}), 500
    
@app.route("/read_file", methods=["GET"])
async def http_read_file():
    """
        Read the content of a file in the user's library.
        If the token is provided the user can read both public and private files (if theirs).
        If the token is not provided the user can only read public files.
        The request must be a JSON object with the following fields:
            - uid: The user ID of the user.
            - filename: The name of the file to be read.
        Returns a JSON object with the following fields:
            - ok: True if the file was read successfully, False otherwise.
            - uid: The user ID of the user.
            - filename: The name of the file.
            - content: The content of the file.
    """
    # --- Autenticación: Bearer token (en este caso no es necesaria siempre y cuando sea archivo publico)---
    auth = request.headers.get("Authorization", "")
    if auth.startswith("Bearer "):
        token = auth.split(" ", 1)[1].strip()
    else:
        token = None
    
    # --- Cuerpo JSON ---
    try:
        body = (await request.get_json(silent=True))
        
        uid = body.get("uid")
        filename = body.get("filename")

    except Exception as exc:
        return jsonify({"status": "ERROR", "message": str(exc)}), 400
    
    if not uid or filename is None:
        return jsonify({
            "ok": False,
            "error": "Campos requeridos: uid, filename, content"
        }), 401

    try:
        content = read_file(uid, filename, token)
        if content is None:
            return jsonify({
                "ok": False,
                "error": "No tienes permiso para leer este fichero o no existe"
            }), 403
        
        return jsonify({
            "ok": True,
            "uid": uid,
            "filename": filename,
            "content": content
        }), 200
    except Exception as e:
        # Cualquier error no controlado
        return jsonify({"ok": False, "error": str(e)}), 500
    
@app.route("/list_files", methods=["GET"])
async def http_list_files():
    """
        List all files in the user's library.
        If the token is provided all the files (public and private are listed).
        If the token is not provided only public files are listed.
        The request must be a JSON object with the following fields:
            - uid: The user ID of the user.
        Returns a JSON object with the following fields:
            - ok: True if the files were listed successfully, False otherwise.
            - uid: The user ID of the user.
            - files: A list of filenames in the user's library.
    """
    # --- Autenticación: Bearer token ---
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        return jsonify({"ok": False, "error": "Falta Authorization Bearer"}), 401

    token = auth.split(" ", 1)[1].strip()
    
    # --- Cuerpo JSON ---
    try:
        body = (await request.get_json(silent=True))
        
        uid = body.get("uid")

    except Exception as exc:
        return jsonify({"status": "ERROR", "message": str(exc)}), 400
    
    if uid is None:
        return jsonify({
            "ok": False,
            "error": "Campos requeridos: uid"
        }), 401

    try:
        files = list_files(uid, token)
        return jsonify({
            "ok": True,
            "uid": uid,
            "files": files
        }), 200
    except Exception as e:
        # Cualquier error no controlado
        return jsonify({"ok": False, "error": str(e)}), 500

@app.route("/create_share_token", methods=["POST"])
async def http_create_share_token():
    """
        Creates a valid share token if the uid passed and token verify
        The request must be a JSON object with the following fields:
            - uid: The user ID
            - filename: The file to share
            - minutes: The number of minutes that the link will be valid
        Returns a JSON object with the following fields:
            - ok: True is the share token was created successfully
            - share_token: the share token created
    """
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        return jsonify({"ok": False, "error": "Falta Authorization Bearer"}), 401
    login_token = auth.split(" ", 1)[1].strip()

    body = (await request.get_json(silent=True)) or {}
    uid = body.get("uid")
    filename = body.get("filename")
    minutes = body.get("minutes", 1)

    if not uid or not filename:
        return jsonify({"ok": False, "error": "Campos requeridos: uid, filename"}), 401

    share = _create_share_token(minutes, uid, login_token, filename)
    if not share:
        return jsonify({"ok": False, "error": "No se pudo crear el enlace (token inválido o fichero inexistente)"}), 403

    return jsonify({"ok": True, "share_token": share}), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5051, debug=True)
    