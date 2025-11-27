----------------------------------
-- Preparación para el deadlock --
----------------------------------
INSERT INTO Usuario (user_id, name, password, token, nationality, admin) VALUES
('100', 'deadlock_user', 'deadlock', 'dead', 'lock', FALSE);

INSERT INTO Pedido(order_id, user_id, total, date) VALUES
(100, '100', 100, '2025-11-27');
----------------------------------
--           SESIÓN 1           --
----------------------------------
-- Dispara trigger
BEGIN;

UPDATE Pedido 
SET paid = true
WHERE order_id = 100;

-- Llega a sleep
UPDATE Usuario
SET discount = 10
WHERE user_id = 100;

----------------------------------
--           SESIÓN 2           --
----------------------------------
-- Bloqueo el discount de user
BEGIN;

UPDATE Usuario
SET discount = 20
WHERE user_id = 100;

-- Update balance
UPDATE Usuario
SET balance = 100
WHERE user_id = 100