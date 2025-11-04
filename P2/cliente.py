from math import e
import requests
from http import HTTPStatus

USERS = "http://127.0.0.1:5050"
CATALOG = "http://127.0.0.1:5051"

def ok(name, cond):
    status = "OK" if cond else "FAIL"
    print(f"[{status}] {name}")
    return cond

def main():

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
    r = requests.put(f"{USERS}/user", json={"name": "alice", "password": "secret"}, headers=headers_admin)
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
    r = requests.put(f"{USERS}/user", json={"name": "aleatorio", "password": "aleatorio"}, headers=headers_alice)
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
                        print(f"\t[{movie['movieid']}] {movie['title']} - {movie['price']}")
            
    # Añadir película al carrito más de una vez
    if movieids:
        r = requests.put(f"{CATALOG}/cart/{movieids[0]}", headers=headers_alice)
        ok(f"Añadir película con ID [{movieids[0]}] al carrito más de una vez", r.status_code == HTTPStatus.CONFLICT)

        # Eliminar película del carrito
        r = requests.delete(f"{CATALOG}/cart/{movieids[-1]}", headers=headers_alice)
        if ok(f"Elimimar película con ID [{movieids[-1]}] del carrito", r.status_code == HTTPStatus.OK):
            r = requests.get(f"{CATALOG}/cart", headers=headers_alice)
            if ok(f"Obtener carrito del usuario sin la película [{movieids[-1]}]", r.status_code == HTTPStatus.OK):
                data = r.json()
                if data:
                    for movie in data:
                        print(f"\t[{movie['movieid']}] {movie['title']} - {movie['price']}")
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
            print("\tContenidos:")
            for movie in order['movies']:
                    print(f"\t- [{movie['movieid']}] {movie['title']} ({movie['price']})")
        

        # Test: Verificar que el carrito está vacío después del checkout
        r = requests.get(f"{CATALOG}/cart", headers=headers_alice)
        ok("Obtener carrito vacío después de la venta", r.status_code == HTTPStatus.OK and not r.json())

    
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
    for movieid in movieids[:10]:
        r = requests.post(f"{CATALOG}/movies/calification", json={"movieid": movieid, "rating": random.randint(0, 10)}, headers=headers_alice)
        ok(f"Votar película con ID [{movieid}]", r.status_code == HTTPStatus.OK)
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
    print("# Limpiar base de datos")
    print("# =======================================================")
    
    # Test: Borrar usuario 'alice' con token de administrador
    r = requests.delete(f"{USERS}/user/{uid_alice}", headers=headers_admin)
    ok("Borrar usuario alice", r.status_code == HTTPStatus.OK)

    # Test: Intentar borrar un usuario que ya no existe (debe fallar con NOT_FOUND)
    r = requests.delete(f"{USERS}/user/{uid_alice}", headers=headers_admin)
    ok("Borrar usuario inexistente", r.status_code == HTTPStatus.NOT_FOUND)

    print("\nPruebas completadas.")

if __name__ == "__main__":
    main()
