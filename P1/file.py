"""
file.py - Sistema de Gestión de Archivos con API REST

Este módulo implementa un sistema completo de gestión de archivos de usuario con 
funcionalidades de creación, lectura, modificación y eliminación, expuesto a través 
de una API REST construida con Quart.

Funcionalidades principales:
    - Creación y modificación de archivos de usuario
    - Gestión de visibilidad (público/privado)
    - Sistema de tokens de compartición con expiración temporal
    - Almacenamiento persistente en archivos CSV por usuario
    - API REST con endpoints HTTP asíncronos
    - Autenticación mediante tokens Bearer

Estructura de datos:
    - Archivos de usuario: almacenados en resources/files/<uid>.txt
    - Cada archivo contiene: nombre, visibilidad, contenido
    - Tokens de compartición: formato UID.filename.timestamp.hash

Autor: Juan Larrondo Fernández de Córdoba y Ana Pardo Jiménez
Fecha de creación: 14-9-2025
Última modificación: 11-10-2025
Versión: 3.0.0
Python: 3.7+
Dependencias: pandas, quart, datetime

Uso:
    python file.py
    
El servidor se ejecutará en http://0.0.0.0:5051
"""

import pandas as pd
import os, uuid
from quart import Quart, jsonify, request
from datetime import datetime, timedelta, timezone

# =============================================================================
# CONFIGURACIÓN Y CONSTANTES
# =============================================================================

Secret_uuid = uuid.UUID('00010203-0405-0607-0809-0a0b0c0d0e0f')
path = "resources/files/"

# =============================================================================
# FUNCIONES DE GESTIÓN DE ARCHIVOS
# =============================================================================

def create_file(uid, token, filename, content, visibility="private"):
    """
    Crea un nuevo archivo en la biblioteca del usuario o actualiza uno existente.
    
    Si el archivo ya existe, actualiza su contenido y/o visibilidad.
    Verifica que el token proporcionado sea válido para el usuario.

    Args:
        uid (str): El ID de usuario del propietario del archivo.
        token (str): Token de autenticación del usuario.
        filename (str): El nombre del archivo a crear o actualizar.
        content (str): El contenido del archivo.
        visibility (str, optional): La visibilidad del archivo. Puede ser "public" o "private". Por defecto "private".

    Returns:
        None: La función no retorna valor, pero actualiza el archivo en disco.
    """

    # Excluye a los usuarios no dueños del fichero
    if uuid.UUID(token) != uuid.uuid5(Secret_uuid, uid):
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
    Lista todos los archivos en la biblioteca del usuario.
    
    Si se proporciona un token válido, se listan todos los archivos (públicos y privados).
    Si no se proporciona token, solo se pueden listar archivos públicos.

    Args:
        uid (str): El ID de usuario del propietario de la biblioteca.
        token (str, optional): Token de autenticación del usuario. Por defecto None.

    Returns:
        list or None: Lista de nombres de archivos en la biblioteca del usuario, 
                     o None si no se tiene permiso de acceso.
    """
    if token is not None and uuid.UUID(token) == uuid.uuid5(Secret_uuid, uid):
        df = _open_library(uid)
        return df['name'].tolist()
    else:
        return None

def read_file(uid, filename, token = None):
    """
    Lee el contenido de un archivo en la biblioteca del usuario.
    
    Si se proporciona un token válido, el usuario puede leer archivos públicos y privados.
    Si no se proporciona token, el usuario solo puede leer archivos públicos, a menos que
    proporcione un token de compartición válido.

    Args:
        uid (str): El ID de usuario del propietario del archivo.
        filename (str): El nombre del archivo a leer.
        token (str, optional): Token de autenticación del usuario o token de compartición. Por defecto None.

    Returns:
        str or None: El contenido del archivo si se tiene permiso de lectura, 
                    None si no se tiene permiso o el archivo no existe.
    """
    df = _open_library(uid)

    file_row = df[df['name'] == filename]

    if file_row.empty:
        return None
    elif file_row.iloc[0]['visibility'] == 'public':
        return file_row.iloc[0]['content']
    elif file_row.iloc[0]['visibility'] == 'private' and token is not None:
        token = token.strip()

        if token.count(".") >= 3 and _check_share_token(filename, token, uid):
            return file_row.iloc[0]['content']

        try:
            if token.count(".") < 3 and uuid.UUID(token) == uuid.uuid5(Secret_uuid, uid):
                return file_row.iloc[0]['content']
        except Exception:
            pass

        return None
    else:
        return None

def modify_file(uid, filename, new_content, token, visibility=None):
    """
    Modifica el contenido de un archivo en la biblioteca del usuario.
    
    El usuario debe proporcionar un token válido para modificar un archivo.

    Args:
        uid (str): El ID de usuario del propietario del archivo.
        filename (str): El nombre del archivo a modificar.
        new_content (str): El nuevo contenido del archivo.
        token (str): Token de autenticación del usuario.
        visibility (str, optional): Nueva visibilidad del archivo. Por defecto None (no cambia).

    Returns:
        bool: True si el archivo fue modificado exitosamente, False en caso contrario.
    """
    if uuid.UUID(token) != uuid.uuid5(Secret_uuid, uid):
        return False
    
    df = _open_library(uid)

    if filename in df['name'].values:
        df.loc[df['name'] == filename, 'content'] = new_content
        if visibility is not None:
            df.loc[df['name'] == filename, 'visibility'] = visibility
        df.to_csv(path + uid + ".txt", sep="\t", index=False)
        return True
    else:
        return False

def remove_file(uid, filename, token):
    """
    Elimina un archivo de la biblioteca del usuario.
    
    El usuario debe proporcionar un token válido para eliminar un archivo.

    Args:
        uid (str): El ID de usuario del propietario del archivo.
        filename (str): El nombre del archivo a eliminar.
        token (str): Token de autenticación del usuario.
            
    Returns:
        bool: True si el archivo fue eliminado exitosamente, False en caso contrario.
    """
    if uuid.UUID(token) != uuid.uuid5(Secret_uuid, uid):
        return False
    
    df = _open_library(uid)

    if filename in df['name'].values:
        df.drop(df[df['name'] == filename].index, inplace=True)
        df.to_csv(path + uid + ".txt", sep="\t", index=False)
        return True
    else:
        return False

# =============================================================================
# FUNCIONES AUXILIARES
# =============================================================================

def _open_library(uid):
    """
    Abre el archivo de biblioteca del usuario.
    
    Si el archivo de biblioteca no existe, crea uno nuevo vacío.

    Args:
        uid (str): El ID de usuario del propietario de la biblioteca.

    Returns:
        pd.DataFrame: La biblioteca del usuario como un DataFrame de pandas.
    """
    lib_name = os.path.join(path, uid + ".txt")
    if not os.path.exists(lib_name):
        return pd.DataFrame(columns=["name", "visibility", "content"])
    return pd.read_csv(lib_name, sep="\t")

# =============================================================================
# FUNCIONES DE TOKENS DE COMPARTICIÓN
# =============================================================================

def _create_share_token(minutes: int, uid: str, login_token: str, filename: str) -> str:
    """
    Función privada para crear un token de compartición temporal.
    
    Genera un token que permite acceso temporal a un archivo específico.

    Args:
        minutes (int): Número de minutos que el enlace será válido.
        uid (str): ID del usuario propietario del archivo.
        login_token (str): Token de autenticación del usuario.
        filename (str): Nombre del archivo a compartir.

    Returns:
        str or None: El token de compartición con formato UID.nombre.exp.hash donde hash 
                    es la información previa como sha-1, o None si falla la validación.
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
    Función para verificar si un token de compartición es válido.
    
    Valida que el token no haya expirado y que corresponda al archivo y usuario correctos.

    Args: 
        file_name (str): Nombre del archivo a compartir.
        share_token (str): El token de compartición a verificar.
        user (str): UID del propietario del archivo.
        
    Returns: 
        bool: True si el token es válido, False en caso contrario.
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

# =============================================================================
# SERVIDOR HTTP - API REST (QUART)
# =============================================================================

app = Quart(__name__)

# -----------------------------------------------------------------------------
# Endpoints de Gestión de Archivos
# -----------------------------------------------------------------------------

@app.route("/create_file", methods=["POST"])
async def http_create_file():
    """
    Endpoint HTTP para crear un nuevo archivo en la biblioteca del usuario.
    
    - Método: POST
    - Path: /create_file
    - Headers: Authorization: Bearer <token>
    - Body (JSON): {"uid": "<uid>", "filename": "<nombre>", "content": "<contenido>", "visibility": "<public|private>"}
    - Comportamiento: Llama a create_file(uid, token, filename, content, visibility)
    - Respuestas esperadas:
        200: {"ok": true, "uid": "<uid>", "filename": "<nombre>", "visibility": "<visibilidad>"} - Archivo creado
        400: {"ok": false, "error": "..."} - Parámetros faltantes o body inválido
        401: {"ok": false, "error": "Falta Authorization Bearer"} - Token no proporcionado
        500: {"ok": false, "error": "..."} - Error interno del servidor
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
    Endpoint HTTP para modificar el contenido de un archivo en la biblioteca del usuario.
    
    - Método: PUT
    - Path: /modify_file
    - Headers: Authorization: Bearer <token>
    - Body (JSON): {"uid": "<uid>", "filename": "<nombre>", "new_content": "<nuevo_contenido>", "visibility": "<public|private>"}
    - Comportamiento: Llama a modify_file(uid, filename, new_content, token, visibility)
    - Respuestas esperadas:
        200: {"ok": true, "uid": "<uid>", "filename": "<nombre>", "visibility": "<visibilidad>"} - Archivo modificado
        400: {"ok": false, "error": "..."} - Parámetros faltantes o body inválido
        401: {"ok": false, "error": "Falta Authorization Bearer"} - Token no proporcionado
        403: {"ok": false, "error": "No tienes permiso para modificar este fichero o no existe"} - Sin permisos
        500: {"ok": false, "error": "..."} - Error interno del servidor
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
    Endpoint HTTP para eliminar un archivo de la biblioteca del usuario.
    
    - Método: DELETE
    - Path: /remove_file
    - Headers: Authorization: Bearer <token>
    - Body (JSON): {"uid": "<uid>", "filename": "<nombre>"}
    - Comportamiento: Llama a remove_file(uid, filename, token)
    - Respuestas esperadas:
        200: {"ok": true, "uid": "<uid>", "filename": "<nombre>"} - Archivo eliminado
        400: {"ok": false, "error": "..."} - Parámetros faltantes o body inválido
        401: {"ok": false, "error": "Falta Authorization Bearer"} - Token no proporcionado
        403: {"ok": false, "error": "No tienes permiso para eliminar este fichero o no existe"} - Sin permisos
        500: {"ok": false, "error": "..."} - Error interno del servidor
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
    Endpoint HTTP para leer el contenido de un archivo en la biblioteca del usuario.
    
    - Método: GET
    - Path: /read_file
    - Headers: Authorization: Bearer <token> (opcional para archivos públicos)
    - Body (JSON): {"uid": "<uid>", "filename": "<nombre>"}
    - Comportamiento: Llama a read_file(uid, filename, token). Permite acceso con token o tokens de compartición.
    - Respuestas esperadas:
        200: {"ok": true, "uid": "<uid>", "filename": "<nombre>", "content": "<contenido>"} - Archivo leído
        400: {"ok": false, "error": "..."} - Parámetros faltantes o body inválido
        403: {"ok": false, "error": "No tienes permiso para leer este fichero o no existe"} - Sin permisos
        500: {"ok": false, "error": "..."} - Error interno del servidor
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
    Endpoint HTTP para listar todos los archivos en la biblioteca del usuario.
    
    - Método: GET
    - Path: /list_files
    - Headers: Authorization: Bearer <token>
    - Body (JSON): {"uid": "<uid>"}
    - Comportamiento: Llama a list_files(uid, token). Requiere token para listar archivos privados.
    - Respuestas esperadas:
        200: {"ok": true, "uid": "<uid>", "files": ["<archivo1>", "<archivo2>", ...]} - Archivos listados
        400: {"ok": false, "error": "..."} - Parámetros faltantes o body inválido
        401: {"ok": false, "error": "Falta Authorization Bearer"} - Token no proporcionado
        500: {"ok": false, "error": "..."} - Error interno del servidor
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

# -----------------------------------------------------------------------------
# Endpoints de Compartición
# -----------------------------------------------------------------------------

@app.route("/create_share_token", methods=["POST"])
async def http_create_share_token():
    """
    Endpoint HTTP para crear un token de compartición temporal.
    
    - Método: POST
    - Path: /create_share_token
    - Headers: Authorization: Bearer <token>
    - Body (JSON): {"uid": "<uid>", "filename": "<nombre>", "minutes": <minutos>}
    - Comportamiento: Llama a _create_share_token(minutes, uid, login_token, filename)
    - Respuestas esperadas:
        200: {"ok": true, "share_token": "<token>"} - Token de compartición creado
        400: {"ok": false, "error": "..."} - Parámetros faltantes o body inválido
        401: {"ok": false, "error": "Falta Authorization Bearer"} - Token no proporcionado
        403: {"ok": false, "error": "No se pudo crear el enlace (token inválido o fichero inexistente)"} - Sin permisos
        500: {"ok": false, "error": "..."} - Error interno del servidor
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

# =============================================================================
# PUNTO DE ENTRADA PRINCIPAL
# =============================================================================

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5051, debug=True)