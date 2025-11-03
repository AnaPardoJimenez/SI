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

# --- Engine y sesión asíncronos ---
# DATABASE_URL y engine ya están definidos al principio del archivo
DATABASE_URL = "postgresql+asyncpg://alumnodb:1234@db:5432/si1"
engine = create_async_engine(DATABASE_URL, echo=False)
async_session = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

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

async def delete_from_cart(movieid, token):
    result = await find_movie_in_cart(movieid, token)
    if result[1] != "OK": return result[1]

    user_id = result[0].get("user_id")
    query = """
        DELETE 
            FROM Carrito_Pelicula cp 
                USING Carrito c
            WHERE cp.cart_id = c.cart_id 
                AND c.user_id = :user_id
                AND cp.movieid = :movieid 
    """
    params = {"movieid": movieid, "user_id": user_id}

    result = await fetch_all(engine, query, params=params)
    if result: return "OK"
    return "ERROR"

async def checkout(token):
    # Obtener el ID del usuario
    if not (user_id := await get_user_id(token)): return None, "USER_NOT_FOUND"
    # Obtener el total del carrito
    if (total := await get_cart_total(user_id)) == None: return None, "PRICE_NOT_FOUND"
    # Obtener el saldo del usuario
    if not (current_balance := await get_balance(user_id)): return None, "BALANCE_NOT_FOUND"
    # Verificar si el saldo es suficiente para pagar el carrito
    if (current_balance + total) < 0: return None, "INSUFFICIENT_BALANCE"

    # Crear el pedido
    if not (order_id := await create_order(user_id, total)): return None, "CREATE_ORDER_FAILED"
    # Añadir las películas al pedido
    if not await add_movies_to_order(order_id): return None, "ADD_MOVIES_TO_ORDER_FAILED"

    # Actualizar el saldo del usuario
    if not await add_to_balance(user_id, -total): return None, "ADD_TO_BALANCE_FAILED"
    # Eliminar las películas del carrito
    if not await empty_cart(user_id): return None, "EMPTY_CART_FAILED"

    query = """
        SELECT cart_id
        FROM Carrito
        WHERE user_id = :user_id
    """
    params = {"user_id": user_id}
    result = await fetch_all(engine, query, params=params)
    if result:
        return result[0]["cart_id"], "OK"
    else:
        return None, "CART_ID_NOT_FOUND"

async def get_order(order_id):
    # Obtener los datos del pedido
    query_order = """
        SELECT *
        FROM Pedido
        WHERE order_id = :order_id
    """
    params = {"order_id": order_id}
    order_data = await fetch_all(engine, query_order, params=params)
    if not order_data:
        return None, "ORDER_NOT_FOUND"
    order_dict = {"order_id": order_data[0]["order_id"], "user_id": order_data[0]["user_id"], "total": order_data[0]["total"], "date": order_data[0]["date"]}
    # Obtener las películas del pedido

    query_movies = """
        SELECT m.movieid, m.title, m.price 
        FROM Pelicula m
        JOIN Pedido_Pelicula pm ON m.movieid = pm.movieid
        WHERE pm.order_id = :order_id
    """
    movies_data = await fetch_all(engine, query_movies, params=params)
    if movies_data.empty:
        return None, "MOVIES_NOT_FOUND"

    movies_list = [
        {
            'movieid': movie.get('movieid'),
            'title': movie.get('title'),
            'price': movie.get('price')
        }
        for movie in movies_data
    ] if movies_data else []

    order_dict["movies"] = movies_list
    return order_dict, "OK"

async def new_balance(user_id, amount):
    query = """
        UPDATE Usuario 
        SET balance = :amount
        WHERE user_id = :user_id
    """
    params = {"user_id": user_id, "amount": amount}
    return await fetch_all(engine, query, params=params)

# =============================================================================
# FUNCIONES AUXILIARES
# =============================================================================

async def find_movie_in_cart(movieid, token):
    if not (user_id := await get_user_id(token)): return None, "USER_NOT_FOUND"

    query = """
        SELECT * 
            FROM Carrito_Pelicula cp
                JOIN Carrito c ON cp.cart_id = c.cart_id
            WHERE cp.movieid = :movieid
                AND c.user_id = :user_id
    """
    params = {"movieid": movieid, "user_id": user_id}
    data = await fetch_all(engine, query, params=params)
    if data.empty:
        return None, "MOVIE_NOT_FOUND"
    return data[0], "OK"

async def get_balance(user_id):
    query = """
        SELECT balance
            FROM Usuario
            WHERE user_id = :user_id
    """
    params = {"user_id": user_id}
    result = await fetch_all(engine, query, params=params)
    if result:
        return float(result[0]["balance"])
    else:
        return None

async def add_to_balance(user_id, amount):
    query = """
        UPDATE Usuario 
        SET balance = balance + :amount
        WHERE user_id = :user_id
    """
    params = {"user_id": user_id, "amount": amount}
    return await fetch_all(engine, query, params=params)

async def get_cart_total(user_id):
    query = """
        SELECT SUM(p.price) as total
            FROM Carrito c
                JOIN Carrito_Pelicula cp ON c.cart_id = cp.cart_id
                JOIN Peliculas p ON cp.movieid = p.movieid
            WHERE c.user_id = :user_id
    """
    params = {"user_id": user_id}
    result = await fetch_all(engine, query, params=params)
    if result:
        total = result[0]["total"]
        # Si total es None (carrito vacío), retornar 0.0
        if total is None:
            return 0.0
        return float(total)
    else:
        return None

async def empty_cart(user_id):
    params = {"user_id": user_id}
    query = """
        DELETE
            FROM Carrito_Pelicula cp
                USING Carrito c
            WHERE cp.cart_id = c.cart_id
                AND c.user_id = :user_id
    """
    return await fetch_all(engine, query, params=params)

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
        return None

async def create_order(user_id, total):
    async def create_cart(user_id):
        query = """
            INSERT INTO Carrito (user_id)
            VALUES (:user_id)
        """
        params = {"user_id": user_id}
        return await fetch_all(engine, query, params=params)

    await create_cart(user_id)
    query = """
        SELECT cart_id
        FROM Carrito
        WHERE user_id = :user_id
    """
    params = {"user_id": user_id}
    result = await fetch_all(engine, query, params=params)
    if not result: return None
    cart_id = result[0]["cart_id"]
    if not cart_id: return None

    query = """
        INSERT INTO Pedido (order_id, user_id, total, date)
        VALUES (:order_id, :user_id, :total, NOW())
        RETURNING order_id
    """
    params = {"order_id": cart_id, "user_id": user_id, "total": total}
    return await fetch_all(engine, query, params=params)

async def add_movies_to_order(order_id):
    query = """
        INSERT INTO Pedido_Pelicula (order_id, movieid)
        SELECT :order_id, movieid
        FROM Carrito_Pelicula
        WHERE cart_id = :cart_id
    """
    params = {"order_id": order_id, "cart_id": order_id}
    return await fetch_all(engine, query, params=params)

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
                elif query_upper.startswith(('DELETE')) or query_upper.startswith(('INSERT')):
                    return True  # No se borró nada, pero no es un error
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


@app.route("/movies", methods=["GET"])
async def http_get_movies():
    try:
        body = request.args.to_dict(flat=True)

        data, status = await get_movies(body)
        if status == "OK":
            return jsonify(data), HTTPStatus.OK
        elif status == "ERROR" and data is None:
            return jsonify({}), HTTPStatus.OK

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



@app.route("/cart/<int:movieid>", methods=["DELETE"])
async def http_delete_from_cart(movieid):
    """
    Endpoint HTTP para eliminar una película del carrito.
    
    - Método: DELETE
    - Path: /cart/<int:movieid>
    - Comportamiento: Llama a delete_from_cart(movieid, token)
    - Respuestas esperadas:
        HTTPStatus.OK: {"status":"OK", "message": "Película eliminada del carrito."} - Película eliminada exitosamente
        HTTPStatus.NOT_FOUND: {"status":"ERROR", "message": "No se encontró la película en el carrito."} - No se encontró la película en el carrito
        HTTPStatus.INTERNAL_SERVER_ERROR: {"status":"ERROR", "message": "No se pudo eliminar la película del carrito."} - No se pudo eliminar la película del carrito
        HTTPStatus.IM_A_TEAPOT: {"status":"ERROR", "message": "El servidor se rehusa a preparar café porque es una tetera."} - El servidor se rehusa a preparar café porque es una tetera
    """
    try:
        if movieid is None:
            return jsonify({'status': 'ERROR', 'message': 'El ID de la película es requerido'}), HTTPStatus.BAD_REQUEST
        
        auth = request.headers.get("Authorization", "")
        if not auth.startswith("Bearer "):
            return jsonify({'status': 'ERROR', 'message': 'Falta Authorization Bearer'}), HTTPStatus.BAD_REQUEST
        
        token = auth.split(" ", 1)[1].strip()

        result = await delete_from_cart(movieid, token)
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


@app.route("/cart/checkout", methods=["POST"])
async def http_checkout():
    """
    Endpoint HTTP para crear un pedido.
    
    - Método: POST
    - Path: /cart/checkout
    - Comportamiento: Llama a checkout(token)
    - Respuestas esperadas:
        HTTPStatus.OK: {"status":"OK", "message": "Pedido creado correctamente."} - Pedido creado exitosamente
        HTTPStatus.NOT_FOUND: {"status":"ERROR", "message": "Usuario no encontrado"} - Usuario no existe
        HTTPStatus.NOT_FOUND: {"status":"ERROR", "message": "Precio no encontrado"} - Precio no encontrado
        HTTPStatus.NOT_FOUND: {"status":"ERROR", "message": "Saldo no encontrado"} - Saldo no encontrado
        HTTPStatus.PAYMENT_REQUIRED: {"status":"ERROR", "message": "Saldo insuficiente"} - Saldo insuficiente
        HTTPStatus.INTERNAL_SERVER_ERROR: {"status":"ERROR", "message": "No se pudo actualizar el saldo."} - No se pudo actualizar el saldo
        HTTPStatus.INTERNAL_SERVER_ERROR: {"status":"ERROR", "message": "No se pudo vaciar el carrito."} - No se pudo vaciar el carrito
        HTTPStatus.IM_A_TEAPOT: {"status":"ERROR", "message": "El servidor se rehusa a preparar café porque es una tetera."} - El servidor se rehusa a preparar café porque es una tetera
    """
    try:
        auth = request.headers.get("Authorization", "")
        if not auth.startswith("Bearer "):
            return jsonify({'status': 'ERROR', 'message': 'Falta Authorization Bearer'}), HTTPStatus.BAD_REQUEST
        
        token = auth.split(" ", 1)[1].strip()
        orderid, result = await checkout(token)
        if result == "OK":
            return jsonify({'status': 'OK', 'orderid': orderid, 'message': 'Pedido creado correctamente.'}), HTTPStatus.OK
        elif result == "USER_NOT_FOUND":
            return jsonify({'status': 'ERROR', 'message': 'Usuario no encontrado'}), HTTPStatus.NOT_FOUND
        elif result == "PRICE_NOT_FOUND":
            return jsonify({'status': 'ERROR', 'message': 'Precio no encontrado'}), HTTPStatus.NOT_FOUND
        elif result == "BALANCE_NOT_FOUND":
            return jsonify({'status': 'ERROR', 'message': 'Saldo no encontrado'}), HTTPStatus.NOT_FOUND
        elif result == "INSUFFICIENT_BALANCE":
            return jsonify({'status': 'ERROR', 'message': 'Saldo insuficiente'}), HTTPStatus.PAYMENT_REQUIRED
        elif result == "ADD_TO_BALANCE_FAILED":
            return jsonify({'status': 'ERROR', 'message': 'No se pudo actualizar el saldo.'}), HTTPStatus.INTERNAL_SERVER_ERROR
        elif result == "EMPTY_CART_FAILED":
            return jsonify({'status': 'ERROR', 'message': 'No se pudo vaciar el carrito.'}), HTTPStatus.INTERNAL_SERVER_ERROR
        elif result == "CART_ID_NOT_FOUND":
            return jsonify({'status': 'ERROR', 'message': 'No existe carrito para el usuario.'}), HTTPStatus.INTERNAL_SERVER_ERROR
        elif result == "CREATE_ORDER_FAILED":
            return jsonify({'status': 'ERROR', 'message': 'No se pudo crear el pedido.'}), HTTPStatus.INTERNAL_SERVER_ERROR
        elif result == "ADD_MOVIES_TO_ORDER_FAILED":
            return jsonify({'status': 'ERROR', 'message': 'No se pudo añadir las películas al pedido.'}), HTTPStatus.INTERNAL_SERVER_ERROR
        else:
            return jsonify({'status': 'ERROR', 'message': 'El servidor se rehusa a preparar café porque es una tetera.'}), HTTPStatus.IM_A_TEAPOT
    except Exception as exc:
        return jsonify({'status': 'ERROR', 'message': str(exc)}), HTTPStatus.INTERNAL_SERVER_ERROR


@app.route("/user/credit", methods=["POST"])
async def http_new_balance():
    """
    Endpoint HTTP para actualizar el saldo de un usuario.
    
    - Método: POST
    - Path: /user/credit
    - Body (JSON): {"amount": "<amount>"}
    - Comportamiento: Llama a new_balance(user_id, amount)
    - Respuestas esperadas:
        HTTPStatus.OK: {"status":"OK"} - Saldo actualizado exitosamente
        HTTPStatus.BAD_REQUEST: {"status":"ERROR", "message": "..."} - Parámetros faltantes
        HTTPStatus.UNAUTHORIZED: {"status":"ERROR", "message": "Credenciales incorrectas"} - Contraseña incorrecta
        HTTPStatus.NOT_FOUND: {"status":"ERROR", "message": "Usuario no encontrado"} - Usuario no existe
        HTTPStatus.INTERNAL_SERVER_ERROR.BAD_REQUEST: {"status":"ERROR", "message": "..."} - Error interno del servidor o del sistema de archivos
    """
    try:
        auth = request.headers.get("Authorization", "")
        if not auth.startswith("Bearer "):
            return jsonify({"ok": False, "error": "Falta Authorization Bearer"}), HTTPStatus.BAD_REQUEST

        token = auth.split(" ", 1)[1].strip()
        if not (user_id := await get_user_id(token)):
            return jsonify({'status': 'ERROR', 'message': 'Usuario no encontrado'}), HTTPStatus.NOT_FOUND

        body = (await request.get_json(silent=True))
        if not (amount := body.get("amount")):
            return jsonify({'status': 'ERROR', 'message': 'Body JSON no contiene la clave "amount"'}), HTTPStatus.BAD_REQUEST

        result = await new_balance(user_id, amount)
        if result:
            return jsonify({'status': 'OK', 'new_credit': amount, 'message': 'Saldo actualizado exitosamente.'}), HTTPStatus.OK
        else:
            return jsonify({'status': 'ERROR', 'message': 'No se pudo actualizar el saldo.'}), HTTPStatus.INTERNAL_SERVER_ERROR

    except Exception as exc:
        return jsonify({'status': 'ERROR', 'message': str(exc)}), HTTPStatus.INTERNAL_SERVER_ERROR


@app.route("/orders/<int:order_id>", methods=["GET"])
async def http_get_order(order_id):
    """
    Endpoint HTTP para obtener un pedido por su ID.
    
    - Método: GET
    - Path: /orders/<int:order_id>
    - Comportamiento: Llama a get_order(order_id)
    - Respuestas esperadas:
        HTTPStatus.OK: {"status":"OK", "order": "<order>"} - Pedido obtenido exitosamente
        HTTPStatus.NOT_FOUND: {"status":"ERROR", "message": "No se encontró el pedido."} - No se encontró el pedido
        HTTPStatus.INTERNAL_SERVER_ERROR: {"status":"ERROR", "message": "No se pudo obtener el pedido."} - No se pudo obtener el pedido
        HTTPStatus.IM_A_TEAPOT: {"status":"ERROR", "message": "El servidor se rehusa a preparar café porque es una tetera."} - El servidor se rehusa a preparar café porque es una tetera
    """
    try:
        result = await get_order(order_id)
        if result[1] == "OK":
            return jsonify({'status': 'OK', 'order': result[0]}), HTTPStatus.OK
        else:
            return jsonify({'status': 'ERROR', 'message': 'No se encontró el pedido.'}), HTTPStatus.NOT_FOUND
    except Exception as exc:
        return jsonify({'status': 'ERROR', 'message': str(exc)}), HTTPStatus.INTERNAL_SERVER_ERROR

# =============================================================================
# PUNTO DE ENTRADA PRINCIPAL
# =============================================================================

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5051, debug=True)