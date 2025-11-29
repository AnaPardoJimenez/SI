-- =============================================================================
-- populate.sql - Script de Población de Base de Datos
-- =============================================================================
-- 
-- Este script inserta datos iniciales en las tablas del sistema de catálogo
-- de películas. Incluye películas de diversas sagas populares y sus actores
-- asociados.
--
-- Datos incluidos:
--   - Usuario administrador por defecto (admin/admin)
--   - Actores de diversas películas y sagas
--   - Películas de Star Wars, Harry Potter, LOTR/Hobbit, Studio Ghibli,
--     Matrix, Evangelion, Pixar y otras películas populares
--   - Relaciones de participación de actores en películas
--
-- Autor: Juan Larrondo Fernández de Córdoba y Ana Pardo Jiménez
-- Fecha de creación: 28-10-2025
-- Última modificación: 28-10-2025
--
-- Uso:
--   Este script se ejecuta automáticamente al inicializar la base de datos
--   con Docker Compose (ver docker-compose.yml).
--
-- Nota: Este script debe ejecutarse después de schema.sql para que las
--       tablas existan previamente.
--
-- =============================================================================

-- Usuario administrador por defecto
-- Credenciales: name='admin', password='admin'
-- Token: f8a7b6c5-d4e3-2f10-9e8d-7c6b5a493827
-- Saldo inicial: 15000.00
-- =============================================================================

INSERT INTO Usuario (user_id, name, password, token, nationality, discount, balance, admin) VALUES
('123e4567-e89b-12d3-a456-426614174000', 'admin', 'be36316a288a721dfe60768ea309880006cb8c980129869fb21128cb0702ac9929dc5a9dd1fec590785f6c6cb60821fa2a92cd37395f18e87f06c07406544f84', 'f8a7b6c5-d4e3-2f10-9e8d-7c6b5a493827', 'España', 0, 15000.00, TRUE),
('123e4567-e89b-12d3-a456-426614174001', 'juan', 'be36316a288a721dfe60768ea309880006cb8c980129869fb21128cb0702ac9929dc5a9dd1fec590785f6c6cb60821fa2a92cd37395f18e87f06c07406544f84', 'f8a7b6c5-d4e3-2f10-9e8d-7c6b5a493827', 'España', 0, 15000.00, FALSE);


-- =============================================================================
-- Insertar Actores
-- =============================================================================
-- Se insertan actores de diversas sagas y películas populares
INSERT INTO Actores (name) VALUES 
-- Star Wars
('Mark Hamill'),
('Harrison Ford'),
('Carrie Fisher'),
('Ewan McGregor'),
('Natalie Portman'),
('Hayden Christensen'),
('Samuel L. Jackson'),
('Liam Neeson'),
-- Harry Potter
('Daniel Radcliffe'),
('Emma Watson'),
('Rupert Grint'),
('Alan Rickman'),
('Maggie Smith'),
('Robbie Coltrane'),
-- LOTR/Hobbit
('Elijah Wood'),
('Ian McKellen'),
('Orlando Bloom'),
('Viggo Mortensen'),
('Martin Freeman'),
('Richard Armitage'),
-- Pixar
('Ellen DeGeneres'),
('Albert Brooks'),
('Alexander Gould'),
-- Studio Ghibli
('Daveigh Chase'),
('Miyu Irino'),
('Rumi Hiiragi'),
('Mari Natsuki'),
-- Anime
('Ryunosuke Kamiki'),
('Mone Kamishiraishi'),
('Miyu Irino'),
('Saori Hayami'),
-- Matrix
('Keanu Reeves'),
('Laurence Fishburne'),
('Carrie-Anne Moss'),
('Hugo Weaving'),
-- Evangelion
('Megumi Ogata'),
('Kotono Mitsuishi'),
('Yuriko Yamaguchi'),
('Takeshi Kusao'),
-- Others
('Al Pacino'),
('John Travolta'),
('Christian Bale'),
('Leonardo DiCaprio'),
('Tom Hanks'),
('Jim Caviezel'),
('Asa Butterfield'),
('Seth Rogen'),
('Tom Hardy');

-- =============================================================================
-- Insertar Películas
-- =============================================================================
-- Se insertan películas de diversas sagas con sus metadatos:
--   - Título y descripción
--   - Año de lanzamiento
--   - Género
--   - Precio de venta
--   - Rating y votos iniciales (0, se actualizan con calificaciones)
INSERT INTO Peliculas (title, description, year, genre, price, rating, votes, stock) VALUES 
-- Star Wars Saga
('Star Wars: Episode IV - A New Hope', 'The story of Luke Skywalker and the Rebellion against the Galactic Empire', 1977, 'Science Fiction', 12.99, 0, 0, 100),
('Star Wars: Episode V - The Empire Strikes Back', 'Luke learns about the Force while the Rebellion fights against the Empire', 1980, 'Science Fiction', 12.99, 0, 0, 100),
('Star Wars: Episode VI - Return of the Jedi', 'The final battle between good and evil in the galaxy', 1983, 'Science Fiction', 12.99, 0, 0, 100),
('Star Wars: Episode I - The Phantom Menace', 'The story of Anakin Skywalker and the invasion of Naboo', 1999, 'Science Fiction', 11.99, 0, 0, 100),
('Star Wars: Episode II - Attack of the Clones', 'Anakin becomes a Jedi while the galaxy prepares for war', 2002, 'Science Fiction', 11.99, 0, 0, 100),
('Star Wars: Episode III - Revenge of the Sith', 'The transformation of Anakin Skywalker into Darth Vader', 2005, 'Science Fiction', 11.99, 0, 0, 100),

-- Harry Potter Saga
('Harry Potter and the Philosopher''s Stone', 'A boy discovers he is a wizard and enters Hogwarts', 2001, 'Fantasy', 10.99, 0, 0, 100),
('Harry Potter and the Chamber of Secrets', 'Harry returns to Hogwarts where mysterious attacks occur', 2002, 'Fantasy', 10.99, 0, 0, 100),
('Harry Potter and the Prisoner of Azkaban', 'Harry discovers the truth about his parents and Sirius Black', 2004, 'Fantasy', 10.99, 0, 0, 100),
('Harry Potter and the Goblet of Fire', 'Harry participates in the Triwizard Tournament', 2005, 'Fantasy', 10.99, 0, 0, 100),
('Harry Potter and the Order of the Phoenix', 'Harry forms Dumbledore''s Army to fight against Voldemort', 2007, 'Fantasy', 10.99, 0, 0, 100),
('Harry Potter and the Half-Blood Prince', 'Harry learns about Voldemort''s past', 2009, 'Fantasy', 10.99, 0, 0, 100),
('Harry Potter and the Deathly Hallows Part 1', 'Harry, Ron and Hermione search for the Horcruxes', 2010, 'Fantasy', 10.99, 0, 0, 100),
('Harry Potter and the Deathly Hallows Part 2', 'The final battle between Harry and Voldemort', 2011, 'Fantasy', 10.99, 0, 0, 100),

-- The Hobbit and LOTR
('The Hobbit: An Unexpected Journey', 'Bilbo Baggins joins an epic adventure with dwarves', 2012, 'Fantasy', 11.99, 0, 0, 100),
('The Hobbit: The Desolation of Smaug', 'Bilbo and the dwarves reach the Lonely Mountain', 2013, 'Fantasy', 11.99, 0, 0, 100),
('The Hobbit: The Battle of the Five Armies', 'The final battle for the Lonely Mountain', 2014, 'Fantasy', 11.99, 0, 0, 100),
('The Lord of the Rings: The Fellowship of the Ring', 'Frodo embarks on a journey to destroy the One Ring', 2001, 'Fantasy', 12.99, 0, 0, 100),
('The Lord of the Rings: The Two Towers', 'The Fellowship splits as Sauron grows stronger', 2002, 'Fantasy', 12.99, 0, 0, 100),
('The Lord of the Rings: The Return of the King', 'The final battle for Middle-earth', 2003, 'Fantasy', 12.99, 0, 0, 100),

-- Pixar
('Finding Nemo', 'A clownfish searches for his lost son in the ocean', 2003, 'Animation', 9.99, 0, 0, 100),
('Finding Dory', 'Dory searches for her parents with the help of her friends', 2016, 'Animation', 9.99, 0, 0, 100),

-- Studio Ghibli
('Spirited Away', 'A young girl must work in a spiritual world to save her parents', 2001, 'Animation', 11.99, 0, 0, 100),
('My Neighbor Totoro', 'Two sisters discover magical creatures in the forest', 1988, 'Animation', 10.99, 0, 0, 100),
('Princess Mononoke', 'A young prince gets involved in a war between humans and gods', 1997, 'Animation', 11.99, 0, 0, 100),
('Howl''s Moving Castle', 'A young woman is transformed into an old woman and seeks help from a wizard', 2004, 'Animation', 11.99, 0, 0, 100),
('Kiki''s Delivery Service', 'A young witch opens a delivery service in a new city', 1989, 'Animation', 10.99, 0, 0, 100),

-- Anime
('Your Name', 'Two teenagers swap bodies and fall in love', 2016, 'Romance/Anime', 12.99, 0, 0, 100),
('A Silent Voice', 'An ex-bully seeks redemption with a deaf girl', 2016, 'Drama/Anime', 11.99, 0, 0, 100),

-- Matrix (the good ones)
('The Matrix', 'A programmer discovers he lives in a simulated reality', 1999, 'Science Fiction', 10.99, 0, 0, 100),
('The Matrix Reloaded', 'Neo fights against the machines while Zion prepares for war', 2003, 'Science Fiction', 10.99, 0, 0, 100),
('The Matrix Revolutions', 'The final battle between humans and machines', 2003, 'Science Fiction', 10.99, 0, 0, 100),

-- Evangelion
('Neon Genesis Evangelion: Death & Rebirth', 'Compilation and continuation of the Evangelion series', 1997, 'Anime/Science Fiction', 12.99, 0, 0, 100),
('The End of Evangelion', 'The alternate ending of the Evangelion series', 1997, 'Anime/Science Fiction', 12.99, 0, 0, 100),
('Evangelion: 1.0 You Are (Not) Alone', 'Evangelion reboot with new animation', 2007, 'Anime/Science Fiction', 11.99, 0, 0, 100),
('Evangelion: 2.0 You Can (Not) Advance', 'Second movie of the Evangelion reboot', 2009, 'Anime/Science Fiction', 11.99, 0, 0, 100),
('Evangelion: 3.0 You Can (Not) Redo', 'Third movie of the Evangelion reboot', 2012, 'Anime/Science Fiction', 11.99, 0, 0, 100),
('Evangelion: 3.0+1.0 Thrice Upon a Time', 'The final movie of the Evangelion reboot', 2021, 'Anime/Science Fiction', 12.99, 0, 0, 100),

-- Other movies
('The Passion of the Christ', 'The story of the last days of Jesus Christ', 2004, 'Religious Drama', 9.99, 0, 0, 100),
('Ender''s Game', 'A genius child is trained to lead the war against aliens', 2013, 'Science Fiction', 10.99, 0, 0, 100),
('Sausage Party', 'Supermarket foods discover their destiny', 2016, 'Animated Comedy', 8.99, 0, 0, 100),
('The Godfather', 'The story of an Italian mafia family in New York', 1972, 'Drama', 9.99, 0, 0, 100),
('Pulp Fiction', 'Intertwined crime stories in Los Angeles', 1994, 'Crime', 8.99, 0, 0, 100),
('The Dark Knight', 'Batman fights against the Joker in Gotham City', 2008, 'Action', 10.99, 0, 0, 100),
('Inception', 'A thief who steals secrets from dreams', 2010, 'Science Fiction', 12.99, 0, 0, 100),
('Gladiator', 'A gladiator joins the rebellion against the Roman Empire', 2000, 'Action', 10.99, 0, 0, 100),
('Venom', 'A journalist becomes the host of an alien symbiote', 2018, 'Action', 11.99, 0, 0, 100);

-- =============================================================================
-- Insertar Participaciones (Actores en Películas)
-- =============================================================================
-- Se establecen las relaciones entre actores y películas en las que participan.
-- Cada tupla (actor_id, movieid) representa la participación de un actor
-- en una película específica.
INSERT INTO Participa (actor_id, movieid) VALUES 
-- Star Wars
(1, 1), (2, 1), (3, 1), -- Mark Hamill, Harrison Ford, Carrie Fisher in A New Hope
(1, 2), (2, 2), (3, 2), -- In Empire Strikes Back
(1, 3), (2, 3), (3, 3), -- In Return of the Jedi
(4, 4), (5, 4), (6, 4), -- Ewan McGregor, Natalie Portman, Hayden Christensen in Phantom Menace
(4, 5), (5, 5), (6, 5), -- In Attack of the Clones
(4, 6), (5, 6), (6, 6), -- In Revenge of the Sith

-- Harry Potter
(9, 7), (10, 7), (11, 7), -- Daniel Radcliffe, Emma Watson, Rupert Grint in Philosopher's Stone
(9, 8), (10, 8), (11, 8), -- In Chamber of Secrets
(9, 9), (10, 9), (11, 9), -- In Prisoner of Azkaban
(9, 10), (10, 10), (11, 10), -- In Goblet of Fire
(9, 11), (10, 11), (11, 11), -- In Order of the Phoenix
(9, 12), (10, 12), (11, 12), -- In Half-Blood Prince
(9, 13), (10, 13), (11, 13), -- In Deathly Hallows Part 1
(9, 14), (10, 14), (11, 14), -- In Deathly Hallows Part 2

-- LOTR/Hobbit
(15, 19), (16, 19), (17, 19), -- Elijah Wood, Ian McKellen, Orlando Bloom in Fellowship
(15, 20), (16, 20), (17, 20), -- In Two Towers
(15, 21), (16, 21), (17, 21), -- In Return of the King
(20, 16), (21, 16), (22, 16), -- Martin Freeman, Richard Armitage in Hobbit 1
(20, 17), (21, 17), (22, 17), -- In Hobbit 2
(20, 18), (21, 18), (22, 18), -- In Hobbit 3

-- Pixar
(23, 22), (24, 22), (25, 22), -- Ellen DeGeneres, Albert Brooks, Alexander Gould in Finding Nemo
(23, 23), (24, 23), (25, 23), -- In Finding Dory

-- Studio Ghibli
(26, 24), (27, 24), (28, 24), -- Daveigh Chase, Miyu Irino, Rumi Hiiragi in Spirited Away
(26, 25), (27, 25), (28, 25), -- In Totoro
(26, 26), (27, 26), (28, 26), -- In Princess Mononoke
(26, 27), (27, 27), (28, 27), -- In Howl's Moving Castle
(26, 28), (27, 28), (28, 28), -- In Kiki's Delivery Service

-- Anime
(29, 29), (30, 29), -- Ryunosuke Kamiki, Mone Kamishiraishi in Your Name
(31, 30), (32, 30), -- Miyu Irino, Saori Hayami in A Silent Voice

-- Matrix
(33, 31), (34, 31), (35, 31), -- Keanu Reeves, Laurence Fishburne, Carrie-Anne Moss in Matrix
(33, 32), (34, 32), (35, 32), -- In Reloaded
(33, 33), (34, 33), (35, 33), -- In Revolutions

-- Evangelion
(36, 34), (37, 34), (38, 34), -- Megumi Ogata, Kotono Mitsuishi, Yuriko Yamaguchi in Death & Rebirth
(36, 35), (37, 35), (38, 35), -- In End of Evangelion
(36, 36), (37, 36), (38, 36), -- In 1.0
(36, 37), (37, 37), (38, 37), -- In 2.0
(36, 38), (37, 38), (38, 38), -- In 3.0
(36, 39), (37, 39), (38, 39), -- In 3.0+1.0

-- Other movies  
(39, 43), -- Al Pacino in The Godfather (ID 43)
(40, 44), -- John Travolta in Pulp Fiction (ID 44)
(41, 45), -- Christian Bale in The Dark Knight (ID 45)
(42, 40), -- Leonardo DiCaprio in Passion of the Christ (ID 40)
(43, 41), -- Tom Hanks in Ender's Game (ID 41)
(44, 42), -- Jim Caviezel in Sausage Party (ID 42)
(45, 43), -- Asa Butterfield in The Godfather (ID 43)
(46, 44), -- Seth Rogen in Pulp Fiction (ID 44)
(48, 47); -- Tom Hardy in Venom (ID 47)

-- INSERT INTO Pedido (order_id, user_id, total, date, paid) VALUES
-- (1, '123e4567-e89b-12d3-a456-426614174000', 10.99, '2024-01-01', TRUE),
-- (2, '123e4567-e89b-12d3-a456-426614174000', 10.99, '2024-01-02', TRUE),
-- (3, '123e4567-e89b-12d3-a456-426614174001', 10.99, '2025-01-03', TRUE),
-- (4, '123e4567-e89b-12d3-a456-426614174000', 10.99, '2024-01-04', TRUE),
-- (5, '123e4567-e89b-12d3-a456-426614174001', 10.99, '2024-01-05', TRUE),
-- (6, '123e4567-e89b-12d3-a456-426614174000', 10.99, '2024-01-06', TRUE),
-- (7, '123e4567-e89b-12d3-a456-426614174001', 10.99, '2025-01-07', TRUE),
-- (8, '123e4567-e89b-12d3-a456-426614174000', 10.99, '2025-01-08', TRUE),
-- (9, '123e4567-e89b-12d3-a456-426614174001', 10.99, '2025-01-09', TRUE),
-- (10, '123e4567-e89b-12d3-a456-426614174000', 10.99, '2025-01-10', TRUE),
-- (11, '123e4567-e89b-12d3-a456-426614174000', 10.99, '2025-01-11', TRUE),
-- (12, '123e4567-e89b-12d3-a456-426614174001', 10.99, '2025-01-12', TRUE),
-- (13, '123e4567-e89b-12d3-a456-426614174000', 10.99, '2024-01-13', TRUE),
-- (14, '123e4567-e89b-12d3-a456-426614174001', 10.99, '2025-01-14', TRUE),
-- (15, '123e4567-e89b-12d3-a456-426614174001', 10.99, '2025-01-15', TRUE),
-- (16, '123e4567-e89b-12d3-a456-426614174001', 10.99, '2025-01-16', TRUE),
-- (17, '123e4567-e89b-12d3-a456-426614174001', 10.99, '2024-01-17', TRUE),
-- (18, '123e4567-e89b-12d3-a456-426614174001', 10.99, '2024-01-18', TRUE),
-- (19, '123e4567-e89b-12d3-a456-426614174001', 10.99, '2025-01-19', TRUE),
-- (20, '123e4567-e89b-12d3-a456-426614174001', 10.99, '2025-01-20', TRUE);

-- INSERT INTO Paises (pais) VALUES
-- ('España'),
-- ('Reino Unido'),
-- ('Estados Unidos');

-- =============================================================================
-- Insertar Calificaciones para la película ID 1 (Star Wars: A New Hope)
-- =============================================================================
-- Se insertan calificaciones de usuarios para la película con ID 1
-- de cara a la prueba inicial del sistema de ratings mediante
-- procedimiento almacenado al inicio del sistema
INSERT INTO Calificacion (user_id, movieid, rating) VALUES
('123e4567-e89b-12d3-a456-426614174001', 1, 7),
('123e4567-e89b-12d3-a456-426614174000', 1, 9);

-- Actualizar votos de la película ID 1 para reflejar las calificaciones insertadas
UPDATE Peliculas
SET votes = 2
WHERE movieid = 1;
