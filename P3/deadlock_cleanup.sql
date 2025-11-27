-- =============================================================================
-- deadlock_cleanup.sql - Script de limpieza para pruebas de deadlock
-- =============================================================================
-- 
-- Este script elimina todos los datos creados por deadlock_setup.sql
-- para dejar la base de datos en su estado original.
--
-- =============================================================================

-- Eliminar en orden inverso a las dependencias (evitar errores de foreign key)

-- Eliminar elementos del carrito
DELETE FROM Carrito_Pelicula WHERE cart_id = 1;

-- Eliminar carrito
DELETE FROM Carrito WHERE cart_id = 1;

-- Eliminar pedido
DELETE FROM Pedido WHERE order_id = 1;

-- Eliminar usuario
DELETE FROM Usuario WHERE user_id = '1';

SELECT '✓ Limpieza completada' AS status;