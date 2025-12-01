-- ============================================================================
-- ARCHIVO: actualiza.sql
-- DESCRIPCIÓN: Contiene funciones y triggers de PostgreSQL para mantener
--              la integridad y consistencia de los datos en el sistema de
--              gestión de películas. Incluye:
--              - Actualización automática de stock de películas
--              - Procesamiento de pagos y gestión de carritos
--              - Cálculo y actualización de ratings de películas
-- ============================================================================

-- ============================================================================
-- FUNCIÓN: update_stock()
-- DESCRIPCIÓN: Devuelve el ID de la película a la que se refiere el carrito.
-- LÓGICA: Actualiza el stock de la película según la cantidad de películas que se han eliminado del carrito.
-- ============================================================================
CREATE FUNCTION update_stock()
RETURNS TRIGGER AS $$
DECLARE
    pedido_count INT;
BEGIN
    -- Verificar si existe un pedido con este cart_id
    SELECT COUNT(*) INTO pedido_count
    FROM pedido p
    WHERE p.order_id = OLD.cart_id;
    
    -- Solo proceder si no hay pedido asociado
    IF pedido_count = 0 THEN
        -- DELETE, devolver el stock completo
        IF TG_OP = 'DELETE' THEN
            UPDATE Peliculas
            SET stock = stock + OLD.quantity
            WHERE movieid = OLD.movieid;
            RETURN OLD;
        
        -- UPDATE, ajustar según la diferencia
        ELSIF TG_OP = 'UPDATE' THEN
            UPDATE Peliculas
            SET stock = stock + (OLD.quantity - NEW.quantity)
            WHERE movieid = OLD.movieid;
            RETURN NEW;
        
        -- INSERT, reducir el stock completo
        ELSIF TG_OP = 'INSERT' THEN
            UPDATE Peliculas
            SET stock = stock - NEW.quantity
            WHERE movieid = NEW.movieid;
            RETURN NEW;
        END IF;
    END IF;
    
    -- Si hay pedido o no es DELETE/UPDATE/INSERT, retornar el registro apropiado
    IF TG_OP = 'DELETE' THEN
        RETURN OLD;
    ELSE
        RETURN NEW;
    END IF;
END;
$$ LANGUAGE plpgsql;

-- TRIGGER: update_stock_id_trigger
-- Se ejecuta después de DELETE o UPDATE OF quantity en la tabla carrito_pelicula
-- Solo se activa cuando no hay pedido con el cart_id de la película que se ha eliminado del carrito
CREATE TRIGGER update_stock_trigger
AFTER DELETE OR UPDATE OF quantity OR INSERT ON carrito_pelicula
FOR EACH ROW
EXECUTE FUNCTION update_stock();



-- ============================================================================
-- FUNCIÓN: update_paid()
-- DESCRIPCIÓN: Procesa el pago de un pedido cuando se marca como pagado.
--              Realiza las siguientes acciones:
--              1. Resta el total del pedido del balance del usuario
--              2. Vacía el carrito del usuario (elimina Carrito_Pelicula y Carrito)
--              3. Crea un nuevo carrito vacío para el usuario
-- NOTA: La línea PERFORM pg_sleep(5) está comentada, pero podría usarse
--       para simular condiciones de concurrencia en pruebas.
-- ============================================================================
CREATE FUNCTION update_paid()
RETURNS TRIGGER AS $$
BEGIN
    -- Restar el total del pedido del balance del usuario
    UPDATE Usuario
    SET balance = balance - NEW.total
    WHERE user_id = NEW.user_id;

    --PERFORM pg_sleep(5);

    -- Vaciar el carrito del usuario (eliminar Carrito_Pelicula y Carrito)
    DELETE FROM Carrito_Pelicula
    WHERE cart_id = NEW.order_id;

    DELETE FROM Carrito
    WHERE user_id = NEW.user_id;

    INSERT INTO Carrito (user_id)
    VALUES (NEW.user_id);

    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

-- TRIGGER: update_paid_trigger
-- Se ejecuta después de actualizar el campo 'paid' en la tabla pedido
-- Solo se activa cuando paid = TRUE (pedido marcado como pagado)
CREATE TRIGGER update_paid_trigger
AFTER UPDATE OF paid ON pedido
FOR EACH ROW
WHEN (NEW.paid = TRUE)
EXECUTE FUNCTION update_paid();



-- ============================================================================
-- FUNCIÓN: insert_rating()
-- DESCRIPCIÓN: Actualiza el rating promedio de una película cuando se inserta
--              una nueva calificación.
-- LÓGICA: Calcula el nuevo promedio usando la fórmula:
--         rating = (rating_anterior * (votes-1) + nueva_calificacion) / votes
--         Esto evita recalcular todos los ratings desde cero.
-- ============================================================================
CREATE FUNCTION insert_rating()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE Peliculas
    SET rating = (rating * (votes-1) + NEW.rating) / votes
    WHERE movieid = NEW.movieid;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- TRIGGER: insert_rating_trigger
-- Se ejecuta después de INSERT en la tabla calificacion
-- Actualiza automáticamente el rating de la película calificada
CREATE TRIGGER insert_rating_trigger
AFTER INSERT ON calificacion
FOR EACH ROW
EXECUTE FUNCTION insert_rating();



-- ============================================================================
-- FUNCIÓN: update_rating()
-- DESCRIPCIÓN: Actualiza el rating promedio de una película cuando se modifica
--              una calificación existente.
-- LÓGICA: Recalcula el rating promedio llamando a la función media_rating()
--         para obtener el promedio actualizado de todas las calificaciones.
-- ============================================================================
CREATE FUNCTION update_rating()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE Peliculas
    SET rating = media_rating(NEW.movieid)
    WHERE OLD.movieid = NEW.movieid;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- TRIGGER: update_rating_trigger
-- Se ejecuta después de UPDATE en la tabla calificacion
-- Recalcula el rating promedio de la película cuando se modifica una calificación
CREATE TRIGGER update_rating_trigger
AFTER UPDATE ON calificacion
FOR EACH ROW
EXECUTE FUNCTION update_rating();


-- ============================================================================
-- FUNCIÓN: media_rating(p_movieid INT)
-- DESCRIPCIÓN: Calcula el promedio de todas las calificaciones de una película.
-- PARÁMETROS:
--   - p_movieid: ID de la película para la cual calcular el promedio
-- RETORNA: DECIMAL(10,2) - El rating promedio, o 0.00 si no hay calificaciones
-- ============================================================================
CREATE FUNCTION media_rating(p_movieid INT)
RETURNS DECIMAL(10,2) AS
$$
DECLARE
    rating DECIMAL(10,2);
BEGIN
    SELECT AVG(c.rating) INTO rating
    FROM Calificacion c
    WHERE c.movieid = p_movieid;

    IF rating IS NULL THEN
        RETURN 0.00;
    END IF;

    RETURN rating;
END;
$$
LANGUAGE plpgsql;


-- ============================================================================
-- PROCEDIMIENTO: actualizar_rating_pelicula(p_movieid INT)
-- DESCRIPCIÓN: Procedimiento manual para recalcular el rating promedio de una
--              película concreta sin depender del trigger. Calcula el promedio
--              de todas las calificaciones registradas y actualiza el campo
--              rating en la tabla Peliculas.
-- PARÁMETROS:
--   - p_movieid: ID de la película cuyo rating debe recalcularse
-- ============================================================================
CREATE OR REPLACE PROCEDURE actualizar_rating_pelicula(p_movieid INT)
AS $$
DECLARE
    nuevo_rating DECIMAL(10,2);
BEGIN
    SELECT AVG(c.rating) INTO nuevo_rating
    FROM Calificacion c
    WHERE c.movieid = p_movieid;

    IF nuevo_rating IS NULL THEN
        nuevo_rating := 0.00;
    END IF;

    UPDATE Peliculas
    SET rating = nuevo_rating
    WHERE movieid = p_movieid;
END;
$$ 
LANGUAGE plpgsql;

-- ====================================================================================
-- FUNCIÓN: update_total_cart()
-- DESCRIPCIÓN: Actualiza el total del carrito según el contenido de la tabla carrito_pelicula.
-- PARÁMETROS:
--   - NEW: Registro recién insertado o modificado en la tabla carrito_pelicula
-- RETORNA: Decimal(10,2) - El total del carrito
-- ============================================================================
CREATE FUNCTION update_total_cart()
RETURNS TRIGGER AS $$
BEGIN

    IF TG_OP = 'UPDATE' OR TG_OP = 'INSERT' THEN
        UPDATE Carrito
        SET total = (SELECT SUM(p.price * cp.quantity)
                        FROM Carrito_Pelicula cp
                        JOIN Peliculas p ON cp.movieid = p.movieid
                        WHERE cp.cart_id = NEW.cart_id)
        -- SET total = total + (SELECT p.price * (NEW.quantity - OLD.quantity)
        --                         FROM Peliculas p
        --                         WHERE p.movieid = NEW.movieid)
        WHERE cart_id = NEW.cart_id;

    ELSIF TG_OP = 'DELETE' THEN
        UPDATE Carrito
        SET total = total - (SELECT p.price * OLD.quantity
                                FROM Peliculas p
                                WHERE p.movieid = OLD.movieid)
        WHERE cart_id = OLD.cart_id;
        RETURN OLD;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- TRIGGER: update_total_cart_trigger
-- Se ejecuta después de INSERT o UPDATE en la tabla carrito_pelicula
-- Actualiza el total del carrito según el contenido de la tabla carrito_pelicula
CREATE TRIGGER update_total_cart_trigger
AFTER INSERT OR UPDATE OR DELETE ON carrito_pelicula
FOR EACH ROW
EXECUTE FUNCTION update_total_cart();


-- ====================================================================================
-- FUNCIÓN: update_total_cart()
-- DESCRIPCIÓN: Actualiza el total del carrito según el contenido de la tabla carrito_pelicula.
-- PARÁMETROS:
--   - NEW: Registro recién insertado o modificado en la tabla carrito_pelicula
-- RETORNA: Decimal(10,2) - El total del carrito
-- ============================================================================
CREATE FUNCTION update_total_cart_onDelete()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE Carrito
    SET total = total - (SELECT p.price * OLD.quantity
                            FROM Peliculas p
                            WHERE p.movieid = OLD.movieid)
    WHERE cart_id = OLD.cart_id;
    RETURN OLD;
END;
$$ LANGUAGE plpgsql;

-- TRIGGER: update_total_cart_trigger
-- Se ejecuta después de INSERT o UPDATE en la tabla carrito_pelicula
-- Actualiza el total del carrito según el contenido de la tabla carrito_pelicula
CREATE TRIGGER update_total_cart_onDelete_trigger
AFTER DELETE ON carrito_pelicula
FOR EACH ROW
EXECUTE FUNCTION update_total_cart_onDelete();
