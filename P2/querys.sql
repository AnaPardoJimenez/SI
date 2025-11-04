-- =============================================================================
-- querys.sql - Consultas SQL de Ejemplo y Referencia
-- =============================================================================
--
-- ADVERTENCIA: Este archivo contiene consultas DESACTUALIZADAS que hacen referencia
-- a tablas y columnas que ya no existen en el esquema actual.
--
-- El esquema actual utiliza:
--   - Carrito_Pelicula (no "Pertenece")
--   - cart_id (no "order_id" en Carrito)
--   - movieid (no "movie_id")
--   - title (no "name" en Peliculas)
--
-- Este archivo se mantiene como referencia histórica, pero las consultas
-- deben actualizarse antes de ejecutarse.
--
-- Autor: Juan Larrondo Fernández de Córdoba y Ana Pardo Jiménez
-- Fecha de creación: 28-10-2025
-- Última modificación: 28-10-2025
-- Estado: DESACTUALIZADO - Requiere actualización
--
-- =============================================================================

-- NOTA: Las siguientes consultas están DESACTUALIZADAS y NO funcionarán
-- con el esquema actual. Se mantienen solo como referencia histórica.
--
-- Para versiones actualizadas, ver los ejemplos al final del archivo.

-- =============================================================================
-- CONSULTAS DESACTUALIZADAS (NO USAR - Solo referencia histórica)
-- =============================================================================

-- Eliminar elementos de carrito (tabla Pertenece - YA NO EXISTE):
-- delete from Pertenece where order_id = 1 and movie_id = 1;

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

-- =============================================================================
-- FLUJO COMPLETO DESACTUALIZADO (NO USAR - Solo referencia histórica)
-- =============================================================================
--
-- NOTA: Este flujo usa tablas y columnas que ya no existen:
--   - "Pertenece" -> ahora es "Carrito_Pelicula"
--   - "order_id" en Carrito -> ahora es "cart_id"
--   - "movie_id" -> ahora es "movieid"
--   - "peliculas.name" -> ahora es "peliculas.title"

-- 1. Crear un carrito para el usuario admin (si no existe):
-- INSERT INTO Carrito (user_id)
-- SELECT '123e4567-e89b-12d3-a456-426614174000'
-- WHERE NOT EXISTS (SELECT 1 FROM Carrito WHERE user_id = '123e4567-e89b-12d3-a456-426614174000');

-- 2. Añadir varias películas al carrito del admin (usando IDs de películas existentes):
-- Añadir Star Wars Episode IV, Harry Potter 1, y The Matrix
-- INSERT INTO Pertenece (order_id, movie_id)  -- DESACTUALIZADO
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