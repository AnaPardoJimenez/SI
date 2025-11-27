-- =============================================================================
-- deadlock_cliente1.sql - Cliente 1 para interbloqueo con trigger update_paid
-- =============================================================================
-- 
-- INSTRUCCIONES:
-- 1. Ejecutar primero: deadlock_setup.sql
-- 2. Ejecutar este archivo en la TERMINAL 1
-- 3. Inmediatamente después (en menos de 2 segundos), ejecutar 
--    deadlock_cliente2.sql en la TERMINAL 2
-- 
-- INTERBLOQUEO:
--   Este script dispara el trigger update_paid() que:
--     - UPDATE Usuario (línea 30 de actualiza.sql) - adquiere lock en Usuario
--     - Espera 5 segundos (pg_sleep en línea 34)
--     - DELETE Carrito_Pelicula (línea 37 de actualiza.sql) - intenta lock en Carrito_Pelicula
--   
--   Cliente 2:
--     - DELETE Carrito_Pelicula - adquiere lock en Carrito_Pelicula
--     - Espera 5 segundos
--     - UPDATE Usuario - intenta lock en Usuario (que el trigger ya tiene)
--   
--   Resultado: Interbloqueo detectado por PostgreSQL
-- =============================================================================

BEGIN;

SELECT 'Cliente 1: Iniciando transacción...' AS status;
SELECT 'Cliente 1: Disparando trigger update_paid al actualizar paid=TRUE' AS status;

-- Disparar el trigger update_paid que ejecutará:
-- 1. UPDATE Usuario (línea 30) - adquiere lock
-- 2. pg_sleep(5) (línea 34) - espera
-- 3. DELETE Carrito_Pelicula (línea 37) - intenta lock (BLOQUEADO por Cliente 2)
UPDATE Pedido
SET paid = TRUE
WHERE order_id = 1;

-- Si llegamos aquí, no hubo deadlock (poco probable si Cliente 2 está ejecutándose)
SELECT 'Cliente 1: Operación completada exitosamente' AS status;

COMMIT;

SELECT 'Cliente 1: Transacción completada' AS status;