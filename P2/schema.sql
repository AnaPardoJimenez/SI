-- Esquema de base de datos para sistema de películas
-- Basado en el diagrama ERD proporcionado

-- Tabla de Usuarios
CREATE TABLE Usuario (
    user_id VARCHAR(37) NOT NULL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    password VARCHAR(255) NOT NULL,
    token VARCHAR(255),
    balance DECIMAL(10,2) DEFAULT 0.00,
    admin BOOLEAN DEFAULT FALSE
);

-- Tabla de Actores
CREATE TABLE Actores (
    actor_id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL
);

-- Tabla de Películas
CREATE TABLE Peliculas (
    movieid SERIAL PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    description VARCHAR(1023),
    year INT,
    genre VARCHAR(100),
    price DECIMAL(10,2),
    rating DECIMAL(10,2),
    votes INT
);

CREATE TABLE Calificacion (
    user_id VARCHAR(37),
    movieid INT,
    rating DECIMAL(10,2),
    PRIMARY KEY (user_id, movieid),
    FOREIGN KEY (user_id) REFERENCES Usuario(user_id) ON DELETE CASCADE,
    FOREIGN KEY (movieid) REFERENCES Peliculas(movieid) ON DELETE CASCADE
);

-- Tabla de Participación (Junction table para Actores-Películas)
CREATE TABLE Participa (
    actor_id INT,
    movieid INT,
    PRIMARY KEY (actor_id, movieid),
    FOREIGN KEY (actor_id) REFERENCES Actores(actor_id) ON DELETE CASCADE,
    FOREIGN KEY (movieid) REFERENCES Peliculas(movieid) ON DELETE CASCADE
);

-- Tabla de Carrito/Órdenes
CREATE TABLE Carrito (
    cart_id SERIAL PRIMARY KEY,
    user_id VARCHAR(37) NOT NULL,
    FOREIGN KEY (user_id) REFERENCES Usuario(user_id) ON DELETE CASCADE
);

-- Tabla de Pertenencia (Junction table para Carrito-Películas)
CREATE TABLE Carrito_Pelicula (
    cart_id INT,
    movieid INT,
    PRIMARY KEY (cart_id, movieid),
    FOREIGN KEY (cart_id) REFERENCES Carrito(cart_id) ON DELETE CASCADE,
    FOREIGN KEY (movieid) REFERENCES Peliculas(movieid) ON DELETE CASCADE
);

CREATE TABLE Pedido (
    order_id INT PRIMARY KEY,
    user_id VARCHAR(37) NOT NULL,
    total DECIMAL(10,2) NOT NULL,
    date TIMESTAMP NOT NULL,
    FOREIGN KEY (user_id) REFERENCES Usuario(user_id) ON DELETE CASCADE
);

CREATE TABLE Pedido_Pelicula (
    order_id INT,
    movieid INT,
    PRIMARY KEY (order_id, movieid),
    FOREIGN KEY (order_id) REFERENCES Pedido(order_id) ON DELETE CASCADE,
    FOREIGN KEY (movieid) REFERENCES Peliculas(movieid) ON DELETE CASCADE
);

-- Índices para mejorar el rendimiento
-- CREATE INDEX idx_peliculas_year ON Peliculas(year);
-- CREATE INDEX idx_peliculas_genre ON Peliculas(genre);
-- CREATE INDEX idx_participa_actor ON Participa(actor_id);
-- CREATE INDEX idx_participa_movie ON Participa(movieid);
-- CREATE INDEX idx_pertenece_order ON Pertenece(order_id);
-- CREATE INDEX idx_pertenece_movie ON Pertenece(movieid);