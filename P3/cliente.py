"""
cliente.py - Cliente de Pruebas para el Sistema de Catálogo de Películas

Este módulo implementa un cliente de pruebas completo que verifica todas las
funcionalidades del sistema de catálogo de películas y gestión de usuarios.

Funcionalidades probadas:
    - Creación y autenticación de usuarios
    - Búsqueda y filtrado de películas (título, año, género, actor)
    - Búsqueda por conjunto de actores
    - Obtención de top N películas
    - Gestión del carrito de compra (añadir, eliminar, obtener)
    - Procesamiento de pedidos (checkout)
    - Gestión de saldo de usuarios
    - Sistema de calificación de películas

El cliente realiza pruebas exhaustivas de todos los endpoints de la API y
valida que las respuestas sean correctas según los casos de uso esperados.

Autor: Juan Larrondo Fernández de Córdoba y Ana Pardo Jiménez
Fecha de creación: 28-10-2025
Última modificación: 28-10-2025
Versión: 1.0.0
Python: 3.7+
Dependencias: requests

Uso:
    python cliente.py
    
Requisitos:
    - Servidor de usuarios corriendo en http://127.0.0.1:5050
    - Servidor de catálogo corriendo en http://127.0.0.1:5051
    - Base de datos PostgreSQL inicializada con schema.sql y populate.sql
"""

from math import e
from datetime import datetime
import uuid
import requests
from http import HTTPStatus

# URLs de los servicios
USERS = "http://127.0.0.1:5050"
CATALOG = "http://127.0.0.1:5051"

def ok(name, cond):
    """
    Función auxiliar para imprimir el resultado de una prueba.
    
    Args:
        name (str): Nombre descriptivo de la prueba.
        cond (bool): Condición que indica si la prueba pasó o falló.
    
    Returns:
        bool: El valor de cond (útil para encadenar condiciones).
    """
    status = "OK" if cond else "FAIL"
    print(f"[{status}] {name}")
    return cond

def main():
    """
    Función principal que ejecuta todas las pruebas del sistema.
    
    Las pruebas se organizan en secciones:
    1. Creación y autenticación de usuarios
    2. Consultas al catálogo de películas
    3. Gestión del carrito de compra
    4. Sistema de votación de películas
    5. Pruebas de búsqueda por actores y parámetro N
    6. Limpieza de la base de datos
    """

    print("# =======================================================")
    print("# Creación y autenticación de usuarios para el test")
    print("# =======================================================")

    # Usuario administrador por defecto, debe existir
    r = requests.get(f"{USERS}/user", json={"name": "admin", "password": "admin"})
    if ok("Autenticar usuario administrador predefinido", r.status_code == HTTPStatus.OK):
        data = r.json()
        uid_admin, token_admin = data["uid"], data["token"]
    else:
        print("\nPruebas incompletas: Fin del test por error crítico")
        exit(-1)

    headers_admin = {"Authorization": f"Bearer {token_admin}"}

    # Se asume que el usuario 'Alice' no existe
    r = requests.put(f"{USERS}/user", json={"name": "alice", "password": "secret", "nationality": "Estados Unidos"}, headers=headers_admin)
    if ok("Crear usuario 'alice'", r.status_code == HTTPStatus.OK and r.json()):
        data = r.json()
        uid_alice, _ = data["uid"], data["username"]
    else:
        print("\nPruebas incompletas: Fin del test por error crítico")
        exit(-1)

    # Test: Autenticar el usuario 'alice' recién creado
    r = requests.get(f"{USERS}/user", json={"name": "alice", "password": "secret"})
    if ok("Autenticar usuario 'alice'", r.status_code == HTTPStatus.OK and r.json()["uid"] == uid_alice):
        data = r.json()
        _, token_alice = data["uid"], data["token"]
    else:
        print("\nPruebas incompletas: Fin del test por error crítico")

    # Test: Intentar borrar usuario administrador (debe fallar con FORBIDDEN)
    r = requests.delete(f"{USERS}/user/{uid_admin}", headers=headers_admin)
    ok("Borrar usuario administrador falla", r.status_code == HTTPStatus.FORBIDDEN)

    headers_alice = {"Authorization": f"Bearer {token_alice}"}

    # Test: Intentar crear usuario con token de usuario no administrador (debe fallar con UNAUTHORIZED)
    r = requests.put(f"{USERS}/user", json={"name": "aleatorio", "password": "aleatorio", "nationality": "Estados Unidos"}, headers=headers_alice)
    ok("Crear usuario 'aleatorio' con token de usuario 'alice' falla", r.status_code == HTTPStatus.UNAUTHORIZED)

    # Test: Intentar borrar usuario con token de usuario no administrador (debe fallar con UNAUTHORIZED)
    r = requests.delete(f"{USERS}/user/{uid_alice}", headers=headers_alice)
    ok("Borrar usuario 'alice' con token de usuario 'alice' falla", r.status_code == HTTPStatus.UNAUTHORIZED)

    print("# =======================================================")
    print("# Distintas consultas de alice al catálogo de películas")
    print("# =======================================================")

    # Test: Obtener todas las películas del catálogo
    r = requests.get(f"{CATALOG}/movies", headers=headers_alice)
    if ok("Obtener catálogo de películas completo", r.status_code == HTTPStatus.OK):
        data = r.json()
        if data:
            for movie in data:
                print(f"\t- {movie['title']}\n\t  {movie['description']}")
        else:
            print("\tNo hay películas en el catálogo")
    
    # Test: Buscar películas por título (búsqueda parcial con 'matrix')
    # Se asume que al menos hay una película que cumple la condición. Si no se reciben
    # los datos de ninguna película el test se da por no satisfecho
    r = requests.get(f"{CATALOG}/movies", params={"title": "matrix"}, headers=headers_alice)
    if ok("Buscar películas con 'matrix' en el título", r.status_code == HTTPStatus.OK and r.json()):
        data = r.json()
        if data:
            for movie in data:
                print(f"\t[{movie['movieid']}] {movie['title']}")

    # Test: Buscar películas con título inexistente (debe devolver lista vacía)
    r = requests.get(f"{CATALOG}/movies", params={"title": "No debe haber pelis con este título"}, headers=headers_alice)
    ok("Búsqueda fallida de películas por título", r.status_code == HTTPStatus.OK and not r.json())
    
    # Test: Buscar películas por múltiples criterios (título, año y género)
    # Los ids de estas búsqueda se utilizarán después para las pruebas de la gestión
    # del carrito
    movieids = []
    r = requests.get(f"{CATALOG}/movies", params={"title": "Gladiator", "year": 2000, "genre": "action"}, headers=headers_alice)
    if ok("Buscar películas por varios campos de movie", r.status_code == HTTPStatus.OK):
        data = r.json()
        if data:
            for movie in data:
                print(f"\t[{movie['movieid']}] {movie['title']}")
                movieids.append(movie['movieid'])
            
            r = requests.get(f"{CATALOG}/movies/{movieids[0]}", headers=headers_alice)
            if ok(f"Obtener detalles de la película con ID [{movieids[0]}]", 
                  r.status_code == HTTPStatus.OK and r.json() and r.json()['movieid'] == movieids[0]):
                data = r.json()
                print(f"\t{data['title']} ({data['year']})")
                print(f"\tGénero: {movie['genre']}")
                print(f"\tDescripción: {movie['description']}")
                print(f"\tPrecio: {movie['price']}")
        else:
            print("\tNo se encontraron películas.")
    
    # Test: Buscar películas con criterios que no coinciden (año 2025 no existe)
    r = requests.get(f"{CATALOG}/movies", params={"title": "Gladiator", "year": 2025, "genre": "action"}, headers=headers_alice)
    ok("Buscar películas por varios campos de movie fallida", r.status_code == HTTPStatus.OK and not r.json())
    
    # Test: Obtener detalles de una película con ID inexistente (debe devolver NOT_FOUND)
    r = requests.get(f"{CATALOG}/movies/99999999", headers=headers_alice)
    ok(f"Obtener detalles de la película con ID no válido", HTTPStatus.NOT_FOUND)
    
    # Test: Buscar películas por actor (debe encontrar películas donde participa 'Tom Hardy')
    r = requests.get(f"{CATALOG}/movies", params={"actor": "Tom Hardy"}, headers=headers_alice)
    if ok("Buscar películas en las que participa 'Tom Hardy'", r.status_code == HTTPStatus.OK and r.json()):
        data = r.json()
        if data:
            for movie in data:
                print(f"\t[{movie['movieid']}] {movie['title']}")
                movieids.append(movie['movieid'])

    # Test: Buscar películas por actor inexistente (debe devolver lista vacía)
    r = requests.get(f"{CATALOG}/movies", params={"actor": "Juan Larrondo"}, headers=headers_alice)
    ok("Buscar películas en las que participa 'Juan Larrondo'", r.status_code == HTTPStatus.OK and not r.json())
    
    print("# =======================================================")
    print("# Gestión del carrito de alice")
    print("# =======================================================")

    final_stock = 0
    r = requests.get(f"{CATALOG}/movies", headers=headers_admin)
    if ok("Obtener catálogo de películas", r.status_code == HTTPStatus.OK and r.json()):
        data = r.json()
        if data:
            for movie in data: final_stock += movie['stock']

    # Aumentar el saldo de alice
    r = requests.post(f"{CATALOG}/user/credit", json={"amount": -1}, headers=headers_alice)
    if ok("Aumentar el saldo de alice", r.status_code == HTTPStatus.OK and r.json()):
        saldo = float(r.json()["new_credit"])
        print(f"\tSaldo actualizado a {saldo:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))

    # Añadir películas al carrito
    for movieid in movieids:
        r = requests.put(f"{CATALOG}/cart/{movieid}", headers=headers_alice)
        if ok(f"Añadir película con ID [{movieid}] al carrito", r.status_code == HTTPStatus.OK):
            r = requests.get(f"{CATALOG}/cart", headers=headers_alice)
            if ok("Obtener carrito del usuario con el nuevo contenido", r.status_code == HTTPStatus.OK and r.json()):
                data = r.json()
                if data:
                    for movie in data:
                        print(f"\t{movie['quantity']} [id: {movie['movieid']}] {movie['title']} - {movie['price']}")

    # Añadir película al carrito más de una vez (incrementa cantidad)
    if movieids:
        extra_quantity = 2
        total_quantity = 1 + extra_quantity  # ya se añadió 1 unidad en el bucle anterior

        r = requests.put(f"{CATALOG}/cart/{movieids[0]}", json={"quantity": extra_quantity}, headers=headers_alice)
        ok(f"Añadir {extra_quantity} unidades extra de la película con ID [{movieids[0]}] al carrito", r.status_code == HTTPStatus.OK)

        r = requests.get(f"{CATALOG}/cart", headers=headers_alice)
        if ok("Obtener carrito del usuario con el nuevo contenido", r.status_code == HTTPStatus.OK and r.json()):
            data = r.json()
            if data:
                for movie in data:
                    print(f"\t{movie['quantity']} [id: {movie['movieid']}] {movie['title']} - {movie['price']}")
    
        # Intentar borrar más unidades de las que hay debe fallar
        r = requests.delete(f"{CATALOG}/cart/{movieids[0]}", json={"quantity": total_quantity + 1}, headers=headers_alice)
        ok("Intentar eliminar más unidades de las existentes en el carrito", r.status_code == HTTPStatus.CONFLICT)

        r = requests.get(f"{CATALOG}/cart", headers=headers_alice)
        if ok("Obtener carrito del usuario con el nuevo contenido", r.status_code == HTTPStatus.OK and r.json()):
            data = r.json()
            if data:
                for movie in data:
                    print(f"\t{movie['quantity']} [id: {movie['movieid']}] {movie['title']} - {movie['price']}")

        # Eliminar todas las unidades añadidas de esa película
        r = requests.delete(f"{CATALOG}/cart/{movieids[0]}", json={"quantity": total_quantity}, headers=headers_alice)
        if ok(f"Eliminar la película con ID [{movieids[0]}] del carrito usando quantity: {total_quantity}", r.status_code == HTTPStatus.OK):
            r = requests.get(f"{CATALOG}/cart", headers=headers_alice)
            if ok(f"Obtener carrito del usuario sin la película [{movieids[0]}]", r.status_code == HTTPStatus.OK):
                data = r.json()
                remaining_ids = [movie["movieid"] for movie in data] if data else []
                ok("La película eliminada ya no está en el carrito", movieids[0] not in remaining_ids)
                if data:
                    for movie in data:
                        print(f"\t{movie['quantity']} [id: {movie['movieid']}] {movie['title']} - {movie['price']}")
                else:
                    print("\tEl carrito está vacío.")

    # Checkout del carrito con saldo insuficiente
    r = requests.post(f"{CATALOG}/cart/checkout", headers=headers_alice)
    ok("Checkout del carrito con saldo insuficiente", r.status_code == HTTPStatus.PAYMENT_REQUIRED)

    # Aumentar el saldo de alice a un valor muy alto
    r = requests.post(f"{CATALOG}/user/credit", json={"amount": 1000000}, headers=headers_alice)
    if ok("Aumentar el saldo de alice", r.status_code == HTTPStatus.OK and r.json()):
        saldo = float(r.json()["new_credit"])
        print(f"\tSaldo actualizado a {saldo:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))

    # Checkout del carrito
    r = requests.post(f"{CATALOG}/cart/checkout", headers=headers_alice)
    if ok("Checkout del carrito", r.status_code == HTTPStatus.OK and r.json()):
        data = r.json()
        print(f"\tPedido {data['orderid']} creado correctamente:")

        # Obtener datos del pedido
        r = requests.get(f"{CATALOG}/orders/{data['orderid']}", headers=headers_alice)
        if ok(f"Recuperar datos del pedido {data['orderid']}", r.status_code == HTTPStatus.OK and r.json()):
            order = r.json()
            print(f"\tFecha: {order['date']}\n\tPrecio: {order['total']}")
            print(f"\tContenido - {len(order['movies'])} pelicula(s):")
            for movie in order['movies']:
                    print(f"\t- {movie['quantity']} [id: {movie['movieid']}] {movie['title']} ({movie['price']})")
                    final_stock -= movie['quantity']
        

        # Test: Verificar que el carrito está vacío después del checkout
        r = requests.get(f"{CATALOG}/cart", headers=headers_alice)
        ok("Obtener carrito vacío después de la venta", r.status_code == HTTPStatus.OK and not r.json())


    print("# =======================================================")
    print("# Pruebas de creación/actualización/eliminación de películas")
    print("# =======================================================")

    test_title = f"Test Movie {uuid.uuid4().hex[:8]}"
    new_movie = {
        "title": test_title,
        "description": "Película de prueba",
        "year": 2024,
        "genre": "Test",
        "price": 5.5,
    }

    r = requests.put(f"{CATALOG}/movies", json=new_movie, headers=headers_admin)
    ok("Crear película de prueba", r.status_code == HTTPStatus.OK and r.json().get("status") == "OK")

    r = requests.get(f"{CATALOG}/movies", params={"title": test_title}, headers=headers_admin)
    movieid_test = None
    if ok("Localizar película recién creada", r.status_code == HTTPStatus.OK and r.json()):
        movieid_test = r.json()[0]["movieid"]
        print(f"\tID de la película de prueba: {movieid_test}")

    if movieid_test:
        r = requests.post(f"{CATALOG}/movies", json={"movieid": movieid_test, "genre": "UpdatedGenre"}, headers=headers_admin)
        ok("Actualizar película de prueba", r.status_code == HTTPStatus.OK and r.json().get("status") == "OK")

        r = requests.delete(f"{CATALOG}/movies", json={"movieid": movieid_test}, headers=headers_admin)
        ok("Eliminar película de prueba", r.status_code == HTTPStatus.OK and r.json().get("status") == "OK")

        r = requests.get(f"{CATALOG}/movies/{movieid_test}", headers=headers_admin)
        ok("Consultar película eliminada devuelve NOT_FOUND", r.status_code == HTTPStatus.NOT_FOUND)
    
    print("# =======================================================")
    print("# Votar películas")
    print("# =======================================================")

    import random

    # Test: Obtener catálogo completo para votar películas
    movieids = []
    r = requests.get(f"{CATALOG}/movies", headers=headers_alice)
    if ok("Obtener catálogo de películas completo", r.status_code == HTTPStatus.OK):
        data = r.json()
        if data:
            for movie in data:
                print(f"\t[{movie['movieid']}] {movie['title']}")
                movieids.append(movie['movieid'])

    # Test: Calificar películas con ratings aleatorios (0-10)
    ratings = []
    for movieid in movieids[:10]:
        ratings.append(random.randint(0, 10))
        r = requests.post(f"{CATALOG}/movies/calification", json={"movieid": movieid, "rating": ratings[-1]}, headers=headers_alice)
        ok(f"Votar película con ID [{movieid}] con rating {ratings[-1]}", r.status_code == HTTPStatus.OK)
    # Test: Verificar que las calificaciones se actualizaron en el catálogo
    r = requests.get(f"{CATALOG}/movies", headers=headers_alice)
    if ok("Obtener catálogo de películas completo", r.status_code == HTTPStatus.OK):
        data = r.json()
        if data:
            for movie in data:
                print(f"\t[{movie['movieid']}] {movie['title']} - {movie['rating']} - {movie['votes']}")
        else:
            print("\tNo hay películas en el catálogo")

    # Test: Actualizar calificaciones de películas a 0
    for movieid in movieids[:10]:
        r = requests.post(f"{CATALOG}/movies/calification", json={"movieid": movieid, "rating": 0}, headers=headers_alice)
        ok(f"Votar película con ID [{movieid}] con rating 0", r.status_code == HTTPStatus.OK)
    # Test: Calificar películas como administrador (rating 7.69)
    for movieid in movieids[:10]:
        r = requests.post(f"{CATALOG}/movies/calification", json={"movieid": movieid, "rating": 7.69}, headers=headers_admin)
        ok(f"Votar película con ID [{movieid}] con rating 7.69 como admin", r.status_code == HTTPStatus.OK)
    # Test: Verificar que las calificaciones se actualizaron después de múltiples votos
    r = requests.get(f"{CATALOG}/movies", headers=headers_alice)
    if ok("Obtener catálogo de películas completo", r.status_code == HTTPStatus.OK):
        data = r.json()
        if data:
            for movie in data:
                print(f"\t[{movie['movieid']}] {movie['title']} - {movie['rating']} - {movie['votes']}")
        else:
            print("\tNo hay películas en el catálogo")

    
    r = requests.post(f"{CATALOG}/movies/calification", json={"movieid": 99999999, "rating": random.randint(0, 10)}, headers=headers_alice)
    ok(f"Votar película con ID [99999999] no válido", r.status_code == HTTPStatus.NOT_FOUND)

    # Test: Intentar calificar con rating negativo (debe fallar con BAD_REQUEST)
    r = requests.post(f"{CATALOG}/movies/calification", json={"movieid": movieids[0], "rating": -1}, headers=headers_alice)
    ok(f"Votar película con ID [{movieids[0]}] con rating -1 no válido", r.status_code == HTTPStatus.BAD_REQUEST)

    # Test: Intentar calificar con rating mayor a 10 (debe fallar con BAD_REQUEST)
    r = requests.post(f"{CATALOG}/movies/calification", json={"movieid": movieids[0], "rating": 11}, headers=headers_alice)
    ok(f"Votar película con ID [{movieids[0]}] con rating 11 no válido", r.status_code == HTTPStatus.BAD_REQUEST)

    print("# =======================================================")
    print("# Pruebas de 'actors' (conjunto) y 'N' (top N por votos)")
    print("# =======================================================")

    # NOTA: el servidor debe convertir 'actors' CSV -> lista (split(','))
    # antes de montar la query con ANY(:actor_names::text[])

    # ---------- 1) Casos correctos ----------
    # 1.1) Conjunto de actores que SÍ co-protagonizan (Star Wars core: salen juntos en 1,2,3)
    r = requests.get(
        f"{CATALOG}/movies",
        params={"actors": "Mark Hamill,Harrison Ford,Carrie Fisher", "N": 5},
        headers=headers_alice
    )
    if ok("actors=Hamill,Ford,Fisher + N=5 (espera resultados)", r.status_code == HTTPStatus.OK):
        data = r.json()
        if data:
            for m in data:
                print(f"\t[{m['movieid']}] {m['title']} (votes={m.get('votes')}, rating={m.get('rating')})")
        else:
            print("\t<lista vacía>  << ¡OJO! Debería haber 1-3 pelis de Star Wars")

    # 1.2) Solo N -> Top N global por votos (en tu dataset todos tienen votes=0, pero debe devolver N filas)
    r = requests.get(f"{CATALOG}/movies", params={"N": 3}, headers=headers_alice)
    if ok("N=3 (top global por votos)", r.status_code == HTTPStatus.OK):
        data = r.json()
        if data:
            print(f"\tDevolvió {len(data)} película(s):")
            for m in data:
                print(f"\t[{m['movieid']}] {m['title']} (votes={m.get('votes')})")
        else:
            print("\t<lista vacía>  << inesperado para N=3")
# 
    # ---------- 2) Conjunto de actores SIN coincidencias ----------
    # (Tom Hardy solo en Venom; Keanu Reeves en Matrix: no comparten película)
    r = requests.get(
        f"{CATALOG}/movies",
        params={"actors": "Tom Hardy,Keanu Reeves", "N": 5},
        headers=headers_alice
    )
    ok("actors=Tom Hardy,Keanu Reeves (sin co-protag) => lista vacía",
       r.status_code == HTTPStatus.OK and not r.json())

    # ---------- 3) N negativo y N fuera del total ----------
    # 3.1) N negativo -> esperamos 200 (el server puede normalizar a abs/ignorar LIMIT)
    r = requests.get(f"{CATALOG}/movies", params={"N": -2}, headers=headers_alice)
    ok("N=-2 (esperamos 200; comportamiento definido por el server)", r.status_code == HTTPStatus.IM_A_TEAPOT)

    # 3.2) N enorme -> debe devolver todas las disponibles (<= N)
    r = requests.get(f"{CATALOG}/movies", params={"N": 9999}, headers=headers_alice)
    ok("N=9999 (<= total de películas)", r.status_code == HTTPStatus.OK and r.json() is not None)

    # ---------- 4) actors + parámetros extra (inválidos/ignorados) ----------
    # Se espera que la rama 'actors' ignore otros filtros
    r = requests.get(
        f"{CATALOG}/movies",
        params={"actors": "Ellen DeGeneres,Albert Brooks,Alexander Gould", "year": "2003", "foo": "bar", "N": 2},
        headers=headers_alice
    )
    if ok("actors (Finding Nemo trio) + extras ignorados + N=2", r.status_code == HTTPStatus.OK):
        data = r.json()
        if data:
            for m in data:
                print(f"\t[{m['movieid']}] {m['title']}")
        else:
            print("\t<lista vacía>  << debería salir 'Finding Nemo'")

    # ---------- 5) Combinaciones de parámetros + N ----------
    # 5.1) title + N (las Matrix)
    r = requests.get(f"{CATALOG}/movies", params={"title": "matrix", "N": 2}, headers=headers_alice)
    if ok("title='matrix' + N=2", r.status_code == HTTPStatus.OK):
        data = r.json()
        if data:
            for m in data:
                print(f"\t[{m['movieid']}] {m['title']}")
        else:
            print("\t<lista vacía>")

    # 5.2) genre + year + N (Action, 2000 -> Gladiator)
    r = requests.get(f"{CATALOG}/movies", params={"genre": "Action", "year": 2000, "N": 5}, headers=headers_alice)
    if ok("genre=Action, year=2000, N=5 (espera Gladiator)", r.status_code == HTTPStatus.OK):
        data = r.json()
        if data:
            for m in data:
                print(f"\t[{m['movieid']}] {m['title']}")
        else:
            print("\t<lista vacía>  << debería estar 'Gladiator'")

    # 5.3) actor (uno) + N  -> Tom Hardy (debe devolver 'Venom')
    r = requests.get(f"{CATALOG}/movies", params={"actor": "Tom Hardy", "N": 3}, headers=headers_alice)
    if ok("actor='Tom Hardy' + N=3 (espera 'Venom')", r.status_code == HTTPStatus.OK):
        data = r.json()
        if data:
            for m in data:
                print(f"\t[{m['movieid']}] {m['title']}")
        else:
            print("\t<lista vacía>  << debería estar 'Venom'")
    
    print("# =======================================================")
    print("# Gestión de descuentos de usuario")
    print("# =======================================================")

    discount_value = 15

    # Asignar descuento a alice como admin
    r = requests.put(f"{USERS}/user/{uid_alice}/discount", json={"discount": discount_value}, headers=headers_admin)
    ok(f"Asignar descuento del {discount_value}% a 'alice' como admin", r.status_code == HTTPStatus.OK)

    # Consultar descuento de alice con su propio token
    r = requests.get(f"{USERS}/user/{uid_alice}/discount", headers=headers_alice)
    if ok("Consultar descuento de 'alice' con su token", r.status_code == HTTPStatus.OK and r.json().get("discount") == discount_value):
        print(f"\tDescuento actual: {r.json().get('discount')}%")

        # --- Test sencillo: añadir una película al carrito y comprobar total con descuento ---
        movie_for_discount = movieids[0] if movieids else None
        if movie_for_discount is None:
            r_movies = requests.get(f"{CATALOG}/movies", headers=headers_alice)
            if ok("Recuperar catálogo para test sencillo de descuento", r_movies.status_code == HTTPStatus.OK and r_movies.json()):
                movieids = [m["movieid"] for m in r_movies.json()]
                movie_for_discount = movieids[0] if movieids else None

        if movie_for_discount is not None:
            r_movie_info = requests.get(f"{CATALOG}/movies/{movie_for_discount}", headers=headers_alice)
            if ok(f"Obtener datos de la película [{movie_for_discount}] para test de descuento",
                  r_movie_info.status_code == HTTPStatus.OK and r_movie_info.json()):
                movie_info = r_movie_info.json()
                price_base = float(movie_info["price"])
                expected_total = round(price_base * (1 - (discount_value / 100.0)), 2)

                # Vaciar carrito para garantizar que solo contiene esta película
                # Vaciar el carrito por completo antes de añadir la película del test
                while True:
                    r_cart = requests.get(f"{CATALOG}/cart", headers=headers_alice)
                    if not (r_cart.status_code == HTTPStatus.OK and r_cart.json()):
                        break
                    for movie in r_cart.json():
                        requests.delete(f"{CATALOG}/cart/{movie['movieid']}", headers=headers_alice)

                r_add_test = requests.put(f"{CATALOG}/cart/{movie_for_discount}", headers=headers_alice)
                ok(f"Añadir película [{movie_for_discount}] para test sencillo de descuento", r_add_test.status_code == HTTPStatus.OK)

                r_credit_test = requests.post(f"{CATALOG}/user/credit", json={"amount": 100}, headers=headers_alice)
                ok("Asegurar saldo antes del checkout con descuento", r_credit_test.status_code == HTTPStatus.OK)

                r_checkout_test = requests.post(f"{CATALOG}/cart/checkout", headers=headers_alice)
                if ok("Checkout sencillo aplicando descuento", r_checkout_test.status_code == HTTPStatus.OK and r_checkout_test.json()):
                    orderid_test = r_checkout_test.json().get("orderid")

                    r_order_test = requests.get(f"{CATALOG}/orders/{orderid_test}", headers=headers_alice)
                    if ok("Obtener pedido para verificar total con descuento", r_order_test.status_code == HTTPStatus.OK and r_order_test.json()):
                        content = r_order_test.json().get("movies")
                        print(f"\tContenido - {len(content)} pelicula(s)")
                        for movie in content:
                            print(f"\t- {movie['quantity']} [id: {movie['movieid']}] {movie['title']} ({movie['price']})")
                            final_stock -= movie['quantity']

                        total_paid = float(r_order_test.json().get("total"))
                        ok("Total pagado coincide con precio con descuento", round(total_paid, 2) == expected_total)
                        print(f"\tTotal esperado: {expected_total:.2f} | Total cobrado: {total_paid:.2f}")

                else:
                    print("\tNo se pudo completar el checkout del test sencillo de descuento.")
        else:
            print("\tNo se encontró ninguna película para el test sencillo de descuento.")

    # Consultar descuento de alice con token ajeno (debe fallar)
    r = requests.get(f"{USERS}/user/{uid_alice}/discount", headers=headers_admin)
    ok("Consultar descuento de 'alice' con token admin falla", r.status_code == HTTPStatus.UNAUTHORIZED)

    # Eliminar descuento de alice como admin
    r = requests.delete(f"{USERS}/user/{uid_alice}/discount", headers=headers_admin)
    ok("Eliminar descuento de 'alice' como admin", r.status_code == HTTPStatus.OK)

    # Confirmar descuento a 0
    r = requests.get(f"{USERS}/user/{uid_alice}/discount", headers=headers_alice)
    if ok("Consultar descuento de 'alice' tras eliminarlo", r.status_code == HTTPStatus.OK and r.json().get("discount") == 0):
        print(f"\tDescuento tras eliminar: {r.json().get('discount')}%")

    print("# =======================================================")
    print("# Actualización de usuario")
    print("# =======================================================")

    nuevo_nombre = "alice_mod"
    nueva_password = "secret2"
    pais_alice = "Estados Unidos"

    r = requests.put(
        f"{USERS}/user/{uid_alice}",
        json={"name": nuevo_nombre, "password": nueva_password},
        headers=headers_admin
    )
    ok("Actualizar nombre y contraseña de 'alice' como admin", r.status_code == HTTPStatus.OK)

    r = requests.get(f"{USERS}/user", json={"name": nuevo_nombre, "password": nueva_password})
    if ok("Login con credenciales actualizadas", r.status_code == HTTPStatus.OK and r.json()):
        data = r.json()
        token_alice = data["token"]
        headers_alice = {"Authorization": f"Bearer {token_alice}"}

    print("# =======================================================")
    print("# Estadística de ventas (admin)")
    print("# =======================================================")

    # Crear un pedido para usuario de otro país y comprobar que no aparece en las estadísticas de Alice
    pais_bob = "Reino Unido"
    r = requests.get(f"{USERS}/user", json={"name": "bob", "password": "secret"})
    if not (r.status_code == HTTPStatus.OK and r.json()):
        r_create_bob = requests.put(
            f"{USERS}/user",
            json={"name": "bob", "password": "secret", "nationality": pais_bob},
            headers=headers_admin,
        )
        ok("Crear usuario 'bob' para test de estadística", r_create_bob.status_code == HTTPStatus.OK and r_create_bob.json())
        r = requests.get(f"{USERS}/user", json={"name": "bob", "password": "secret"})

    if ok("Login usuario 'bob'", r.status_code == HTTPStatus.OK and r.json()):
        data = r.json()
        uid_bob = data["uid"]
        token_bob = data["token"]
        headers_bob = {"Authorization": f"Bearer {token_bob}"}

        # Asegurar que hay una película que comprar
        if not movieids:
            r_movies = requests.get(f"{CATALOG}/movies", headers=headers_bob)
            if ok("Obtener catálogo para bob", r_movies.status_code == HTTPStatus.OK and r_movies.json()):
                movieids = [m["movieid"] for m in r_movies.json()]

        if movieids:
            movie_to_buy = movieids[0]
            requests.post(f"{CATALOG}/user/credit", json={"amount": 100}, headers=headers_bob)
            requests.put(f"{CATALOG}/cart/{movie_to_buy}", headers=headers_bob)
            r_checkout = requests.post(f"{CATALOG}/cart/checkout", headers=headers_bob)
            if ok("Checkout de bob", r_checkout.status_code == HTTPStatus.OK):
                orderid = r_checkout.json().get("orderid")
                r_order = requests.get(f"{CATALOG}/orders/{orderid}", headers=headers_bob)
                if ok("Obtener pedido", r_order.status_code == HTTPStatus.OK and r_order.json()):
                    content = r_order.json().get("movies")
                    print(f"\tContenido - {len(content)} pelicula(s)")
                    for movie in content:
                        print(f"\t- {movie['quantity']} [id: {movie['movieid']}] {movie['title']} ({movie['price']})")
                        final_stock -= movie['quantity']

    year_param = datetime.now().year
    country_param = pais_alice
    r = requests.get(f"{CATALOG}/estadisticaVentas/{year_param}/{country_param}", headers=headers_admin)
    ok("Consultar estadística de ventas por año y país", r.status_code in (HTTPStatus.OK, HTTPStatus.NOT_FOUND))
    if r.status_code == HTTPStatus.OK:
        orders = r.json()
        print(f"\tDevolvió {len(orders)} pedido(s) para {country_param} en {year_param}")
        for order in orders:
            print(f"\t- Pedido {order['order_id']} de usuario {order['user_name']} por {order['total']} en fecha {order['date']}")

    print("# =======================================================")
    print("# Clientes sin pedidos")
    print("# =======================================================")

    r = requests.get(f"{CATALOG}/clientesSinPedidos", headers=headers_admin)
    ok("Consultar clientes sin pedidos", r.status_code == HTTPStatus.OK)
    if r.status_code == HTTPStatus.OK:
        clientes = r.json()
        print(f"\tDevolvió {len(clientes)} cliente(s) sin pedidos")
        for cliente in clientes:
            print(f"\t- Cliente {cliente['user_id']},  {cliente['name']}, {cliente['balance']}")

    r = requests.get(f"{CATALOG}/clientesSinPedidos", headers=headers_alice)
    ok("Consultar clientes sin pedidos con token de usuario no administrador", r.status_code == HTTPStatus.UNAUTHORIZED)

    print("# =======================================================")
    print("# Comprobaciones del precio del carrito ")
    print("# =======================================================")

    r = requests.get(f"{CATALOG}/cart", headers=headers_alice)
    if ok("Obtener carrito", r.status_code == HTTPStatus.OK):
        data = r.json()
        if data:
            for movie in data:
                print(f"\t{movie['quantity']} [id: {movie['movieid']}] {movie['title']} - {movie['price']}")
        else:
            print(f"\tEl carrito está vacío. Carrito: {data}")
    else: print(r)

    r = requests.put(f"{CATALOG}/cart/1", json={"quantity": 2}, headers=headers_alice)
    ok(f"Añadir película [1] para test sencillo de descuento", r.status_code == HTTPStatus.OK)
    r = requests.put(f"{CATALOG}/cart/1", headers=headers_alice)
    ok(f"Añadir película [1] para test sencillo de descuento", r.status_code == HTTPStatus.OK)
    r = requests.put(f"{CATALOG}/cart/3", headers=headers_alice)
    ok(f"Añadir película [3] para test sencillo de descuento", r.status_code == HTTPStatus.OK)

    total = 0
    r = requests.get(f"{CATALOG}/cart", headers=headers_alice)
    if ok("Obtener carrito", r.status_code == HTTPStatus.OK and r.json()):
        data = r.json()
        if data:
            for movie in data:
                price_int = float(movie['price'])
                print(f"\t[{movie['movieid']}] {movie['title']} - {price_int}")
                total += price_int * movie.get('quantity', 1)
            print(f"\tTotal: {total}")
        else:
            print("\tEl carrito está vacío.")

    r = requests.get(f"{CATALOG}/cart/total", headers=headers_alice)
    if ok("Obtener total del carrito", r.status_code == HTTPStatus.OK and r.json()['total'] == total):
        data = r.json()
        print(f"\t✓ Total del carrito: {data['total']}")

    r = requests.delete(f"{CATALOG}/cart/1", headers=headers_alice)
    ok(f"Eliminar película [1] del carrito", r.status_code == HTTPStatus.OK)

    total = 0
    r = requests.get(f"{CATALOG}/cart", headers=headers_alice)
    if ok("Obtener carrito", r.status_code == HTTPStatus.OK and r.json()):
        data = r.json()
        if data:
            for movie in data:
                price_int = float(movie['price'])
                total += price_int * movie.get('quantity', 1)
    
    r = requests.get(f"{CATALOG}/cart/total", headers=headers_alice)
    if ok("Obtener total del carrito", r.status_code == HTTPStatus.OK and r.json()['total'] == total):
        data = r.json()
        print(f"\t✓ Total del carrito: {data['total']}")

    r = requests.delete(f"{CATALOG}/cart/1", headers=headers_alice)
    ok(f"Eliminar película [1] del carrito", r.status_code == HTTPStatus.OK)

    total = 0
    r = requests.get(f"{CATALOG}/cart", headers=headers_alice)
    if ok("Obtener carrito", r.status_code == HTTPStatus.OK and r.json()):
        data = r.json()
        if data:
            for movie in data:
                price_int = float(movie['price'])
                total += price_int * movie.get('quantity', 1)
    
    r = requests.get(f"{CATALOG}/cart/total", headers=headers_alice)
    if ok("Obtener total del carrito", r.status_code == HTTPStatus.OK and r.json()['total'] == total):
        data = r.json()
        print(f"\t✓ Total del carrito: {data['total']}")

    r = requests.delete(f"{CATALOG}/cart/3", headers=headers_alice)
    ok(f"Eliminar película [3] del carrito", r.status_code == HTTPStatus.OK)

    r = requests.delete(f"{CATALOG}/cart/1", headers=headers_alice)
    ok(f"Eliminar película [1] del carrito", r.status_code == HTTPStatus.OK)

    total = 0
    r = requests.get(f"{CATALOG}/cart", headers=headers_alice)
    if ok("Obtener carrito", r.status_code == HTTPStatus.OK):
        data = r.json()
        print(f"\tEl carrito está vacío. Carrito: {data}")
    
    r = requests.get(f"{CATALOG}/cart/total", headers=headers_alice)
    if ok("Obtener total del carrito", r.status_code == HTTPStatus.OK and r.json()['total'] == total):
        data = r.json()
        print(f"\t✓ Total del carrito: {data['total']}")

    print("# =======================================================")
    print("# Comprobar total de stock correcto")
    print("# =======================================================")

    total_stock = 0
    r = requests.get(f"{CATALOG}/movies", headers=headers_admin)
    if ok("Obtener catálogo de películas", r.status_code == HTTPStatus.OK and r.json()):
        data = r.json()
        if data:
            for movie in data: total_stock += movie['stock']
            if not ok(f"Total de stock coincide con el catálogo: {final_stock} ?= {total_stock}", total_stock == final_stock):
                print(f"\tTotal de stock: {total_stock} != {final_stock}")

    print("# =======================================================")
    print("# Limpiar base de datos")
    print("# =======================================================")
    
    # Test: Borrar usuario 'alice' con token de administrador
    r = requests.delete(f"{USERS}/user/{uid_alice}", headers=headers_admin)
    ok("Borrar usuario alice", r.status_code == HTTPStatus.OK)

    # Test: Intentar borrar un usuario que ya no existe (debe fallar con NOT_FOUND)
    r = requests.delete(f"{USERS}/user/{uid_alice}", headers=headers_admin)
    ok("Borrar usuario inexistente", r.status_code == HTTPStatus.NOT_FOUND)

    # Test: Borrar usuario 'bob' con token de administrador
    r = requests.delete(f"{USERS}/user/{uid_bob}", headers=headers_admin)
    ok("Borrar usuario bob", r.status_code == HTTPStatus.OK)

    # Test: Intentar borrar un usuario que ya no existe (bob)
    r = requests.delete(f"{USERS}/user/{uid_bob}", headers=headers_admin)
    ok("Borrar usuario bob inexistente", r.status_code == HTTPStatus.NOT_FOUND)

    print("\nPruebas completadas.")

if __name__ == "__main__":
    main()
