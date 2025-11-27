-- Índice para filtrar por nacionalidad (muy selectivo)
CREATE INDEX idx_usuario_nationality ON Usuario(nationality);
-- Índice para el JOIN (user_id en Pedido)
CREATE INDEX idx_pedido_user_id ON Pedido(user_id);
-- Alternativa: índice solo en date si hay muchas consultas por fecha
CREATE INDEX idx_pedido_date ON Pedido(date);
-- Índice compuesto para la consulta (date + user_id para mejor rendimiento)
CREATE INDEX idx_pedido_date_user ON Pedido(user_id, date);

-- EXPLAIN SELECT 
--             p.order_id,
--             p.date,
--             p.total,
--             u.name AS user_name
--         FROM Pedido p
--         INNER JOIN Usuario u ON p.user_id = u.user_id
--         WHERE u.nationality = 'España'
--             AND p.date >= '2025-01-01'
--             AND p.date < '2026-01-01'
--         ORDER BY p.date ASC;

INSERT INTO Usuario (user_id, name, password, token, nationality, admin) VALUES
('100', 'deadlock_user', 'deadlock', 'dead', 'lock', FALSE);

INSERT INTO Pedido(order_id, user_id, total, date) VALUES
(100, '100', 100, '2025-11-27');

BEGIN;

UPDATE Pedido 
SET paid = true
WHERE order_id = 100;

-- Llega a sleep
UPDATE Usuario
SET discount = 10
WHERE user_id = '100';

COMMIT;



BEGIN;

UPDATE Usuario
SET discount = 20
WHERE user_id = '100';

-- Update balance
UPDATE Usuario
SET balance = 100
WHERE user_id = '100';

COMMIT;







INSERT INTO Usuario (user_id, name, password, token, nationality, admin) VALUES
('100', 'deadlock_user', 'deadlock', 'dead', 'lock', FALSE);

INSERT INTO Pedido(order_id, user_id, total, date) VALUES
(100, '100', 100, '2025-11-27');

BEGIN;

UPDATE Usuario
SET discount = 10
WHERE user_id = '100';

-- Llega a sleep
SELECT pg_sleep(5);

-- Vaciar el carrito del usuario (eliminar Carrito_Pelicula y Carrito)
DELETE FROM Carrito_Pelicula
WHERE cart_id = 100;

COMMIT;


BEGIN;

UPDATE Carrito
SET user_id = user_id
WHERE user_id = '100';

-- Llega a sleep
SELECT pg_sleep(5);

UPDATE Usuario
SET discount = 20
WHERE user_id = '100';

COMMIT;