-- Datos para poblar las tablas del sistema de películas
-- Incluye Star Wars, Harry Potter, LOTR, Ghibli, Evangelion y más!


-- Insertar Actores
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
-- Otros
('Al Pacino'),
('John Travolta'),
('Christian Bale'),
('Leonardo DiCaprio'),
('Tom Hanks'),
('Jim Caviezel'),
('Asa Butterfield'),
('Seth Rogen');

-- Insertar Películas
INSERT INTO Peliculas (name, description, year, genre, price) VALUES 
-- Star Wars Saga
('Star Wars: Episode IV - A New Hope', 'La historia de Luke Skywalker y la Rebelión contra el Imperio Galáctico', 1977, 'Ciencia Ficción', 12.99),
('Star Wars: Episode V - The Empire Strikes Back', 'Luke aprende sobre la Fuerza mientras la Rebelión lucha contra el Imperio', 1980, 'Ciencia Ficción', 12.99),
('Star Wars: Episode VI - Return of the Jedi', 'La batalla final entre el bien y el mal en la galaxia', 1983, 'Ciencia Ficción', 12.99),
('Star Wars: Episode I - The Phantom Menace', 'La historia de Anakin Skywalker y la invasión de Naboo', 1999, 'Ciencia Ficción', 11.99),
('Star Wars: Episode II - Attack of the Clones', 'Anakin se convierte en Jedi mientras la galaxia se prepara para la guerra', 2002, 'Ciencia Ficción', 11.99),
('Star Wars: Episode III - Revenge of the Sith', 'La transformación de Anakin Skywalker en Darth Vader', 2005, 'Ciencia Ficción', 11.99),

-- Harry Potter Saga
('Harry Potter and the Philosopher''s Stone', 'Un niño descubre que es un mago y entra a Hogwarts', 2001, 'Fantasía', 10.99),
('Harry Potter and the Chamber of Secrets', 'Harry regresa a Hogwarts donde ocurren misteriosos ataques', 2002, 'Fantasía', 10.99),
('Harry Potter and the Prisoner of Azkaban', 'Harry descubre la verdad sobre sus padres y Sirius Black', 2004, 'Fantasía', 10.99),
('Harry Potter and the Goblet of Fire', 'Harry participa en el Torneo de los Tres Magos', 2005, 'Fantasía', 10.99),
('Harry Potter and the Order of the Phoenix', 'Harry forma la Armada de Dumbledore para luchar contra Voldemort', 2007, 'Fantasía', 10.99),
('Harry Potter and the Half-Blood Prince', 'Harry aprende sobre el pasado de Voldemort', 2009, 'Fantasía', 10.99),
('Harry Potter and the Deathly Hallows Part 1', 'Harry, Ron y Hermione buscan los Horrocruxes', 2010, 'Fantasía', 10.99),
('Harry Potter and the Deathly Hallows Part 2', 'La batalla final entre Harry y Voldemort', 2011, 'Fantasía', 10.99),

-- El Hobbit y LOTR
('The Hobbit: An Unexpected Journey', 'Bilbo Baggins se une a una aventura épica con enanos', 2012, 'Fantasía', 11.99),
('The Hobbit: The Desolation of Smaug', 'Bilbo y los enanos llegan a la Montaña Solitaria', 2013, 'Fantasía', 11.99),
('The Hobbit: The Battle of the Five Armies', 'La batalla final por la Montaña Solitaria', 2014, 'Fantasía', 11.99),
('The Lord of the Rings: The Fellowship of the Ring', 'Frodo emprende un viaje para destruir el Anillo Único', 2001, 'Fantasía', 12.99),
('The Lord of the Rings: The Two Towers', 'La Comunidad se separa mientras Sauron se fortalece', 2002, 'Fantasía', 12.99),
('The Lord of the Rings: The Return of the King', 'La batalla final por la Tierra Media', 2003, 'Fantasía', 12.99),

-- Pixar
('Finding Nemo', 'Un pez payaso busca a su hijo perdido en el océano', 2003, 'Animación', 9.99),
('Finding Dory', 'Dory busca a sus padres con la ayuda de sus amigos', 2016, 'Animación', 9.99),

-- Studio Ghibli
('Spirited Away', 'Una niña debe trabajar en un mundo espiritual para salvar a sus padres', 2001, 'Animación', 11.99),
('My Neighbor Totoro', 'Dos hermanas descubren criaturas mágicas en el bosque', 1988, 'Animación', 10.99),
('Princess Mononoke', 'Un joven príncipe se involucra en una guerra entre humanos y dioses', 1997, 'Animación', 11.99),
('Howl''s Moving Castle', 'Una joven es transformada en anciana y busca ayuda de un mago', 2004, 'Animación', 11.99),
('Kiki''s Delivery Service', 'Una joven bruja abre un servicio de entregas en una nueva ciudad', 1989, 'Animación', 10.99),

-- Anime
('Your Name', 'Dos adolescentes intercambian cuerpos y se enamoran', 2016, 'Romance/Anime', 12.99),
('A Silent Voice', 'Un ex-bully busca redención con una chica sorda', 2016, 'Drama/Anime', 11.99),

-- Matrix (las buenas)
('The Matrix', 'Un programador descubre que vive en una realidad simulada', 1999, 'Ciencia Ficción', 10.99),
('The Matrix Reloaded', 'Neo lucha contra las máquinas mientras Zion se prepara para la guerra', 2003, 'Ciencia Ficción', 10.99),
('The Matrix Revolutions', 'La batalla final entre humanos y máquinas', 2003, 'Ciencia Ficción', 10.99),

-- Evangelion
('Neon Genesis Evangelion: Death & Rebirth', 'Recopilación y continuación de la serie Evangelion', 1997, 'Anime/Ciencia Ficción', 12.99),
('The End of Evangelion', 'El final alternativo de la serie Evangelion', 1997, 'Anime/Ciencia Ficción', 12.99),
('Evangelion: 1.0 You Are (Not) Alone', 'Reboot de Evangelion con nueva animación', 2007, 'Anime/Ciencia Ficción', 11.99),
('Evangelion: 2.0 You Can (Not) Advance', 'Segunda película del reboot de Evangelion', 2009, 'Anime/Ciencia Ficción', 11.99),
('Evangelion: 3.0 You Can (Not) Redo', 'Tercera película del reboot de Evangelion', 2012, 'Anime/Ciencia Ficción', 11.99),
('Evangelion: 3.0+1.0 Thrice Upon a Time', 'La película final del reboot de Evangelion', 2021, 'Anime/Ciencia Ficción', 12.99),

-- Otras películas
('The Passion of the Christ', 'La historia de los últimos días de Jesucristo', 2004, 'Drama Religioso', 9.99),
('Ender''s Game', 'Un niño genio es entrenado para liderar la guerra contra alienígenas', 2013, 'Ciencia Ficción', 10.99),
('Sausage Party', 'Los alimentos de un supermercado descubren su destino', 2016, 'Comedia Animada', 8.99),
('The Godfather', 'La historia de una familia mafiosa italiana en Nueva York', 1972, 'Drama', 9.99),
('Pulp Fiction', 'Historias entrelazadas de crimen en Los Ángeles', 1994, 'Crimen', 8.99),
('The Dark Knight', 'Batman lucha contra el Joker en Gotham City', 2008, 'Acción', 10.99),
('Inception', 'Un ladrón que roba secretos de los sueños', 2010, 'Ciencia Ficción', 12.99);

-- Insertar Usuarios
INSERT INTO Usuario (user_id, name, password, token, balance, admin) VALUES
('123e4567-e89b-12d3-a456-426614174000', 'admin', 'admin', 'f8a7b6c5-d4e3-2f10-9e8d-7c6b5a493827', 15000.00, TRUE);

-- Insertar Carritos
-- Insertar Carritos
-- Si quieres poblar carritos iniciales añade filas aquí con el formato:
--   INSERT INTO Carrito (order_id, user_id) VALUES (1, 'uuid-user-1'), (2, 'uuid-user-2');
-- Actualmente se omite la inserción para evitar errores de sintaxis; asegúrate de
-- crear primero los usuarios referenciados en la tabla Usuario antes de añadir carritos.

-- Insertar Participaciones (Actores en Películas)
INSERT INTO Participa (actor_id, movie_id) VALUES 
-- Star Wars
(1, 1), (2, 1), (3, 1), -- Mark Hamill, Harrison Ford, Carrie Fisher en A New Hope
(1, 2), (2, 2), (3, 2), -- En Empire Strikes Back
(1, 3), (2, 3), (3, 3), -- En Return of the Jedi
(4, 4), (5, 4), (6, 4), -- Ewan McGregor, Natalie Portman, Hayden Christensen en Phantom Menace
(4, 5), (5, 5), (6, 5), -- En Attack of the Clones
(4, 6), (5, 6), (6, 6), -- En Revenge of the Sith

-- Harry Potter
(9, 7), (10, 7), (11, 7), -- Daniel Radcliffe, Emma Watson, Rupert Grint en Philosopher's Stone
(9, 8), (10, 8), (11, 8), -- En Chamber of Secrets
(9, 9), (10, 9), (11, 9), -- En Prisoner of Azkaban
(9, 10), (10, 10), (11, 10), -- En Goblet of Fire
(9, 11), (10, 11), (11, 11), -- En Order of the Phoenix
(9, 12), (10, 12), (11, 12), -- En Half-Blood Prince
(9, 13), (10, 13), (11, 13), -- En Deathly Hallows Part 1
(9, 14), (10, 14), (11, 14), -- En Deathly Hallows Part 2

-- LOTR/Hobbit
(15, 19), (16, 19), (17, 19), -- Elijah Wood, Ian McKellen, Orlando Bloom en Fellowship
(15, 20), (16, 20), (17, 20), -- En Two Towers
(15, 21), (16, 21), (17, 21), -- En Return of the King
(20, 16), (21, 16), (22, 16), -- Martin Freeman, Richard Armitage en Hobbit 1
(20, 17), (21, 17), (22, 17), -- En Hobbit 2
(20, 18), (21, 18), (22, 18), -- En Hobbit 3

-- Pixar
(23, 22), (24, 22), (25, 22), -- Ellen DeGeneres, Albert Brooks, Alexander Gould en Finding Nemo
(23, 23), (24, 23), (25, 23), -- En Finding Dory

-- Studio Ghibli
(26, 24), (27, 24), (28, 24), -- Daveigh Chase, Miyu Irino, Rumi Hiiragi en Spirited Away
(26, 25), (27, 25), (28, 25), -- En Totoro
(26, 26), (27, 26), (28, 26), -- En Princess Mononoke
(26, 27), (27, 27), (28, 27), -- En Howl's Moving Castle
(26, 28), (27, 28), (28, 28), -- En Kiki's Delivery Service

-- Anime
(29, 29), (30, 29), -- Ryunosuke Kamiki, Mone Kamishiraishi en Your Name
(31, 30), (32, 30), -- Miyu Irino, Saori Hayami en A Silent Voice

-- Matrix
(33, 31), (34, 31), (35, 31), -- Keanu Reeves, Laurence Fishburne, Carrie-Anne Moss en Matrix
(33, 32), (34, 32), (35, 32), -- En Reloaded
(33, 33), (34, 33), (35, 33), -- En Revolutions

-- Evangelion
(36, 34), (37, 34), (38, 34), -- Megumi Ogata, Kotono Mitsuishi, Yuriko Yamaguchi en Death & Rebirth
(36, 35), (37, 35), (38, 35), -- En End of Evangelion
(36, 36), (37, 36), (38, 36), -- En 1.0
(36, 37), (37, 37), (38, 37), -- En 2.0
(36, 38), (37, 38), (38, 38), -- En 3.0
(36, 39), (37, 39), (38, 39), -- En 3.0+1.0

-- Otras películas  
(39, 43), -- Al Pacino en The Godfather (ID 43)
(40, 44), -- John Travolta en Pulp Fiction (ID 44)
(41, 45), -- Christian Bale en The Dark Knight (ID 45)
(42, 40), -- Leonardo DiCaprio en Passion of the Christ (ID 40)
(43, 41), -- Tom Hanks en Ender's Game (ID 41)
(44, 42), -- Jim Caviezel en Sausage Party (ID 42)
(45, 43), -- Asa Butterfield en The Godfather (ID 43)
(46, 44); -- Seth Rogen en Pulp Fiction (ID 44)

-- Insertar Pertenencia (Películas en Carritos)
INSERT INTO Pertenece (order_id, movie_id) VALUES 
-- Ana Pardo Jiménez tiene Star Wars en su carrito
(1, 1), (1, 2), (1, 3), (1, 4), (1, 5), (1, 6),
-- Carlos García tiene Harry Potter
(2, 7), (2, 8), (2, 9), (2, 10),
-- María López tiene LOTR y Hobbit
(3, 16), (3, 17), (3, 18), (3, 19), (3, 20), (3, 21),
-- Luis Fernández tiene Studio Ghibli
(4, 24), (4, 25), (4, 26), (4, 27), (4, 28),
-- Sofia Martínez tiene Anime y Matrix
(5, 29), (5, 30), (5, 31), (5, 32), (5, 33);
