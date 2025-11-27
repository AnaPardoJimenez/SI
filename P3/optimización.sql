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