-- =============================================================================
-- deadlock_setup.sql - Script de preparación para prueba de deadlock
-- =============================================================================
-- 
-- Este script prepara los datos necesarios para probar deadlocks entre
-- el trigger update_paid y una transacción externa.
-- Ejecutar este script ANTES de ejecutar deadlock_cliente1.sql y 
-- deadlock_cliente2.sql en terminales diferentes.
--
-- =============================================================================

-- Limpiar datos anteriores si existen
DELETE FROM Pedido WHERE order_id = 1;
DELETE FROM Carrito_Pelicula WHERE cart_id = 1;
DELETE FROM Carrito WHERE cart_id = 1;
DELETE FROM Usuario WHERE user_id = '1';

-- Crear usuario de prueba (ID simple: '1')
INSERT INTO Usuario (user_id, name, password, token, nationality, admin, balance) VALUES
('1', 'test', 'pass', 'token', 'España', FALSE, 1000.00);

-- Crear carrito (ID simple: 1)
INSERT INTO Carrito (cart_id, user_id) VALUES
(1, '1');

-- Crear pedido (ID simple: 1, debe coincidir con cart_id)
INSERT INTO Pedido(order_id, user_id, total, date, paid) VALUES
(1, '1', 100.00, '2025-11-27', FALSE);

-- Añadir primera película al carrito (usa movieid=1 que ya existe en populate.sql)
INSERT INTO Carrito_Pelicula (cart_id, movieid, quantity) VALUES
(1, 1, 1)
ON CONFLICT (cart_id, movieid) DO NOTHING;

-- Verificar datos creados
SELECT '✓ Datos preparados' AS status;
SELECT user_id, name, balance FROM Usuario WHERE user_id = '1';
SELECT order_id, user_id, total, paid FROM Pedido WHERE order_id = 1;
SELECT cart_id, movieid, quantity FROM Carrito_Pelicula WHERE cart_id = 1;