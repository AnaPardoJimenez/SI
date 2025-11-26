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
    IF NEW.quantity = 0 THEN
        DELETE FROM Carrito_pelicula
        WHERE cart_id = NEW.cart_id AND movieid = NEW.movieid;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_stock_trigger
AFTER INSERT OR UPDATE ON carrito_pelicula
FOR EACH ROW
EXECUTE FUNCTION update_stock();



CREATE FUNCTION update_paid()
RETURNS TRIGGER AS $$
BEGIN
    -- Restar el total del pedido del balance del usuario
    UPDATE Usuario
    SET balance = balance - NEW.total
    WHERE user_id = NEW.user_id;

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

CREATE TRIGGER update_paid_trigger
AFTER UPDATE OF paid ON pedido
FOR EACH ROW
WHEN (NEW.paid = TRUE)
EXECUTE FUNCTION update_paid();



CREATE FUNCTION insert_rating()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE Peliculas
    SET rating = (rating * (votes-1) + NEW.rating) / votes
    WHERE movieid = NEW.movieid;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER insert_rating_trigger
AFTER INSERT ON calificacion
FOR EACH ROW
EXECUTE FUNCTION insert_rating();



CREATE FUNCTION update_rating()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE Peliculas
    SET rating = media_rating(NEW.movieid)
    WHERE OLD.movieid = NEW.movieid;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_rating_trigger
AFTER UPDATE ON calificacion
FOR EACH ROW
EXECUTE FUNCTION update_rating();


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