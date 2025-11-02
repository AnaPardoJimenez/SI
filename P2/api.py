"""
api.py - Sistema de Catálogo de Películas y Gestión de Pedidos

Este módulo implementa un sistema de catálogo de películas con carrito de compra 
y gestión de pedidos, expuesto a través de una API REST construida con Quart.

Funcionalidades principales:
    - Búsqueda y filtrado de películas por diversos criterios
    - Gestión del carrito de compra por usuario
    - Procesamiento de pedidos y checkout
    - Gestión del saldo de usuarios
    - API REST con endpoints HTTP asíncronos

Estructura de datos:
    - Películas: almacenadas en base de datos PostgreSQL
    - Carritos y pedidos: persistentes en base de datos
    - Historial de transacciones por usuario

Autor: Juan Larrondo Fernández de Córdoba y Ana Pardo Jiménez
Fecha de creación: 28-10-2025
Última modificación: 28-10-2025
Versión: 1.0.0
Python: 3.7+
Dependencias: quart, sqlalchemy, asyncpg

Uso:
    python api.py
    
El servidor se ejecutará en http://0.0.0.0:5051
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
engine = create_async_engine(DATABASE_URL, echo=False)

# =============================================================================
# FUNCIONES DE GESTIÓN DE CATÁLOGO
# =============================================================================

def get_movies(params: dict = None):
    
    conditions = []
    query_params = {}
    query = "SELECT * FROM Peliculas"
    flag = 0

    if "title" in params:
        conditions.append("title ILIKE :title")
        query_params["title"] = f"%{params['title']}"
        flag = 1
    elif "year" in params:
        conditions.append("year = :year")
        query_params["year"] = f"%{params['year']}"
        flag = 1
    elif "genre" in params:
        conditions.append("year = :year")
        query_params["genre"] = f"%{params['genre']}"
        flag = 1
    elif "actor" in params:
        conditions.append("actor ILIKE :actor")
        query_params["actor"] = f"%{params['actor']}"
        flag = 1

    if flag == 1:
        query += " WHERE " + " AND ".join(conditions)

    data = fetch_all(engine, query, query_params)
    if data.empty:
        return None, "ERROR"
    return data, "OK"

def get_movies_by_id(movie_id):
    query = "SELECT * FROM Peliculas WHERE movie_id = :movie_id"
    params = {"movie_id": movie_id}

    data = fetch_all(engine, query, params)
    if data.empty:
        return None, "ERROR"
    return data, "OK"

# =============================================================================
# FUNCIONES DE GESTIÓN DE CARRITO
# =============================================================================

def get_cart(user_id, movie_id=None):
    query = """
                SELECT p.movie_id, p.name, p.description, p.year, p.genre, p.price
                FROM Peliculas p
                JOIN Pertenece pe ON p.movie_id = pe.movie_id
                JOIN Carrito c ON pe.order_id = c.order_id
                WHERE c.user_id = :user_id
            """
    
    params = {"user_id": user_id}

    data = fetch_all(engine, query, params)

    # Eliminar película específica si se proporciona movie_id (no de la BBDD, solo de la consulta)
    if movie_id:
        for i in range(len(data) - 1, -1, -1):
            if data[i].get("movie_id") == movie_id:
                data.pop(i)

    if data.empty:
        return None, "ERROR"
    return data, "OK"

def add_to_cart(user_id, movie_id):
    #NOTE: revisar esta query (crea el carrito si no existe y añade la película)
    query = """
                WITH upsert_carrito AS (
                    INSERT INTO Carrito (user_id)
                    SELECT :user_id
                    WHERE NOT EXISTS (SELECT 1 FROM Carrito WHERE user_id = :user_id)
                    RETURNING order_id),
                    
                    carrito_objetivo AS (
                    SELECT order_id FROM upsert_carrito
                    UNION ALL
                    SELECT order_id FROM Carrito WHERE user_id = :user_id
                    LIMIT 1
                )

                INSERT INTO Pertenece (order_id, movie_id)
                SELECT order_id, :movie_id
                FROM carrito_objetivo
                ON CONFLICT DO NOTHING
            """

    params = {"user_id": user_id, "movie_id": movie_id}

    data = fetch_all(engine, query, params)
    if data.empty:
        return None, "ERROR"
    return data, "OK"


async def delete_from_cart(movie_id, token):
    user_id = await get_user_id(token)
    if user_id == "USER_NOT_FOUND":
        return "USER_NOT_FOUND"

    query = """
        SELECT * 
            FROM Pertenece p
                JOIN Carrito c ON p.order_id = c.order_id
            WHERE p.movie_id = :movie_id 
                AND c.user_id = :user_id
    """
    params = {"movie_id": movie_id, "user_id": user_id}

    data = await fetch_all(engine, query, params=params)
    if not data:
        return "NOT_FOUND"

    query = """
        DELETE 
            FROM Pertenece p 
                USING Carrito c
            WHERE p.order_id = c.order_id 
                AND c.user_id = :user_id
                AND p.movie_id = :movie_id 
    """
    params = {"movie_id": movie_id, "user_id": user_id}

    result = await fetch_all(engine, query, params=params)
    if result:
        return "OK"
    else:
        return "ERROR"

async def change_balance(user_id, amount):
    query = """
        UPDATE Usuario u
        SET balance = balance + :amount
        WHERE u.user_id = :user_id
    """
    params = {"user_id": user_id, "amount": amount}
    result = await fetch_all(engine, query, params=params)
    if result:
        return "OK"
    else:
        return "ERROR"

async def empty_cart(user_id):
    query = """
        DELETE
            FROM Pertenece p
                USING Carrito c
            WHERE p.order_id = c.order_id
                AND c.user_id = :user_id
    """
    params = {"user_id": user_id}
    result = await fetch_all(engine, query, params=params)
    if result:
        return "OK"
    else:
        return "ERROR"

async def checkout(token):
    # Obtener el ID del usuario
    user_id = await get_user_id(token)
    if user_id == "USER_NOT_FOUND":
        return "USER_NOT_FOUND"

    # Obtener el total del carrito
    query = """
        SELECT SUM(p.price) as total
            FROM Carrito c
                JOIN Pertenece pe ON c.order_id = pe.order_id
                JOIN Peliculas p ON pe.movie_id = p.movie_id
            WHERE c.user_id = :user_id
    """
    params = {"user_id": user_id}
    total_data = await fetch_all(engine, query, params=params)
    if not total_data or total_data[0]["total"] is None:
        return "NO_PRICE_FOUND"
    
    total = float(total_data[0]["total"])

    # Verificar si el saldo es suficiente para pagar el carrito
    query = """
        SELECT balance 
            FROM Usuario 
            WHERE user_id = :user_id
    """
    params = {"user_id": user_id}
    current_balance = await fetch_all(engine, query, params=params)

    if not current_balance or current_balance[0]['balance'] is None:
        return "NO_BALANCE_FOUND"

    if current_balance and current_balance[0]['balance'] + total < 0:
        return "INSUFFICIENT_BALANCE"

    # Actualizar el saldo del usuario
    if await change_balance(user_id, -total) == "ERROR": return "CHANGE_BALANCE_FAILED"
    
    # Eliminar las películas del carrito
    if await empty_cart(user_id) == "ERROR": return "EMPTY_CART_FAILED"

    return "OK"

# =============================================================================
# FUNCIONES AUXILIARES
# =============================================================================

async def get_user_id(token):
    query = """
        SELECT user_id 
            FROM Usuario 
            WHERE token = :token
    """
    params = {"token": token}
    result = await fetch_all(engine, query, params=params)
    if result:
        return result[0]["user_id"]
    else:
        return "USER_NOT_FOUND"

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
# SERVIDOR HTTP - API REST (QUART)
# =============================================================================

app = Quart(__name__)

DATABASE_URL = "postgresql+asyncpg://alumnodb:1234@localhost:9999/si1"
# --- Engine y sesión asíncronos ---
engine = create_async_engine(DATABASE_URL, echo=False)
async_session = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)



@app.route("/movies", methods=["GET"])
async def http_get_movies():
    try:
        body = (await request.get_json(silent=True))

        result = get_movies(body)
        if result[1] == "OK":
            return jsonify({'status': 'OK', 'movies': result[0]}), HTTPStatus.OK
        else:
            return jsonify({'status': 'ERROR', 'message': 'No se encontraron películas que coincidan con los criterios de búsqueda.'}), HTTPStatus.NOT_FOUND
    
    except Exception as exc:
        return jsonify({'status': 'ERROR', 'message': str(exc)}), HTTPStatus.INTERNAL_SERVER_ERROR


    
@app.route("/movies/<int:movie_id>", methods=["GET"])
async def http_get_movie_by_id(movie_id):
    try:
        result = get_movies_by_id(movie_id)
        if result[1] == "OK":
            return jsonify({'status': 'OK', 'movie': result[0]}), HTTPStatus.OK
        else:
            return jsonify({'status': 'ERROR', 'message': 'No se encontró la película con el ID proporcionado.'}), HTTPStatus.NOT_FOUND
    except Exception as exc:
        return jsonify({'status': 'ERROR', 'message': str(exc)}), HTTPStatus.INTERNAL_SERVER_ERROR



@app.route("/cart", methods=["GET"])
async def http_get_cart():
    try:
        body = (await request.get_json(silent=True))

        user_id = body.get("user_id")

        result = get_cart(user_id)
        if result[1] == "OK":
            return jsonify({'status': 'OK', 'cart': result[0]}), HTTPStatus.OK
        else:
            return jsonify({'status': 'ERROR', 'message': 'El carrito está vacío o no se encontró.'}), HTTPStatus.NOT_FOUND
    except Exception as exc:
        return jsonify({'status': 'ERROR', 'message': str(exc)}), HTTPStatus.INTERNAL_SERVER_ERROR



@app.route("/cart/<int:movie_id>", methods=["PUT"])
async def http_add_to_cart(movie_id):
    try:
        body = (await request.get_json(silent=True))

        user_id = body.get("user_id")

        result = add_to_cart(user_id, movie_id)
        if result[1] == "OK":
            return jsonify({'status': 'OK', 'message': 'Película añadida al carrito.'}), HTTPStatus.OK
        else:
            return jsonify({'status': 'ERROR', 'message': 'No se pudo añadir la película al carrito.'}), HTTPStatus.INTERNAL_SERVER_ERROR
    except Exception as exc:
        return jsonify({'status': 'ERROR', 'message': str(exc)}), HTTPStatus.INTERNAL_SERVER_ERROR



@app.route("/cart/<int:movie_id>", methods=["DELETE"])
async def http_delete_from_cart(movie_id):
    try:
        if movie_id is None:
            return jsonify({'status': 'ERROR', 'message': 'El ID de la película es requerido'}), HTTPStatus.BAD_REQUEST
        
        auth = request.headers.get("Authorization", "")
        if not auth.startswith("Bearer "):
            return jsonify({'status': 'ERROR', 'message': 'Falta Authorization Bearer'}), HTTPStatus.BAD_REQUEST
        
        token = auth.split(" ", 1)[1].strip()
        print(f"238 token={token}")

        result = await delete_from_cart(movie_id, token)
        if result == "OK":
            return jsonify({'status': 'OK', 'message': 'Película eliminada del carrito.'}), HTTPStatus.OK
        elif result == "NOT_FOUND":
            return jsonify({'status': 'OK', 'message': 'No se encontró la película en el carrito.'}), HTTPStatus.NOT_FOUND
        elif result == "ERROR":
            return jsonify({'status': 'ERROR', 'message': 'No se pudo eliminar la película del carrito.'}), HTTPStatus.INTERNAL_SERVER_ERROR
        else:
            return jsonify({'status': 'ERROR', 'message': 'El servidor se rehusa a preparar café porque es una tetera.'}), HTTPStatus.IM_A_TEAPOT

    except Exception as exc:
        return jsonify({'status': 'ERROR', 'message': str(exc)}), HTTPStatus.INTERNAL_SERVER_ERROR


# =============================================================================
# PUNTO DE ENTRADA PRINCIPAL
# =============================================================================

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5051, debug=True)