Eliminar elementos de carrito (tabla Pertenece):
delete from Pertenece where order_id = 1 and movie_id = 1;

Actualizar saldo de usuario (tabla Usuario):
update Usuario set balance = 123456 where user_id = '123e4567-e89b-12d3-a456-426614174000';


select carrito.order_id, pertenece.movie_id, name, description, year, genre, price from carrito
    join Pertenece on Carrito.order_id = Pertenece.order_id
    join Peliculas on Pertenece.movie_id = Peliculas.movie_id
    where Carrito.user_id = '123e4567-e89b-12d3-a456-426614174000';

-- Eliminar primero de Pertenece (usando JOIN correctamente en PostgreSQL):
delete from Pertenece using Carrito where Pertenece.order_id = Carrito.order_id and Carrito.user_id = '123e4567-e89b-12d3-a456-426614174000';

-- Luego eliminar de Carrito (el orden importa por la foreign key):
delete from Carrito where user_id = '123e4567-e89b-12d3-a456-426614174000';

-- ============================================================================
-- FLUJO COMPLETO: Usar admin, añadir películas al carrito, mostrar y eliminar
-- ============================================================================

-- 1. Crear un carrito para el usuario admin (si no existe):
INSERT INTO Carrito (user_id)
SELECT '123e4567-e89b-12d3-a456-426614174000'
WHERE NOT EXISTS (SELECT 1 FROM Carrito WHERE user_id = '123e4567-e89b-12d3-a456-426614174000');

-- 2. Añadir varias películas al carrito del admin (usando IDs de películas existentes):
-- Añadir Star Wars Episode IV, Harry Potter 1, y The Matrix
INSERT INTO Pertenece (order_id, movie_id)
SELECT c.order_id, 1  -- Star Wars: Episode IV - A New Hope
FROM Carrito c
WHERE c.user_id = '123e4567-e89b-12d3-a456-426614174000'
ON CONFLICT DO NOTHING;

INSERT INTO Pertenece (order_id, movie_id)
SELECT c.order_id, 7  -- Harry Potter and the Philosopher's Stone
FROM Carrito c
WHERE c.user_id = '123e4567-e89b-12d3-a456-426614174000'
ON CONFLICT DO NOTHING;

INSERT INTO Pertenece (order_id, movie_id)
SELECT c.order_id, 31  -- The Matrix
FROM Carrito c
WHERE c.user_id = '123e4567-e89b-12d3-a456-426614174000'
ON CONFLICT DO NOTHING;

INSERT INTO Pertenece (order_id, movie_id)
SELECT c.order_id, 24  -- Spirited Away
FROM Carrito c
WHERE c.user_id = '123e4567-e89b-12d3-a456-426614174000'
ON CONFLICT DO NOTHING;

INSERT INTO Pertenece (order_id, movie_id)
SELECT c.order_id, 29  -- Your Name
FROM Carrito c
WHERE c.user_id = '123e4567-e89b-12d3-a456-426614174000'
ON CONFLICT DO NOTHING;

-- 3. Mostrar el carrito del admin (con todos los detalles de las películas):
SELECT 
    carrito.order_id, 
    pertenece.movie_id, 
    peliculas.name, 
    peliculas.description, 
    peliculas.year, 
    peliculas.genre, 
    peliculas.price
FROM carrito
JOIN Pertenece ON Carrito.order_id = Pertenece.order_id
JOIN Peliculas ON Pertenece.movie_id = Peliculas.movie_id
WHERE Carrito.user_id = '123e4567-e89b-12d3-a456-426614174000';

-- 4. Eliminar varias películas del carrito (por ejemplo, eliminar movie_id 1 y 31):
DELETE FROM Pertenece 
WHERE order_id = (
    SELECT order_id FROM Carrito WHERE user_id = '123e4567-e89b-12d3-a456-426614174000'
) 
AND movie_id IN (1, 31);  -- Eliminar Star Wars Episode IV y The Matrix

-- 5. Mostrar el carrito del admin de nuevo (debería tener menos películas):
SELECT 
    carrito.order_id, 
    pertenece.movie_id, 
    peliculas.name, 
    peliculas.description, 
    peliculas.year, 
    peliculas.genre, 
    peliculas.price
FROM carrito
JOIN Pertenece ON Carrito.order_id = Pertenece.order_id
JOIN Peliculas ON Pertenece.movie_id = Peliculas.movie_id
WHERE Carrito.user_id = '123e4567-e89b-12d3-a456-426614174000';