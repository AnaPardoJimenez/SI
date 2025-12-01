-- =======================================================================
-- Archivo: transactions.sql
-- Descripción: Esqueleto y ejemplos de transacciones SQL
-- para operaciones frecuentes (insertar, actualizar, borrar)
-- en el contexto de una base de datos (por ejemplo, catálogo de películas).
-- Instrucciones:
-- - Reemplace los valores y nombres de tabla/campo según su esquema real.
-- - Cada transacción se ejecuta como una unidad atómica.
-- =======================================================================

-- =======================================================================
-- Ejemplo 1: Transacción para borrar pais correctamente
-- =======================================================================
CREATE OR REPLACE PROCEDURE borrar_pais_transaccion(nombre_pais VARCHAR)
AS $$
    DECLARE
        existe_user BOOLEAN;
    BEGIN
    
    SELECT 1
        FROM usuario u
        WHERE nationality = nombre_pais
        LIMIT 1
    INTO existe_user;

    IF existe_user = FALSE THEN
        RAISE EXCEPTION 'No existen usuarios del país %.', nombre_pais;
        ROLLBACK;
    END IF;

    

    COMMIT;
EXCEPTION
    WHEN OTHERS THEN
        ROLLBACK;
        RAISE;
END
$$ LANGUAGE plpgsql;

BEGIN TRANSACTION;



COMMIT;


-- =======================================================================
-- Ejemplo 2: Transacción para borrar pais incorrectamente
-- =======================================================================
BEGIN TRANSACTION;



COMMIT;


-- =======================================================================
-- Ejemplo 3: Transacción para borrar pais desordenado
-- =======================================================================
BEGIN TRANSACTION;



COMMIT;

-- =======================================================================
-- FIN DEL ESQUELETO DE TRANSACCIONES SQL
-- =======================================================================
