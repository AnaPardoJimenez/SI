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

CREATE TRIGGER update_stock_trigger
AFTER INSERT OR UPDATE ON carrito_pelicula
FOR EACH ROW
EXECUTE FUNCTION update_stock();