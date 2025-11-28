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
-- DESCRIPCIÓN: Actualiza automáticamente el stock de películas cuando se
--              insertan o modifican elementos en el carrito.
-- LÓGICA:
--   - INSERT: Reduce el stock (quantity negativo)
--   - UPDATE: Ajusta el stock según la diferencia entre cantidad antigua y nueva
-- ============================================================================
CREATE OR REPLACE FUNCTION update_stock()
RETURNS TRIGGER AS $$
DECLARE
    quantity INT;
BEGIN
    IF TG_OP = 'INSERT' THEN
        quantity := -NEW.quantity;
    ELSIF TG_OP = 'UPDATE' THEN
        quantity := OLD.quantity - NEW.quantity;
    END IF;

    UPDATE Peliculas
    SET stock = stock + quantity
    WHERE movieid = NEW.movieid;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- TRIGGER: update_stock_trigger
-- Se ejecuta después de INSERT o UPDATE en la tabla carrito_pelicula
-- Mantiene el stock de películas sincronizado con el contenido del carrito
CREATE TRIGGER update_stock_trigger
AFTER INSERT OR UPDATE OR DELETE ON carrito_pelicula
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
    UPDATE Carrito
    SET total = (SELECT SUM(p.price * cp.quantity)
                    FROM Carrito_Pelicula cp
                    JOIN Peliculas p ON cp.movieid = p.movieid
                    WHERE cp.cart_id = NEW.cart_id)
    WHERE cart_id = NEW.cart_id;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- TRIGGER: update_total_cart_trigger
-- Se ejecuta después de INSERT o UPDATE en la tabla carrito_pelicula
-- Actualiza el total del carrito según el contenido de la tabla carrito_pelicula
CREATE TRIGGER update_total_cart_trigger
AFTER INSERT OR UPDATE ON carrito_pelicula
FOR EACH ROW
EXECUTE FUNCTION update_total_cart();