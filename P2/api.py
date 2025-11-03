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
# --- Engine y sesión asíncronos ---
engine = create_async_engine(DATABASE_URL, echo=False)
async_session = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

# =============================================================================
# FUNCIONES AUXILIARES
# =============================================================================

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
# FUNCIONES DE GESTIÓN DE CATÁLOGO
# =============================================================================

async def get_movies(params: dict = None):
    conditions = []
    query_params = {}
    query = "SELECT * FROM Peliculas"
    flag = 0

    if params is None or not isinstance(params, dict):
        data = await fetch_all(engine, query, query_params)  # 👈 await
        if not data:
            return None, "ERROR"
        return data, "OK"

    if "title" in params:
        conditions.append("title ILIKE :title")
        query_params["title"] = f"%{params['title']}%"
        flag = 1
    if "year" in params and params["year"] != "":
        try:
            query_params["year"] = int(params["year"])
        except (ValueError, TypeError):
            return {}, "ERROR"
        else:
            conditions.append("year = :year")
    if "genre" in params:
        conditions.append("genre ILIKE :genre")
        query_params["genre"] = f"%{params['genre']}%"
        flag = 1
    if "actor" in params:
        conditions.append("actor ILIKE :actor")
        query_params["actor"] = f"%{params['actor']}%"
        flag = 1

    if flag == 1:
        query += " WHERE " + " AND ".join(conditions)

    data = await fetch_all(engine, query, query_params)

    if not data:
        return None, "ERROR"
    return data, "OK"

async def get_movies_by_id(movieid):
    query = "SELECT * FROM Peliculas WHERE movieid = :movieid"
    params = {"movieid": movieid}

    data = (await fetch_all(engine, query, params))
    if not data:
        return None, "ERROR"
    print("[DEBUG] get_movies_by_id data:", data)
    return data[0], "OK"

# =============================================================================
# FUNCIONES DE GESTIÓN DE CARRITO
# =============================================================================

def get_cart(user_id, movieid=None):
    query = """
                SELECT p.movieid, p.name, p.description, p.year, p.genre, p.price
                FROM Peliculas p
                JOIN Pertenece pe ON p.movieid = pe.movieid
                JOIN Carrito c ON pe.order_id = c.order_id
                WHERE c.user_id = :user_id
            """
    
    params = {"user_id": user_id}

    data = fetch_all(engine, query, params)

    # Eliminar película específica si se proporciona movieid (no de la BBDD, solo de la consulta)
    if movieid:
        for i in range(len(data) - 1, -1, -1):
            if data[i].get("movieid") == movieid:
                data.pop(i)

    if data.empty:
        return None, "ERROR"
    return data, "OK"

def add_to_cart(user_id, movieid):
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

                INSERT INTO Pertenece (order_id, movieid)
                SELECT order_id, :movieid
                FROM carrito_objetivo
                ON CONFLICT DO NOTHING
            """

    params = {"user_id": user_id, "movieid": movieid}

    data = fetch_all(engine, query, params)
    if data.empty:
        return None, "ERROR"
    return data, "OK"

# =============================================================================
# SERVIDOR HTTP - API REST (QUART)
# =============================================================================

app = Quart(__name__)

@app.route("/movies", methods=["GET"])
async def http_get_movies():
    try:
        body = request.args.to_dict(flat=True)

        data, status = await get_movies(body)

        if status == "OK":
            return jsonify(data), HTTPStatus.OK
        elif status == "ERROR" and data is None:
            return jsonify({}), HTTPStatus.NOT_FOUND

        return jsonify({
            "status": "ERROR",
            "message": "No se encontraron películas que coincidan con los criterios de búsqueda."
        }), HTTPStatus.NOT_FOUND

    except Exception as exc:
        return jsonify({"status": "ERROR", "message": str(exc)}), HTTPStatus.INTERNAL_SERVER_ERROR

    
@app.route("/movies/<int:movieid>", methods=["GET"])
async def http_get_movie_by_id(movieid):
    try:
        data, status = await get_movies_by_id(movieid)
        if status == "OK":
            return jsonify(data), HTTPStatus.OK
        else:
            return jsonify({}), HTTPStatus.NOT_FOUND
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

@app.route("/cart/<int:movieid>", methods=["PUT"])
async def http_add_to_cart(movieid):
    try:
        body = (await request.get_json(silent=True))

        user_id = body.get("user_id")

        result = add_to_cart(user_id, movieid)
        if result[1] == "OK":
            return jsonify({'status': 'OK', 'message': 'Película añadida al carrito.'}), HTTPStatus.OK
        else:
            return jsonify({'status': 'ERROR', 'message': 'No se pudo añadir la película al carrito.'}), HTTPStatus.INTERNAL_SERVER_ERROR
    except Exception as exc:
        return jsonify({'status': 'ERROR', 'message': str(exc)}), HTTPStatus.INTERNAL_SERVER_ERROR


# =============================================================================
# PUNTO DE ENTRADA PRINCIPAL
# =============================================================================

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5051, debug=True)