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
WHEN (OLD.paid = FALSE AND NEW.paid = TRUE)
EXECUTE FUNCTION update_paid();