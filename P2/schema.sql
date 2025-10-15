-- Esquema de base de datos para sistema de películas
-- Basado en el diagrama ERD proporcionado

-- Tabla de Actores
CREATE TABLE Actores (
    actor_id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL
);

-- Tabla de Películas
CREATE TABLE Peliculas (
    movie_id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description VARCHAR(1023),
    year INT,
    genre VARCHAR(100),
    price DECIMAL(10,2)
);

-- Tabla de Usuarios
CREATE TABLE Usuario (
    user_id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    password VARCHAR(255) NOT NULL,
    token VARCHAR(255),
    balance DECIMAL(10,2) DEFAULT 0.00
);

-- Tabla de Carrito/Órdenes
CREATE TABLE Carrito (
    order_id SERIAL PRIMARY KEY,
    user_id INT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES Usuario(user_id)
);

-- Tabla de Participación (Junction table para Actores-Películas)
CREATE TABLE Participa (
    actor_id INT,
    movie_id INT,
    PRIMARY KEY (actor_id, movie_id),
    FOREIGN KEY (actor_id) REFERENCES Actores(actor_id),
    FOREIGN KEY (movie_id) REFERENCES Peliculas(movie_id)
);

-- Tabla de Pertenencia (Junction table para Carrito-Películas)
CREATE TABLE Pertenece (
    order_id INT,
    movie_id INT,
    PRIMARY KEY (order_id, movie_id),
    FOREIGN KEY (order_id) REFERENCES Carrito(order_id),
    FOREIGN KEY (movie_id) REFERENCES Peliculas(movie_id)
);

-- Índices para mejorar el rendimiento
-- CREATE INDEX idx_peliculas_year ON Peliculas(year);
-- CREATE INDEX idx_peliculas_genre ON Peliculas(genre);
-- CREATE INDEX idx_participa_actor ON Participa(actor_id);
-- CREATE INDEX idx_participa_movie ON Participa(movie_id);
-- CREATE INDEX idx_pertenece_order ON Pertenece(order_id);
-- CREATE INDEX idx_pertenece_movie ON Pertenece(movie_id);