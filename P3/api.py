"""
api.py - Sistema de Catálogo de Películas y Gestión de Pedidos

Este módulo implementa un sistema de catálogo de películas con carrito de compra 
y gestión de pedidos, expuesto a través de una API REST construida con Quart.

Funcionalidades principales:
    - Búsqueda y filtrado de películas por diversos criterios (título, año, género, actor)
    - Búsqueda por conjunto de actores (todos deben aparecer en la película)
    - Obtención de top N películas ordenadas por votos y rating
    - Gestión del carrito de compra por usuario
    - Procesamiento de pedidos y checkout
    - Gestión del saldo de usuarios
    - Sistema de calificación de películas por usuarios
    - API REST con endpoints HTTP asíncronos
    - Autenticación mediante tokens Bearer

Estructura de datos:
    - Películas: almacenadas en base de datos PostgreSQL
    - Carritos y pedidos: persistentes en base de datos
    - Historial de transacciones por usuario
    - Calificaciones de películas por usuarios

Autor: Juan Larrondo Fernández de Córdoba y Ana Pardo Jiménez
Fecha de creación: 28-10-2025
Última modificación: 28-10-2025
Versión: 1.0.0
Python: 3.7+
Dependencias: quart, sqlalchemy, asyncpg

Uso:
    python api.py
    
El servidor se ejecutará en http://0.0.0.0:5051

Endpoints principales:
    GET  /movies              - Buscar películas con filtros opcionales
    GET  /movies/<movieid>    - Obtener detalles de una película
    GET  /cart                - Obtener carrito del usuario
    PUT  /cart/<movieid>      - Añadir película al carrito
    DELETE /cart/<movieid>    - Eliminar película del carrito
    POST /cart/checkout       - Procesar pedido del carrito
    GET  /orders/<order_id>   - Obtener detalles de un pedido
    POST /user/credit         - Actualizar saldo del usuario
    POST /movies/calification - Calificar una película
"""

import os
import uuid
from quart import Quart, jsonify, request
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from http import HTTPStatus
import user

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

async def add_movie(movie_data: dict):
    """
    Añade una película al catálogo con los campos mínimos requeridos.

    Args:
        movie_data (dict): Diccionario con las claves title, description, year,
            genre y price.

    Returns:
        tuple: (success, status)
            - success (bool): True si la inserción se realizó sin errores.
            - status (str): "OK" en caso de éxito, "BAD_REQUEST" si faltan campos
              obligatorios o "ERROR" si la operación falla.
    """

    required_fields = ("title", "description", "year", "genre", "price")
    if not all(movie_data.get(field) for field in required_fields):
        return False, "BAD_REQUEST"  # Todos los campos son obligatorios

    query = """
        INSERT INTO Peliculas (title, description, year, genre, price)
        VALUES (:title, :description, :year, :genre, :price)
    """

    params = {
        "title": movie_data.get("title"),
        "description": movie_data.get("description"),
        "year": movie_data.get("year"),
        "genre": movie_data.get("genre"),
        "price": movie_data.get("price"),
    }
    result = await fetch_all(engine, query, params=params)
    
    if result is True:
        return True, "OK"
    return False, "ERROR"

async def update_movie(movieid: int, movie_data: dict):
    """
    Actualiza cualquier campo editable de una película salvo su identificador.

    Args:
        movieid (int): ID de la película a modificar.
        movie_data (dict): Pares campo-valor a actualizar. Se ignoran claves no permitidas.

    Returns:
        tuple: (success, status)
            - success (bool): True si se actualizó alguna fila.
            - status (str): "OK" en éxito, "BAD_REQUEST" si no hay datos válidos,
              "NOT_FOUND" si no existe la película, "ERROR" en caso de fallo.
    """
    if not movie_data:
        return False, "BAD_REQUEST"  # No se proporcionaron datos para actualizar

    allowed_fields = {"title", "description", "year", "genre", "price", "rating", "stock", "votes"}
    fields_to_update = {k: v for k, v in movie_data.items() if k in allowed_fields}
    if not fields_to_update:
        return False, "BAD_REQUEST"

    set_clauses = ", ".join(f"{field} = :{field}" for field in fields_to_update)
    query = f"UPDATE Peliculas SET {set_clauses} WHERE movieid = :movieid"
    params = {"movieid": movieid, **fields_to_update}

    result = await fetch_all(engine, query, params=params)
    if result is True:
        return True, "OK"
    elif result is False:
        return False, "NOT_FOUND"
    return False, "ERROR"

async def remove_movie(movieid: int):
    """
    Elimina una película del catálogo según su identificador.

    Args:
        movieid (int): ID de la película a eliminar.

    Returns:
        tuple: (success, status)
            - success (bool): True si la eliminación se ejecutó sin errores.
            - status (str): "OK" en caso de éxito, "ERROR" si falla la operación.
    """
    query = """
        DELETE FROM Peliculas
        WHERE movieid = :movieid
    """

    params = {"movieid": movieid}
    result = await fetch_all(engine, query, params=params)
    if result is True:
        return True, "OK"
    elif result is False:
        return False, "NOT_FOUND"
    return False, "ERROR"

async def get_movies(params: dict = None):
    """
    Obtiene películas del catálogo con filtros opcionales.
    
    Parámetros soportados:
        - title: Búsqueda parcial por título (case-insensitive)
        - year: Filtro por año exacto
        - genre: Búsqueda parcial por género (case-insensitive)
        - actor: Búsqueda parcial por nombre de actor (case-insensitive)
        - actors: Lista de actores separados por comas (todos deben aparecer en la película)
        - N: Limitar resultados a las N películas con más votos y mejor rating
    
    Args:
        params (dict, optional): Diccionario con parámetros de búsqueda.
    
    Returns:
        tuple: (data, status)
            - data: Lista de diccionarios con información de películas o None
            - status: "OK", "NOT_FOUND", "ERROR", o "LIMIT_ERROR_VALUE"
    """
    query = "SELECT p.* FROM Peliculas p"
    query_params = {}
    conditions = []
    joins = []

    if params is None or not isinstance(params, dict):
        data = await fetch_all(engine, query, query_params)
        if data is False:
            return None, "NOT_FOUND"
        elif data is None:
            return None, "ERROR"
        return data, "OK"

    if "actors" in params and params["actors"]:
        params["actors"] = [s.strip() for s in params["actors"].split(",") if s.strip()]
        query = """
            SELECT p.*
                FROM Peliculas p
                    JOIN Participa pa ON p.movieid = pa.movieid
                    JOIN Actores a ON a.actor_id = pa.actor_id
            WHERE a.name = ANY(:actor_names)
            GROUP BY p.movieid, p.title, p.description, p.year, p.genre, p.price
            HAVING COUNT(DISTINCT a.name) = CARDINALITY(:actor_names)
        """
        query_params = {"actor_names": params["actors"]}

        if "N" in params and params["N"]:
            try:
                query_params["limit"] = int(params["N"])
            except (ValueError, TypeError):
                return {}, "ERROR"
            query += " ORDER BY p.votes DESC, p.rating DESC LIMIT :limit"

        data = await fetch_all(engine, query, query_params)
        
        if data is False:
            return None, "NOT_FOUND"
        elif data is None:
            return None, "ERROR"
        return data, "OK"

    if "title" in params:
        conditions.append("title ILIKE :title")
        query_params["title"] = f"%{params['title']}%"
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
    if "actor" in params and params["actor"]:
        # Necesitamos JOIN con Participa y Actores
        joins.append(" JOIN Participa pa ON pa.movieid = p.movieid")
        joins.append(" JOIN Actores a   ON a.actor_id = pa.actor_id")
        conditions.append("a.name ILIKE :actor")
        query_params["actor"] = f"%{params['actor']}%"
        query +=  "".join(joins)

    if conditions:
        query += " WHERE " + " AND ".join(conditions)
    
    if "N" in params and params["N"]:
        try:
            query_params["limit"] = int(params["N"])
        except (ValueError, TypeError):
            return {}, "ERROR"
        if query_params["limit"] <= 0:
            return None, "LIMIT_ERROR_VALUE"
        query += " ORDER BY p.votes DESC, p.rating DESC LIMIT :limit"

    data = await fetch_all(engine, query, query_params)
    if data is False:
        return None, "NOT_FOUND"
    elif data is None:
        return None, "ERROR"
    return data, "OK"

async def get_movies_by_id(movieid):
    """
    Obtiene los detalles de una película por su ID.
    
    Args:
        movieid (int): ID de la película a buscar.
    
    Returns:
        tuple: (data, status)
            - data: Diccionario con información de la película o None
            - status: "OK", "NOT_FOUND", o "ERROR"
    """
    query = "SELECT * FROM Peliculas WHERE movieid = :movieid"
    params = {"movieid": movieid}

    data = (await fetch_all(engine, query, params))
    if data is False:
        return None, "NOT_FOUND"
    elif data is None:
        return None, "ERROR"
    return data[0], "OK"

# =============================================================================
# FUNCIONES DE GESTIÓN DE CARRITO
# =============================================================================

async def get_cart(user_id: str, movieid: int | None = None):
    """
    Obtiene el contenido del carrito de un usuario.
    
    Args:
        user_id (str): ID del usuario.
        movieid (int, optional): Si se especifica, excluye esta película del resultado
                                (no la elimina de la base de datos).
    
    Returns:
        tuple: (data, status)
            - data: Lista de diccionarios con películas del carrito o None
            - status: "OK", "CART_EMPTY", "NOT_FOUND", o "ERROR"
    """
    query = """
    SELECT cart_id FROM Carrito WHERE user_id = :user_id
    """
    params = {"user_id": user_id}
    data = await fetch_all(engine, query, params)
    if data is False:
        return None, "NOT_FOUND"
    elif data is None:
        return None, "ERROR"

    query = """
        SELECT
            p.movieid   AS movieid,
            p.title     AS title,
            p.description,
            p.year,
            p.genre,
            p.price
        FROM Carrito c
        JOIN Usuario u        ON u.user_id = c.user_id
        JOIN Carrito_Pelicula cp ON cp.cart_id = c.cart_id
        JOIN Peliculas p         ON p.movieid = cp.movieid
        WHERE c.user_id = :user_id
    """

    params = {"user_id": user_id}

    data = await fetch_all(engine, query, params)  # -> list[dict] | None
    if data is False:
        return None, "CART_EMPTY"
    elif data is None:
        return None, "ERROR"
    # Si te pasan movieid, lo quitas SOLO del resultado (no de la BBDD)
    if movieid is not None:
        data = [row for row in data if row.get("movieid") != movieid]
    if data is False:
        return None, "NOT_FOUND"
    elif data is None:
        return None, "ERROR"
    return data, "OK"

async def add_to_cart(user_id, movieid, quantity=1):
    """
    Añade una película al carrito de un usuario (o incrementa su cantidad).
    
    Args:
        user_id (str): ID del usuario.
        movieid (int): ID de la película a añadir.
    
    Returns:
        str: "OK" si se añadió correctamente o se incrementó la cantidad,
             "NOT_FOUND" si no se encontró el carrito, o "ERROR"
    """
    query = """
                SELECT 1
                FROM Carrito_Pelicula cp
                JOIN Carrito c ON cp.cart_id = c.cart_id
                WHERE c.user_id = :user_id
                AND cp.movieid = :movieid;
            """
    params_check = {"user_id": user_id, "movieid": movieid}
    existing = await fetch_all(engine, query, params_check)
    if existing:
        query = """
            UPDATE Carrito_Pelicula cp
                SET quantity = quantity + :quantity
            FROM Carrito c
            WHERE cp.cart_id = c.cart_id
                AND c.user_id = :user_id
                AND cp.movieid = :movieid
        """
        params_update = {"user_id": user_id, "movieid": movieid, "quantity": quantity}
        update_result = await fetch_all(engine, query, params_update)
        if update_result is True:
            return "OK"
        elif update_result is False:
            return "NOT_FOUND"
        return "ERROR"
        
    query = """
                INSERT INTO Carrito_Pelicula (cart_id, movieid, quantity)
                SELECT c.cart_id, :movieid, :quantity
                FROM Carrito c WHERE c.user_id = :user_id
                ON CONFLICT DO NOTHING
            """
    
    params = {"user_id": user_id, "movieid": movieid, "quantity": quantity}
    ret = await fetch_all(engine, query, params)
    if ret is True:
        return "OK"
    elif ret is False:
        return "NOT_FOUND"
    return "ERROR"

async def delete_from_cart(movieid, token, quantity=1):
    """
    Elimina una película del carrito de un usuario.
    
    Args:
        movieid (int): ID de la película a eliminar.
        token (str): Token de autenticación del usuario.
        quantity (int): Cantidad a eliminar.
    
    Returns:
        str: "OK" si se eliminó correctamente, "NOT_FOUND" si no se encontró,
             "TOO_MANY_MOVIES" si se intenta eliminar más de las existentes,
             o "ERROR" en caso de error
    """
    result = await find_movie_in_cart(movieid, token)
    if result[1] != "OK":
        return result[1]
    
    # Cantidad a eliminar es igual a la cantidad en el carrito: eliminar entrada
    if quantity - result[0].get("quantity", 1) == 0:
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
        if result is True:
            return "OK"
        elif result is False:
            return "NOT_FOUND"
        return "ERROR"
    
    # Cantidad a eliminar es menor a la cantidad en el carrito: decrementar cantidad
    elif quantity < result[0].get("quantity", 1):
        query = """
            UPDATE Carrito_Pelicula cp
                SET quantity = quantity - :quantity
            FROM Carrito c
            WHERE cp.cart_id = c.cart_id
                AND c.user_id = :user_id
                AND cp.movieid = :movieid 
        """
        params = {"movieid": movieid, "user_id": result[0].get("user_id"), "quantity": quantity}
        update_result = await fetch_all(engine, query, params=params)
        if update_result is True:
            return "OK"
        elif update_result is False:
            return "NOT_FOUND"
        return "ERROR"
    
    # Cantidad a eliminar es mayor a la cantidad en el carrito: error
    else:
        return "TOO_MANY_MOVIES"

async def checkout(token):
    """
    Procesa el checkout del carrito del usuario autenticado.
    
    Realiza las siguientes operaciones:
    1. Verifica que el usuario tenga saldo suficiente
    2. Crea un pedido con las películas del carrito
    3. Añade las películas al pedido
    4. Actualiza el saldo del usuario
    5. Vacía el carrito y crea uno nuevo
    
    Args:
        token (str): Token de autenticación del usuario.
    
    Returns:
        tuple: (cart_id, status)
            - cart_id: ID del carrito (que coincide con order_id) o None
            - status: "OK" si el checkout fue exitoso, o código de error en caso contrario
    """
    # Obtener el ID del usuario
    if (user_id := await get_user_id(token)) is None: return None, "USER_NOT_FOUND"
    # Obtener el total del carrito
    if (total := await get_cart_total(user_id)) is None: return None, "PRICE_NOT_FOUND"
    # Obtener el saldo del usuario
    if (current_balance := await get_balance(user_id)) is None: return None, "BALANCE_NOT_FOUND"
    # Verificar si el saldo es suficiente para pagar el carrito
    if (current_balance - total) < 0: return None, "INSUFFICIENT_BALANCE"
    # Crear el pedido
    if (order_id := await create_order(user_id, total)) is None: return None, "CREATE_ORDER_FAILED"
    # Añadir las películas al pedido
    if (await add_movies_to_order(order_id)) is not True: return None, "ADD_MOVIES_TO_ORDER_FAILED"
    query = """
        UPDATE Pedido
        SET paid = TRUE
        WHERE order_id = :order_id
    """
    params = {"order_id": order_id}
    if (await fetch_all(engine, query, params=params)) is None: return None, "UPDATE_PAID_FAILED"
    # Actualizar el saldo del usuario
    #if (await add_to_balance(user_id, -total)) is not True: return None, "ADD_TO_BALANCE_FAILED"
    # Eliminar las películas del carrito
    #if (await empty_cart(user_id)) is not True: return None, "EMPTY_CART_FAILED"

    query = """
        SELECT order_id
        FROM Pedido
        WHERE user_id = :user_id
    """
    params = {"user_id": user_id}
    result = await fetch_all(engine, query, params=params)
    if result:
        return result[0]["order_id"], "OK"
    else:
        return None, "ORDER_ID_NOT_FOUND"

async def get_order(order_id):
    """
    Obtiene los detalles de un pedido, incluyendo las películas asociadas.
    
    Args:
        order_id (int): ID del pedido.
    
    Returns:
        tuple: (order_dict, status)
            - order_dict: Diccionario con información del pedido y sus películas o None
            - status: "OK", "ORDER_NOT_FOUND", "MOVIES_NOT_FOUND", o "ERROR"
    """
    # Obtener los datos del pedido
    query_order = """
        SELECT *
        FROM Pedido
        WHERE order_id = :order_id
    """
    params = {"order_id": order_id}
    order_data = await fetch_all(engine, query_order, params=params)

    if order_data is False:
        return None, "ORDER_NOT_FOUND"
        
    order_dict = {"order_id": order_data[0]["order_id"], "user_id": order_data[0]["user_id"], "total": order_data[0]["total"], "date": order_data[0]["date"]}
    # Obtener las películas del pedido

    query_movies = """
        SELECT m.movieid, m.title, m.price 
        FROM Peliculas m
        JOIN Pedido_Pelicula pm ON m.movieid = pm.movieid
        WHERE pm.order_id = :order_id
    """
    movies_data = await fetch_all(engine, query_movies, params=params)

    movies_list = [
        {
            'movieid': movie.get('movieid'),
            'title': movie.get('title'),
            'price': movie.get('price')
        }
        for movie in movies_data
    ] if movies_data else []

    order_dict["movies"] = movies_list

    if movies_data is False:
        return order_dict, "MOVIES_NOT_FOUND"
    elif movies_data is None:
        return None, "ERROR"
    return order_dict, "OK"

async def new_balance(user_id, amount):
    """
    Establece el saldo de un usuario a un valor específico (no suma, reemplaza).
    
    Args:
        user_id (str): ID del usuario.
        amount (float): Nuevo saldo a establecer.
    
    Returns:
        bool: True si se actualizó correctamente, False en caso contrario
    """
    query = """
        UPDATE Usuario 
        SET balance = :amount
        WHERE user_id = :user_id
    """
    params = {"user_id": user_id, "amount": amount}
    return await fetch_all(engine, query, params=params)

async def rate_movie(user_id, movieid, rating):
    """
    Califica una película.
    
    - Parámetros:
        - user_id: ID del usuario que califica la película
        - movieid: ID de la película que se califica
        - rating: Calificación de la película
    - Respuestas:
        - "OK": Película calificada exitosamente
        - "MOVIE_NOT_FOUND": No se encontró la película
        - "CALIFICATION_FAILED": No se pudo calificar la película
        - "UPDATE_MOVIE_FAILED": No se pudo actualizar la película
    """

    result = await get_movies_by_id(movieid)
    if result[1] != "OK": return "MOVIE_NOT_FOUND"

    query = """
        SELECT rating
        FROM Calificacion
        WHERE movieid = :movieid AND user_id = :user_id
    """
    params = {"movieid": movieid, "user_id": user_id}
    result = await fetch_all(engine, query, params=params)
    if result is False or result is None:
        query = """
            UPDATE Peliculas
            SET votes = votes + 1
            WHERE movieid = :movieid
        """
        params = {"movieid": movieid}
        await fetch_all(engine, query, params=params)
    
    query = """
        INSERT INTO Calificacion (user_id, movieid, rating)
        VALUES (:user_id, :movieid, :rating)
        ON CONFLICT(user_id, movieid) DO UPDATE SET rating = :rating
    """
    params = {"user_id": user_id, "movieid": movieid, "rating": rating}
    await fetch_all(engine, query, params=params)

    query_update = """
        UPDATE Peliculas
        SET rating = media_rating(:movieid)
        WHERE movieid = :movieid
    """
    params_update = {"movieid": movieid}
    await fetch_all(engine, query_update, params=params_update)

    return "OK"

# =============================================================================
# FUNCIONES ESTADÍSTICAS
# =============================================================================

async def estadistica_ventas(anio, pais):
    """
    Devuelve pedidos de un año y país concretos, con datos básicos del usuario.

    Args:
        anio (int): Año de los pedidos a recuperar.
        pais (str): Nacionalidad del usuario.

    Returns:
        tuple: (data, status)
            - data: lista de filas o None
            - status: "OK", "NOT_FOUND", "BAD_REQUEST" o "ERROR"
    """
    try:
        anio_int = int(anio)
    except (TypeError, ValueError):
        return None, "BAD_REQUEST"  # Entrada inválida

    if not pais or not isinstance(pais, str):
        return None, "BAD_REQUEST"

    query = """
        SELECT 
            p.order_id,
            p.date,
            p.total,
            u.name AS user_name
        FROM Pedido p
        JOIN Usuario u ON p.user_id = u.user_id
        WHERE u.nationality = :pais
          AND DATE_PART('year', p.date) = :anio
        ORDER BY p.date ASC
    """
    params = {"anio": anio_int, "pais": pais}
    try:
        data = await fetch_all(engine, query, params=params)
    except Exception:
        return None, "ERROR"

    if data is None or data is False:
        return None, "NOT_FOUND"
    return data, "OK"

# =============================================================================
# FUNCIONES AUXILIARES
# =============================================================================

async def find_movie_in_cart(movieid, token):
    """
    Busca una película en el carrito del usuario autenticado.
    
    Args:
        movieid (int): ID de la película a buscar.
        token (str): Token de autenticación del usuario.
    
    Returns:
        tuple: (data, status)
            - data: Diccionario con información de la película en el carrito o None
            - status: "OK", "USER_NOT_FOUND", "MOVIE_NOT_FOUND", o "ERROR"
    """
    if not (user_id := await get_user_id(token)): 
        return None, "USER_NOT_FOUND"

    query = """
        SELECT * 
            FROM Carrito_Pelicula cp
                JOIN Carrito c ON cp.cart_id = c.cart_id
            WHERE cp.movieid = :movieid
                AND c.user_id = :user_id
    """
    params = {"movieid": movieid, "user_id": user_id}
    data = await fetch_all(engine, query, params=params)
    if data is False:
        return None, "MOVIE_NOT_FOUND"
    elif data is None:
        return None, "ERROR"
    return data[0], "OK"

async def get_balance(user_id):
    """
    Obtiene el saldo actual de un usuario.
    
    Args:
        user_id (str): ID del usuario.
    
    Returns:
        float: Saldo del usuario o None si no se encontró el usuario
    """
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
    """
    Suma (o resta si es negativo) una cantidad al saldo de un usuario.
    
    Args:
        user_id (str): ID del usuario.
        amount (float): Cantidad a sumar (puede ser negativa para restar).
    
    Returns:
        bool: True si se actualizó correctamente, False en caso contrario
    """
    query = """
        UPDATE Usuario 
        SET balance = balance + :amount
        WHERE user_id = :user_id
    """
    params = {"user_id": user_id, "amount": amount}
    return await fetch_all(engine, query, params=params)

async def get_cart_total(user_id):
    """
    Calcula el precio total de todas las películas en el carrito de un usuario.
    
    Args:
        user_id (str): ID del usuario.
    
    Returns:
        float: Precio total del carrito, 0.0 si está vacío, o None en caso de error
    """
    query = """
        SELECT SUM(p.price * cp.quantity) as total
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
        try:
            q2 = """
                SELECT discount FROM Usuario WHERE user_id LIKE :target_uid
            """
            res2 = await fetch_all(engine, q2, params={"target_uid": user_id})
            # Comprueba que res2 contiene filas y que el campo discount no es None
            if res2 is not None:
                print("Descuento encontrado para el usuario:", res2[0]["discount"])
                try:
                    discount = float(res2[0]["discount"])
                except (ValueError, TypeError):
                    discount = 0.0
                # El valor del descuento está garantizado entre 0 y 100, pero por
                # seguridad lo recortamos a ese rango
                if discount > 0.0 and discount <= 100.0:
                    total = total * (1 - (discount / 100.0))
                    print("Descuento aplicado:", discount, "% TOTAL:", total)
                    return float(total)
        except Exception:
            return float(total)
        return float(total)
    else:
        return None

async def empty_cart(user_id):
    """
    Elimina todas las películas del carrito de un usuario.
    
    Args:
        user_id (str): ID del usuario.
    
    Returns:
        bool: True si se vació correctamente, False en caso contrario
    """
    params = {"user_id": user_id}
    query = """
        DELETE
            FROM Carrito_Pelicula cp
                USING Carrito c
            WHERE cp.cart_id = c.cart_id
                AND c.user_id = :user_id
    """
    result = await fetch_all(engine, query, params=params)
    if result is not True:
        return False
    
    query = """
        DELETE
            FROM Carrito c
            WHERE c.user_id = :user_id
    """
    params = {"user_id": user_id}
    result = await fetch_all(engine, query, params=params)
    if result is not True:
        return False

    query = """
        INSERT INTO Carrito (user_id)
        VALUES (:user_id)
    """
    result = await fetch_all(engine, query, params=params)
    if result is not True:
        return False
    return True

async def get_user_id(token):
    """
    Obtiene el ID de usuario a partir de su token de autenticación.
    
    Args:
        token (str): Token de autenticación.
    
    Returns:
        str: ID del usuario o None si el token no es válido
    """
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
    """
    Crea un nuevo pedido a partir del carrito del usuario.
    
    El order_id del pedido se establece igual al cart_id del carrito.
    
    Args:
        user_id (str): ID del usuario.
        total (float): Precio total del pedido.
    
    Returns:
        list: Lista con el resultado de la inserción (con order_id) o None si falló
    """
    query = """
        SELECT cart_id
        FROM Carrito
        WHERE user_id = :user_id
    """
    params = {"user_id": user_id}
    result = await fetch_all(engine, query, params=params)
    if not result:
        return None
    cart_id = result[0]["cart_id"]
    if not cart_id:
        return None

    query = """
        INSERT INTO Pedido (order_id, user_id, total, date)
        VALUES (:order_id, :user_id, :total, NOW())
        RETURNING order_id
    """
    params = {"order_id": cart_id, "user_id": user_id, "total": total}
    if await fetch_all(engine, query, params=params) is not True:
        return None
    return cart_id

async def add_movies_to_order(order_id):
    """
    Copia todas las películas del carrito al pedido.
    
    Args:
        order_id (int): ID del pedido (que coincide con cart_id).
    
    Returns:
        bool: True si se añadieron correctamente, False en caso contrario
    """
    query = """
        INSERT INTO Pedido_Pelicula (order_id, movieid, quantity)
        SELECT :order_id, movieid, quantity
        FROM Carrito_Pelicula
        WHERE cart_id = :cart_id
    """
    params = {"order_id": order_id, "cart_id": order_id}
    return await fetch_all(engine, query, params=params)

async def fetch_all(engine, query, params={}):
    """
    Ejecuta una consulta SQL de forma asíncrona.
    
    Maneja tanto consultas de lectura (SELECT) como de modificación (INSERT, UPDATE, DELETE).
    Para consultas de modificación, usa transacciones con commit automático.
    
    Args:
        engine: Motor de SQLAlchemy para la conexión.
        query (str): Consulta SQL a ejecutar.
        params (dict, optional): Parámetros para la consulta preparada.
    
    Returns:
        Para SELECT:
            - list: Lista de diccionarios con los resultados
            - False: Si no hay resultados
            - None: Si hay un error
        Para INSERT/UPDATE/DELETE:
            - True: Si la operación afectó filas o fue exitosa
            - False: Si no se afectaron filas (UPDATE)
            - None: Si hay un error
    """
    async with engine.connect() as conn:
        query_upper = query.strip().upper()
        is_modification = query_upper.startswith(('INSERT', 'UPDATE', 'DELETE'))
        
        if is_modification:
            async with conn.begin():
                try:
                    result = await conn.execute(text(query), params)
                    if result.rowcount > 0:
                        return True
                    elif query_upper.startswith(('DELETE')) or query_upper.startswith(('INSERT')):
                        return True
                    else:
                        return False
                except Exception as exc:
                    return None
        else:
            try:
                result = await conn.execute(text(query), params)
                rows = result.all()
                if len(rows) > 0:
                    keys = result.keys()
                    data = [dict(zip(keys, row)) for row in rows]
                    return data
                else:
                    return False
            except Exception as exc:
                return None

# =============================================================================
# SERVIDOR HTTP - API REST (QUART)
# =============================================================================

app = Quart(__name__)

@app.route("/movies", methods=["PUT"])
async def http_add_movie():
    """
    Endpoint HTTP para crear una película (solo admin).
    
    - Método: PUT
    - Path: /movies
    - Body (query/body): title, description, year, genre, price
    - Comportamiento: Llama a add_movie(body)
    - Respuestas esperadas:
        HTTPStatus.OK: {"status":"OK"} - Película creada correctamente
        HTTPStatus.BAD_REQUEST: {"status":"ERROR", "message": "..."} - Datos requeridos faltantes
        HTTPStatus.UNAUTHORIZED: {"status":"ERROR", "message": "..."} - Usuario no admin o no encontrado
        HTTPStatus.INTERNAL_SERVER_ERROR: {"status":"ERROR", "message": "..."} - Error interno
    """
    try:
        auth = request.headers.get("Authorization", "")
        if not auth.startswith("Bearer "):
            return jsonify({'status': 'ERROR', 'message': 'Falta Authorization Bearer'}), HTTPStatus.BAD_REQUEST
        
        token = auth.split(" ", 1)[1].strip()

        # Verificar si el usuario es admin
        if not (user_id := await get_user_id(token)):
            return jsonify({'status': 'ERROR', 'message': 'Usuario no encontrado.'}), HTTPStatus.UNAUTHORIZED
        if not await user.comprobar_token_admin(token):
            return jsonify({'status': 'ERROR', 'message': 'Acceso denegado. Se requieren privilegios de administrador.'}), HTTPStatus.UNAUTHORIZED

        body = await request.get_json(silent=True) or {}

        data, status = await add_movie(body)
        if status == "OK":
            return jsonify({'status': 'OK'}), HTTPStatus.OK
        elif status == "BAD_REQUEST":
            return jsonify({'status': 'ERROR', 'message': 'Solicitud incorrecta. Faltan campos obligatorios.'}), HTTPStatus.BAD_REQUEST
        return jsonify({'status': 'ERROR', 'message': 'No se pudo crear la película.'}), HTTPStatus.INTERNAL_SERVER_ERROR

    except Exception as exc:
        return jsonify({"status": "ERROR", "message": str(exc)}), HTTPStatus.INTERNAL_SERVER_ERROR

@app.route("/movies", methods=["POST"])
async def http_update_movies():
    """
    Endpoint HTTP para actualizar una película (solo admin).
    
    - Método: POST
    - Path: /movies
    - Body (query/body): movieid (obligatorio) y campos a actualizar
    - Comportamiento: Llama a update_movie(movieid, body)
    - Respuestas esperadas:
        HTTPStatus.OK: {"status":"OK"} - Película actualizada
        HTTPStatus.BAD_REQUEST: {"status":"ERROR", "message": "..."} - movieid faltante o sin campos válidos
        HTTPStatus.NOT_FOUND: {"status":"ERROR", "message": "..."} - Película no encontrada
        HTTPStatus.UNAUTHORIZED: {"status":"ERROR", "message": "..."} - Usuario no admin o no encontrado
        HTTPStatus.INTERNAL_SERVER_ERROR: {"status":"ERROR", "message": "..."} - Error interno
    """
    try:
        auth = request.headers.get("Authorization", "")
        if not auth.startswith("Bearer "):
            return jsonify({'status': 'ERROR', 'message': 'Falta Authorization Bearer'}), HTTPStatus.BAD_REQUEST
        
        token = auth.split(" ", 1)[1].strip()

        # Verificar si el usuario es admin
        if not (user_id := await get_user_id(token)):
            return jsonify({'status': 'ERROR', 'message': 'Usuario no encontrado.'}), HTTPStatus.UNAUTHORIZED
        if not await user.comprobar_token_admin(token):
            return jsonify({'status': 'ERROR', 'message': 'Acceso denegado. Se requieren privilegios de administrador.'}), HTTPStatus.UNAUTHORIZED

        body = await request.get_json(silent=True) or {}

        if not body.get("movieid"):
            return jsonify({'status': 'ERROR', 'message': 'movieid es obligatorio.'}), HTTPStatus.BAD_REQUEST

        data, status = await update_movie(body.get("movieid"), body)

        if status == "OK":
            return jsonify({'status': 'OK'}), HTTPStatus.OK
        elif status == "NOT_FOUND":
            return jsonify({'status': 'ERROR', 'message': 'Película no encontrada.'}), HTTPStatus.NOT_FOUND
        elif status == "BAD_REQUEST":
            return jsonify({'status': 'ERROR', 'message': 'Solicitud incorrecta. No se proporcionaron campos para actualizar.'}), HTTPStatus.BAD_REQUEST
        return jsonify({'status': 'ERROR', 'message': 'No se pudo actualizar la película.'}), HTTPStatus.INTERNAL_SERVER_ERROR

    except Exception as exc:
        return jsonify({"status": "ERROR", "message": str(exc)}), HTTPStatus.INTERNAL_SERVER_ERROR

@app.route("/movies", methods=["DELETE"])
async def http_delete_movies():
    """
    Endpoint HTTP para eliminar una película (solo admin).
    
    - Método: DELETE
    - Path: /movies
    - Body (query/body): movieid (obligatorio)
    - Comportamiento: Llama a remove_movie(movieid)
    - Respuestas esperadas:
        HTTPStatus.OK: {"status":"OK"} - Película eliminada
        HTTPStatus.BAD_REQUEST: {"status":"ERROR", "message": "..."} - movieid faltante
        HTTPStatus.NOT_FOUND: {"status":"ERROR", "message": "..."} - Película no encontrada
        HTTPStatus.UNAUTHORIZED: {"status":"ERROR", "message": "..."} - Usuario no admin o no encontrado
        HTTPStatus.INTERNAL_SERVER_ERROR: {"status":"ERROR", "message": "..."} - Error interno
    """
    try:
        auth = request.headers.get("Authorization", "")
        if not auth.startswith("Bearer "):
            return jsonify({'status': 'ERROR', 'message': 'Falta Authorization Bearer'}), HTTPStatus.BAD_REQUEST
        
        token = auth.split(" ", 1)[1].strip()

        # Verificar si el usuario es admin
        if not (user_id := await get_user_id(token)):
            return jsonify({'status': 'ERROR', 'message': 'Usuario no encontrado.'}), HTTPStatus.UNAUTHORIZED
        if not await user.comprobar_token_admin(token):
            return jsonify({'status': 'ERROR', 'message': 'Acceso denegado. Se requieren privilegios de administrador.'}), HTTPStatus.UNAUTHORIZED

        body = await request.get_json(silent=True) or {}

        if not body.get("movieid"):
            return jsonify({'status': 'ERROR', 'message': 'movieid es obligatorio.'}), HTTPStatus.BAD_REQUEST

        data, status = await remove_movie(body.get("movieid"))

        if status == "OK":
            return jsonify({'status': 'OK'}), HTTPStatus.OK
        elif status == "NOT_FOUND":
            return jsonify({'status': 'ERROR', 'message': 'Película no encontrada.'}), HTTPStatus.NOT_FOUND
        return jsonify({'status': 'ERROR', 'message': 'No se pudo eliminar la película.'}), HTTPStatus.INTERNAL_SERVER_ERROR

    except Exception as exc:
        return jsonify({"status": "ERROR", "message": str(exc)}), HTTPStatus.INTERNAL_SERVER_ERROR

@app.route("/movies", methods=["GET"])
async def http_get_movies():
    """
    Endpoint HTTP para listar/filtrar películas.
    
    - Método: GET
    - Path: /movies
    - Query params: title, year, genre, actor, actors, N
    - Comportamiento: Llama a get_movies(params)
    - Respuestas esperadas:
        HTTPStatus.OK: <lista de películas> - Resultados devueltos (vacío si no hay)
        HTTPStatus.BAD_REQUEST: {"status":"ERROR", "message": "..."} - Falta Authorization
        HTTPStatus.IM_A_TEAPOT: {} - Límite N inválido (<=0)
        HTTPStatus.INTERNAL_SERVER_ERROR: {"status":"ERROR", "message": "..."} - Error interno
    """
    try:
        auth = request.headers.get("Authorization", "")
        if not auth.startswith("Bearer "):
            return jsonify({'status': 'ERROR', 'message': 'Falta Authorization Bearer'}), HTTPStatus.BAD_REQUEST
        
        token = auth.split(" ", 1)[1].strip()

        if not (user_id := await get_user_id(token)):
            return jsonify({'status': 'ERROR', 'message': 'Usuario no encontrado.'}), HTTPStatus.UNAUTHORIZED

        body = request.args.to_dict(flat=True)

        data, status = await get_movies(body)
        if status == "OK":
            return jsonify(data), HTTPStatus.OK
        elif status == "NOT_FOUND" and data is None:
            return jsonify({}), HTTPStatus.OK
        elif status == "LIMIT_ERROR_VALUE":
            return jsonify({}), HTTPStatus.IM_A_TEAPOT

        return jsonify({'status': 'ERROR', 'message': 'No se encontraron películas que coincidan con los criterios de búsqueda.'}), HTTPStatus.INTERNAL_SERVER_ERROR

    except Exception as exc:
        return jsonify({"status": "ERROR", "message": str(exc)}), HTTPStatus.INTERNAL_SERVER_ERROR

    
@app.route("/movies/<int:movieid>", methods=["GET"])
async def http_get_movie_by_id(movieid):
    """
    Endpoint HTTP para obtener detalles de una película.
    
    - Método: GET
    - Path: /movies/<movieid>
    - Comportamiento: Llama a get_movies_by_id(movieid)
    - Respuestas esperadas:
        HTTPStatus.OK: <película> - Película encontrada
        HTTPStatus.NOT_FOUND: {} - Película no encontrada
        HTTPStatus.BAD_REQUEST: {"status":"ERROR", "message": "..."} - Falta Authorization
        HTTPStatus.INTERNAL_SERVER_ERROR: {"status":"ERROR", "message": "..."} - Error interno
    """
    try:
        auth = request.headers.get("Authorization", "")
        if not auth.startswith("Bearer "):
            return jsonify({'status': 'ERROR', 'message': 'Falta Authorization Bearer'}), HTTPStatus.BAD_REQUEST
        
        token = auth.split(" ", 1)[1].strip()

        if not (user_id := await get_user_id(token)):
            return jsonify({'status': 'ERROR', 'message': 'Usuario no encontrado.'}), HTTPStatus.UNAUTHORIZED

        data, status = await get_movies_by_id(movieid)
        if status == "OK":
            return jsonify(data), HTTPStatus.OK
        elif status == "NOT_FOUND":
            return jsonify({}), HTTPStatus.NOT_FOUND

        return jsonify({'status': 'ERROR', 'message': 'No se encontraron películas que coincidan con los criterios de búsqueda.'}), HTTPStatus.INTERNAL_SERVER_ERROR
        
    except Exception as exc:
        return jsonify({'status': 'ERROR', 'message': str(exc)}), HTTPStatus.INTERNAL_SERVER_ERROR


@app.route("/cart", methods=["GET"])
async def http_get_cart():
    """
    Endpoint HTTP para obtener el carrito del usuario autenticado.
    
    - Método: GET
    - Path: /cart
    - Comportamiento: Llama a get_cart(user_id)
    - Respuestas esperadas:
        HTTPStatus.OK: <carrito> - Carrito encontrado (vacío si no hay items)
        HTTPStatus.NOT_FOUND: {"status":"ERROR", "message": "..."} - Carrito no encontrado
        HTTPStatus.BAD_REQUEST: {"status":"ERROR", "message": "..."} - Falta Authorization
        HTTPStatus.INTERNAL_SERVER_ERROR: {"status":"ERROR", "message": "..."} - Error interno
    """
    try:
        auth = request.headers.get("Authorization", "")
        if not auth.startswith("Bearer "):
            return jsonify({'status': 'ERROR', 'message': 'Falta Authorization Bearer'}), HTTPStatus.BAD_REQUEST
        
        token = auth.split(" ", 1)[1].strip()

        if not (user_id := await get_user_id(token)):
            return None, "USER_NOT_FOUND"
        
        data, status = await get_cart(user_id)
        if status == "OK":
            return jsonify(data), HTTPStatus.OK
        elif status == "NOT_FOUND":
            return jsonify({'status': 'ERROR', 'message': 'No se encontró el carrito.'}), HTTPStatus.NOT_FOUND
        elif status == "CART_EMPTY":
            return jsonify({}), HTTPStatus.OK
        else:
            return jsonify({'status': 'ERROR', 'message': 'El carrito está vacío o no se encontró.'}), HTTPStatus.NOT_FOUND
    except Exception as exc:
        return jsonify({'status': 'ERROR', 'message': str(exc)}), HTTPStatus.INTERNAL_SERVER_ERROR

@app.route("/cart/<int:movieid>", methods=["PUT"])
async def http_add_to_cart(movieid):
    """
    Endpoint HTTP para añadir/incrementar una película en el carrito.
    
    - Método: PUT
    - Path: /cart/<movieid>
    - Body/Query: quantity (opcional, por defecto 1)
    - Comportamiento: Llama a add_to_cart(user_id, movieid, quantity)
    - Respuestas esperadas:
        HTTPStatus.OK: {"status":"OK", "message": "..."} - Película añadida
        HTTPStatus.BAD_REQUEST: {"status":"ERROR", "message": "..."} - Falta Authorization o quantity inválida
        HTTPStatus.NOT_FOUND: {"status":"ERROR", "message": "..."} - Película o recursos no encontrados
        HTTPStatus.UNAUTHORIZED: {"status":"ERROR", "message": "..."} - Usuario no encontrado
        HTTPStatus.INTERNAL_SERVER_ERROR: {"status":"ERROR", "message": "..."} - Error interno
    """
    try:
        auth = request.headers.get("Authorization", "")
        if not auth.startswith("Bearer "):
            return jsonify({'status': 'ERROR', 'message': 'Falta Authorization Bearer'}), HTTPStatus.BAD_REQUEST
        
        quantity = request.args.get("quantity")
        if quantity is None:
            body = await request.get_json(silent=True)
            quantity = body.get("quantity") if body else None
        try:
            quantity = int(quantity) if quantity is not None else 1
        except (TypeError, ValueError):
            return jsonify({'status': 'ERROR', 'message': 'La cantidad debe ser un número entero.'}), HTTPStatus.BAD_REQUEST
        if quantity <= 0:
            return jsonify({'status': 'ERROR', 'message': 'La cantidad debe ser mayor que cero.'}), HTTPStatus.BAD_REQUEST

        token = auth.split(" ", 1)[1].strip()

        user_id = await get_user_id(token)
        if not user_id:
            return jsonify({'status': 'ERROR', 'message': 'Usuario no encontrado.'}), HTTPStatus.UNAUTHORIZED

        status = await add_to_cart(user_id, movieid, quantity)

        if status == "OK":
            return jsonify({'status': 'OK', 'message': 'Película añadida al carrito.'}), HTTPStatus.OK
        elif status == "USER_NOT_FOUND":
            return jsonify({'status': 'ERROR', 'message': 'Usuario no encontrado.'}), HTTPStatus.UNAUTHORIZED
        elif status == "MOVIE_NOT_FOUND":
            return jsonify({'status': 'ERROR', 'message': 'No se encontró la película.'}), HTTPStatus.NOT_FOUND
        elif status == "NOT_FOUND":
            return jsonify({'status': 'ERROR', 'message': 'No se ha encontrado alguna de las búsquedas'}), HTTPStatus.NOT_FOUND
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

        quantity = request.args.get("quantity")
        if quantity is None:
            body = await request.get_json(silent=True)
            quantity = body.get("quantity") if body else None
        try:
            quantity = int(quantity) if quantity is not None else 1
        except (TypeError, ValueError):
            return jsonify({'status': 'ERROR', 'message': 'La cantidad debe ser un número entero.'}), HTTPStatus.BAD_REQUEST
        if quantity <= 0:
            return jsonify({'status': 'ERROR', 'message': 'La cantidad debe ser mayor que cero.'}), HTTPStatus.BAD_REQUEST

        result = await delete_from_cart(movieid, token, quantity)
        if result == "OK":
            return jsonify({'status': 'OK', 'message': 'Película eliminada del carrito.'}), HTTPStatus.OK
        elif result == "USER_NOT_FOUND":
            return jsonify({'status': 'ERROR', 'message': 'Usuario no encontrado.'}), HTTPStatus.UNAUTHORIZED
        elif result == "MOVIE_NOT_FOUND":
            return jsonify({'status': 'ERROR', 'message': 'No se encontró la película en el carrito.'}), HTTPStatus.NOT_FOUND
        elif result == "NOT_FOUND":
            return jsonify({'status': 'OK', 'message': 'No se encontró la película en el carrito.'}), HTTPStatus.NOT_FOUND
        elif result == "ERROR":
            return jsonify({'status': 'ERROR', 'message': 'No se pudo eliminar la película del carrito.'}), HTTPStatus.INTERNAL_SERVER_ERROR
        elif result == "TOO_MANY_MOVIES":
            return jsonify({'status': 'ERROR', 'message': 'Se intentó eliminar más películas de las que existen en el carrito.'}), HTTPStatus.CONFLICT
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
        elif result == "ORDER_ID_NOT_FOUND":
            return jsonify({'status': 'ERROR', 'message': 'No existe pedido para el usuario.'}), HTTPStatus.INTERNAL_SERVER_ERROR
        elif result == "CREATE_ORDER_FAILED":
            return jsonify({'status': 'ERROR', 'message': 'No se pudo crear el pedido.'}), HTTPStatus.INTERNAL_SERVER_ERROR
        elif result == "ADD_MOVIES_TO_ORDER_FAILED":
            return jsonify({'status': 'ERROR', 'message': 'No se pudo añadir las películas al pedido.'}), HTTPStatus.INTERNAL_SERVER_ERROR
        elif result == "UPDATE_PAID_FAILED":
            return jsonify({'status': 'ERROR', 'message': 'No se pudo actualizar el pago del pedido.'}), HTTPStatus.INTERNAL_SERVER_ERROR
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
        HTTPStatus.INTERNAL_SERVER_ERROR: {"status":"ERROR", "message": "..."} - Error interno del servidor
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
        result, status = await get_order(order_id)

        if status == "OK":
            return jsonify(result), HTTPStatus.OK
        elif status == "ORDER_NOT_FOUND":
            return jsonify({'status': 'ERROR', 'message': 'No se encontró el pedido.'}), HTTPStatus.NOT_FOUND
        elif status == "MOVIES_NOT_FOUND":
            return jsonify(result), HTTPStatus.OK
        else:
            return jsonify({'status': 'ERROR', 'message': 'No se encontró el pedido.'}), HTTPStatus.IM_A_TEAPOT
    except Exception as exc:
        return jsonify({'status': 'ERROR', 'message': str(exc)}), HTTPStatus.INTERNAL_SERVER_ERROR


@app.route("/movies/calification", methods=["POST"])
async def http_rate_movie():
    """
    Endpoint HTTP para calificar una película.
    
    - Método: POST
    - Path: /movies/calification
    - Comportamiento: Llama a rate_movie(movieid, rating)
    - Respuestas esperadas:
        HTTPStatus.OK: {"status":"OK", "message": "Película calificada exitosamente."} - Película calificada exitosamente
        HTTPStatus.NOT_FOUND: {"status":"ERROR", "message": "No se encontró la película."} - No se encontró la película
        HTTPStatus.INTERNAL_SERVER_ERROR: {"status":"ERROR", "message": "No se pudo calificar la película."} - No se pudo calificar la película
        HTTPStatus.IM_A_TEAPOT: {"status":"ERROR", "message": "El servidor se rehusa a preparar café porque es una tetera."} - El servidor se rehusa a preparar café porque es una tetera
    """
    try:
        auth = request.headers.get("Authorization", "")
        if not auth.startswith("Bearer "):
            return jsonify({'status': 'ERROR', 'message': 'Falta Authorization Bearer'}), HTTPStatus.BAD_REQUEST
        
        token = auth.split(" ", 1)[1].strip()
        if not (user_id := await get_user_id(token)):
            return jsonify({'status': 'ERROR', 'message': 'Usuario no encontrado'}), HTTPStatus.NOT_FOUND
        
        body = (await request.get_json(silent=True))
        if (movieid := body.get("movieid")) is None:
            return jsonify({'status': 'ERROR', 'message': 'Body JSON no contiene la clave \"movieid\"'}), HTTPStatus.BAD_REQUEST
        if (rating := body.get("rating")) is None:
            return jsonify({'status': 'ERROR', 'message': 'Body JSON no contiene la clave \"rating\"'}), HTTPStatus.BAD_REQUEST
        if not (0 <= rating <= 10):
            return jsonify({'status': 'ERROR', 'message': 'La calificación debe estar entre 0 y 10'}), HTTPStatus.BAD_REQUEST
        
        result = await rate_movie(user_id, movieid, rating)
        if result == "OK":
            return jsonify({'status': 'OK', 'message': 'Película calificada exitosamente.'}), HTTPStatus.OK
        elif result == "MOVIE_NOT_FOUND":
            return jsonify({'status': 'ERROR', 'message': 'No se encontró la película.'}), HTTPStatus.NOT_FOUND
        elif result == "CALIFICATION_FAILED":
            return jsonify({'status': 'ERROR', 'message': 'No se pudo calificar la película.'}), HTTPStatus.INTERNAL_SERVER_ERROR
        elif result == "UPDATE_MOVIE_FAILED":
            return jsonify({'status': 'ERROR', 'message': 'No se pudo actualizar la película.'}), HTTPStatus.INTERNAL_SERVER_ERROR
        else:
            return jsonify({'status': 'ERROR', 'message': 'El servidor se rehusa a preparar café porque es una tetera.'}), HTTPStatus.IM_A_TEAPOT
    except Exception as exc:
        return jsonify({'status': 'ERROR', 'message': str(exc)}), HTTPStatus.INTERNAL_SERVER_ERROR

@app.route("/estadisticaVentas/<anio>/<pais>", methods=["GET"])
async def http_estadistica_ventas(anio, pais):
    """
    Endpoint HTTP para obtener los pedidos de un año y país concretos.

    - Método: GET
    - Path: /estadisticaVentas/<anio>/<pais>
    - Headers: Authorization: Bearer <token_admin>
    - Comportamiento: Verifica que el token pertenezca a un admin y llama a
      estadistica_ventas(anio, pais) para recuperar los pedidos (id, fecha,
      total y nombre de usuario).
    - Respuestas esperadas:
        HTTPStatus.OK: devuelve la lista de pedidos.
        HTTPStatus.BAD_REQUEST: falta Authorization Bearer.
        HTTPStatus.UNAUTHORIZED: token no válido o no es admin.
        HTTPStatus.NOT_FOUND: sin datos para la consulta.
        HTTPStatus.INTERNAL_SERVER_ERROR: error al obtener la estadística.
    """
    try:
        auth = request.headers.get("Authorization", "")
        if not auth.startswith("Bearer "):
            return jsonify({'status': 'ERROR', 'message': 'Falta Authorization Bearer'}), HTTPStatus.BAD_REQUEST
        
        token = auth.split(" ", 1)[1].strip()
        if not (user_id := await get_user_id(token)):
            return jsonify({'status': 'ERROR', 'message': 'Usuario no encontrado'}), HTTPStatus.NOT_FOUND

        # Verificar si el usuario es admin
        if not await user.comprobar_token_admin(token):
            return jsonify({'status': 'ERROR', 'message': 'Acceso denegado. Se requieren privilegios de administrador.'}), HTTPStatus.UNAUTHORIZED
        
        data, status = await estadistica_ventas(anio, pais)
        if status == "OK":
            return jsonify(data), HTTPStatus.OK
        if status == "BAD_REQUEST":
            return jsonify({'status': 'ERROR', 'message': 'Parámetros de entrada inválidos.'}), HTTPStatus.BAD_REQUEST
        if status == "NOT_FOUND":
            return jsonify({'status': 'ERROR', 'message': 'No se encontraron datos para la estadística solicitada.'}), HTTPStatus.NOT_FOUND
        return jsonify({'status': 'ERROR', 'message': 'Error al obtener la estadística de ventas.'}), HTTPStatus.INTERNAL_SERVER_ERROR
    except Exception as exc:
        return jsonify({'status': 'ERROR', 'message': str(exc)}), HTTPStatus.INTERNAL_SERVER_ERROR
    

# =============================================================================
# PUNTO DE ENTRADA PRINCIPAL
# =============================================================================

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5051)
