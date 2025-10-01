import pandas as pd
import os, uuid
from quart import Quart, jsonify, request


def create_file(uid, filename, content):
    """
        Add a new file to the library of the user identified by uid.

        Args:
            uid (str): The user ID of the user.
            filename (str): The name of the file to be created.
            content (str): The content of the file.
        
        Returns:
            bool: True if the file was created successfully, False otherwise.
    """
    pass

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
    pass

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
    pass

def modify_file(uid, filename, new_content, token):
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
    pass

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
    pass

"""
def compute_token(uid: str) -> str:
    return hashlib.sha1(uid.encode()).hexdigest()

@app.route("/create_file", methods=["POST"])
def http_create_file():
    try:
        auth = request.headers.get("Authorization", "")
        if not auth.startswith("Bearer "):
            return jsonify({"status": "ERROR", "message": "token requerido"}), 401

        token = auth.split(" ", 1)[1]

        body = request.get_json(silent=True) or {}
        uid = body.get("uid")
        filename = body.get("filename")
        content = body.get("content", "")

        if not uid or not filename:
            return jsonify({"status": "ERROR", "message": "uid y filename requeridos"}), 400

        # Validar token = sha1(UID)
        if token != compute_token(uid):
            return jsonify({"status": "ERROR", "message": "token inválido"}), 403

        # Guardar fichero en disco en el cwd
        with open(filename, "w", encoding="utf-8") as f:
            f.write(content)

        return jsonify({"status": "OK", "filename": filename}), 200
    except Exception as exc:
        return jsonify({"status": "ERROR", "message": str(exc)}), 500

"""
if __name__ == "__main__":
    # Arranca el microservicio de ficheros en 0.0.0.0:5051
    app.run(host="127.0.0.1", port=5051, debug=True)


