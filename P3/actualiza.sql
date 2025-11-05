CREATE OR REPLACE FUNCTION update_stock()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE Peliculas
    SET stock = stock - 1
    WHERE movieid = NEW.movieid;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_stock_trigger
AFTER INSERT OR DELETE ON carrito_pelicula
FOR EACH ROW
EXECUTE FUNCTION update_stock();