-- =============================================================================
-- deadlock_cliente2.sql - Cliente 2 para interbloqueo con trigger update_paid
-- =============================================================================
-- 
-- INSTRUCCIONES:
-- 1. Ejecutar primero: deadlock_setup.sql
-- 2. Ejecutar deadlock_cliente1.sql en la TERMINAL 1
-- 3. Inmediatamente después (en menos de 2 segundos), ejecutar 
--    este archivo en la TERMINAL 2
-- 
-- INTERBLOQUEO:
--   Cliente 1 (trigger update_paid):
--     - UPDATE Usuario (línea 30 de actualiza.sql) - adquiere lock en Usuario
--     - Espera 5 segundos
--     - DELETE Carrito_Pelicula (línea 37 de actualiza.sql) - intenta lock en Carrito_Pelicula
--   
--   Cliente 2 (este script):
--     - DELETE Carrito_Pelicula - adquiere lock en Carrito_Pelicula
--     - Espera 5 segundos
--     - UPDATE Usuario - intenta lock en Usuario (que Cliente 1 ya tiene)
--   
--   Resultado: Interbloqueo detectado por PostgreSQL
-- =============================================================================

BEGIN;

SELECT 'Cliente 2: Iniciando transacción...' AS status;

-- Paso 1: Adquirir lock en Carrito_Pelicula (este lock bloqueará al trigger)
-- Usamos el mismo cart_id que el trigger intentará eliminar
DELETE FROM Carrito_Pelicula
WHERE cart_id = 1;

SELECT 'Cliente 2: Lock adquirido en Carrito_Pelicula (cart_id=1)' AS status;
SELECT 'Cliente 2: Esperando 5 segundos para que el trigger adquiera su lock...' AS status;

-- Paso 2: Esperar para dar tiempo a que el trigger adquiera su lock en Usuario
SELECT pg_sleep(5);

-- Paso 3: Intentar adquirir lock en Usuario (BLOQUEADO - el trigger lo tiene)
-- Esto causará el interbloqueo si el trigger también intenta acceder a Carrito_Pelicula
SELECT 'Cliente 2: Intentando adquirir lock en Usuario (user_id=1)...' AS status;
SELECT 'Cliente 2: ESPERANDO (el trigger tiene el lock)...' AS status;
UPDATE Usuario
SET balance = balance + 100
WHERE user_id = '1';

-- Si llegamos aquí, no hubo deadlock (poco probable si el trigger está ejecutándose)
SELECT 'Cliente 2: Operación completada exitosamente' AS status;

COMMIT;

SELECT 'Cliente 2: Transacción completada' AS status;