import pandas as pd
import os, uuid
from quart import Quart, jsonify, request

Secret_uuid = uuid.UUID('00010203-0405-0607-0809-0a0b0c0d0e0f')
path = "resources/files/"

# TODO: Añadir comentarios funciones quart
# TODO: Añadir control con share_token
# TODO: testear + comprobar requisitos
# TODO: Revisar control de errores (opcional)

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
    if token != uuid.uuid5(Secret_uuid, uid):
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
        If the token is not provided only public files are listed.

        Args:
            uid (str): The user ID of the user.
            token (str, optional): The authentication token of the user. Defaults to None.

        Returns:
            list: A list of filenames in the user's library.
    """
    if token is not None and token == uuid.uuid5(Secret_uuid, uid):
        df = _open_library(uid)
        return df['name'].tolist()
    else:
        return None

# Hay que permitir acceso con token o con contraseña para ficheros privados
def read_file(uid, filename, token = None):
    """
        Read the content of a file in the user's library.
        If the token is provided the user can read both public and private files.
        If the token is not provided the user can only read public files.

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
        return None
    elif file_row.iloc[0]['visibility'] == 'public':
        return file_row.iloc[0]['content']
    elif token is not None and token == uuid.uuid5(Secret_uuid, uid) and file_row.iloc[0]['visibility'] == 'private':
        return file_row.iloc[0]['content']
    else:
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

    if token != uuid.uuid5(Secret_uuid, uid):
        print("Token inválido")
        return
    
    df = _open_library(uid)

    if filename in df['name'].values:
        df.loc[df['name'] == filename, 'content'] = new_content
        if visibility is not None:
            df.loc[df['name'] == filename, 'visibility'] = visibility
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
    if token != uuid.uuid5(Secret_uuid, uid):
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
    lib_name = path + uid + ".txt"
    df = pd.read_csv(lib_name, sep="\t")
    return df

# --------------------------
# Servidor HTTP (Quart)
# --------------------------
app = Quart(__name__)

@app.route("/create_file", methods=["POST"])
async def http_create_file():
    # --- Autenticación: Bearer token ---
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        return jsonify({"ok": False, "error": "Falta Authorization Bearer"}), 401

    token_str = auth.split(" ", 1)[1].strip()
    try:
        token = uuid.UUID(token_str)
    except ValueError:
        return jsonify({"ok": False, "error": "Formato de token inválido"}), 401
    
    # --- Cuerpo JSON ---
    try:
        body = (await request.get_json(silent=True))
        
        uid = body.get("uid")
        filename = body.get("filename")
        content = body.get("content")
        visibility = body.get("visibility, private")

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
    # --- Autenticación: Bearer token ---
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        return jsonify({"ok": False, "error": "Falta Authorization Bearer"}), 401

    token_str = auth.split(" ", 1)[1].strip()
    try:
        token = uuid.UUID(token_str)
    except ValueError:
        return jsonify({"ok": False, "error": "Formato de token inválido"}), 401
    
    # --- Cuerpo JSON ---
    try:
        body = (await request.get_json(silent=True))
        
        uid = body.get("uid")
        filename = body.get("filename")
        new_content = body.get("new_content")
        visibility = body.get("visibility, private")

    except Exception as exc:
        return jsonify({"status": "ERROR", "message": str(exc)}), 400
    
    if not uid or not filename or new_content is None:
        return jsonify({
            "ok": False,
            "error": "Campos requeridos: uid, filename, content"
        }), 401

    try:
        modify_file(uid, filename, new_content, token, visibility)
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
    # --- Autenticación: Bearer token ---
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        return jsonify({"ok": False, "error": "Falta Authorization Bearer"}), 401

    token_str = auth.split(" ", 1)[1].strip()
    try:
        token = uuid.UUID(token_str)
    except ValueError:
        return jsonify({"ok": False, "error": "Formato de token inválido"}), 401
    
    # --- Cuerpo JSON ---
    try:
        body = (await request.get_json(silent=True))
        
        uid = body.get("uid")
        filename = body.get("filename")

    except Exception as exc:
        return jsonify({"status": "ERROR", "message": str(exc)}), 400
    
    if not uid or not filename is None:
        return jsonify({
            "ok": False,
            "error": "Campos requeridos: uid, filename, content"
        }), 401

    try:
        remove_file(uid, filename, token)
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
    # --- Autenticación: Bearer token (en este caso no es necesaria siempre y cuando sea archivo publico)---
    auth = request.headers.get("Authorization", "")
    if auth.startswith("Bearer "):
        token_str = auth.split(" ", 1)[1].strip()
    try:
        if token_str:
            token = uuid.UUID(token_str)
        else:
            token = None
    except ValueError:
        return jsonify({"ok": False, "error": "Formato de token inválido"}), 401
    
    # --- Cuerpo JSON ---
    try:
        body = (await request.get_json(silent=True))
        
        uid = body.get("uid")
        filename = body.get("filename")

    except Exception as exc:
        return jsonify({"status": "ERROR", "message": str(exc)}), 400
    
    if not uid or not filename is None:
        return jsonify({
            "ok": False,
            "error": "Campos requeridos: uid, filename, content"
        }), 401

    try:
        read_file(uid, filename, token)
        return jsonify({
            "ok": True,
            "uid": uid,
            "filename": filename,
        }), 200
    except Exception as e:
        # Cualquier error no controlado
        return jsonify({"ok": False, "error": str(e)}), 500
    
@app.route("/list_files", methods=["DELETE"])
async def http_list_files():
    # --- Autenticación: Bearer token ---
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        return jsonify({"ok": False, "error": "Falta Authorization Bearer"}), 401

    token_str = auth.split(" ", 1)[1].strip()
    try:
        token = uuid.UUID(token_str)
    except ValueError:
        return jsonify({"ok": False, "error": "Formato de token inválido"}), 401
    
    # --- Cuerpo JSON ---
    try:
        body = (await request.get_json(silent=True))
        
        uid = body.get("uid")

    except Exception as exc:
        return jsonify({"status": "ERROR", "message": str(exc)}), 400
    
    if not uid is None:
        return jsonify({
            "ok": False,
            "error": "Campos requeridos: uid, filename, content"
        }), 401

    try:
        list_files(uid, token)
        return jsonify({
            "ok": True,
            "uid": uid,
        }), 200
    except Exception as e:
        # Cualquier error no controlado
        return jsonify({"ok": False, "error": str(e)}), 500
    
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5051, debug=True)
    