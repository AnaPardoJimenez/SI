-- =============================================================================
-- schema.sql - Esquema de Base de Datos para Sistema de Catálogo de Películas
-- =============================================================================
--
-- Este script crea el esquema completo de la base de datos para el sistema
-- de catálogo de películas y gestión de pedidos.
--
-- Estructura:
--   - Tablas principales: Usuario, Peliculas, Actores, Carrito, Pedido
--   - Tablas de relación: Participa, Carrito_Pelicula, Pedido_Pelicula, Calificacion
--   - Claves foráneas con ON DELETE CASCADE para mantener integridad referencial
--
-- Autor: Juan Larrondo Fernández de Córdoba y Ana Pardo Jiménez
-- Fecha de creación: 28-10-2025
-- Última modificación: 28-10-2025
--
-- Uso:
--   Este script se ejecuta automáticamente al inicializar la base de datos
--   con Docker Compose (ver docker-compose.yml).
--
-- Nota: Este script debe ejecutarse antes de populate.sql.
--
-- =============================================================================

-- =============================================================================
-- Tabla de Usuarios
-- =============================================================================
-- Almacena información de usuarios del sistema, incluyendo credenciales,
-- tokens de autenticación, saldo y permisos de administrador.
CREATE TABLE Usuario (
    user_id VARCHAR(37) NOT NULL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    password VARCHAR(255) NOT NULL,
    token VARCHAR(255),
    nationality VARCHAR(255),
    discount INT DEFAULT 0,
    balance DECIMAL(10,2) DEFAULT 0.00,
    admin BOOLEAN DEFAULT FALSE
);

-- =============================================================================
-- Tabla de Actores
-- =============================================================================
-- Almacena información de actores que participan en las películas.
CREATE TABLE Actores (
    actor_id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL
);

-- =============================================================================
-- Tabla de Películas
-- =============================================================================
-- Almacena información de películas del catálogo, incluyendo metadatos
-- y precio. El rating y votes se actualizan dinámicamente con las calificaciones.
CREATE TABLE Peliculas (
    movieid SERIAL PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    description VARCHAR(1023),
    year INT,
    genre VARCHAR(100),
    price DECIMAL(10,2),
    rating DECIMAL(10,2),
    stock INT DEFAULT 0,
    votes INT
);

-- =============================================================================
-- Tabla de Calificaciones
-- =============================================================================
-- Almacena las calificaciones que los usuarios dan a las películas.
-- Cada usuario puede calificar cada película una vez (clave primaria compuesta).
CREATE TABLE Calificacion (
    user_id VARCHAR(37),
    movieid INT,
    rating DECIMAL(10,2),
    PRIMARY KEY (user_id, movieid),
    FOREIGN KEY (user_id) REFERENCES Usuario(user_id) ON DELETE CASCADE,
    FOREIGN KEY (movieid) REFERENCES Peliculas(movieid) ON DELETE CASCADE
);

-- =============================================================================
-- Tabla de Participación (Relación N:M entre Actores y Películas)
-- =============================================================================
-- Tabla de relación que conecta actores con las películas en las que participan.
CREATE TABLE Participa (
    actor_id INT,
    movieid INT,
    PRIMARY KEY (actor_id, movieid),
    FOREIGN KEY (actor_id) REFERENCES Actores(actor_id) ON DELETE CASCADE,
    FOREIGN KEY (movieid) REFERENCES Peliculas(movieid) ON DELETE CASCADE
);

-- =============================================================================
-- Tabla de Carrito
-- =============================================================================
-- Cada usuario tiene un carrito de compra único que se crea automáticamente
-- al registrarse. El cart_id se reutiliza como order_id cuando se procesa
-- el pedido.
CREATE TABLE Carrito (
    cart_id SERIAL PRIMARY KEY,
    user_id VARCHAR(37) NOT NULL,
    FOREIGN KEY (user_id) REFERENCES Usuario(user_id) ON DELETE CASCADE
);

-- =============================================================================
-- Tabla de Carrito_Pelicula (Relación N:M entre Carrito y Películas)
-- =============================================================================
-- Tabla de relación que conecta carritos con las películas que contienen.
CREATE TABLE Carrito_Pelicula (
    cart_id INT,
    movieid INT,
    quantity INT DEFAULT 1,
    PRIMARY KEY (cart_id, movieid),
    FOREIGN KEY (cart_id) REFERENCES Carrito(cart_id) ON DELETE CASCADE,
    FOREIGN KEY (movieid) REFERENCES Peliculas(movieid) ON DELETE CASCADE
);

-- =============================================================================
-- Tabla de Pedido
-- =============================================================================
-- Almacena información de pedidos procesados. El order_id coincide con
-- el cart_id del carrito del que se generó el pedido.
CREATE TABLE Pedido (
    order_id INT PRIMARY KEY,
    user_id VARCHAR(37) NOT NULL,
    total DECIMAL(10,2) NOT NULL,
    date TIMESTAMP NOT NULL,
    FOREIGN KEY (user_id) REFERENCES Usuario(user_id) ON DELETE CASCADE
);

-- =============================================================================
-- Tabla de Pedido_Pelicula (Relación N:M entre Pedido y Películas)
-- =============================================================================
-- Tabla de relación que conecta pedidos con las películas que contienen.
CREATE TABLE Pedido_Pelicula (
    order_id INT,
    movieid INT,
    PRIMARY KEY (order_id, movieid),
    FOREIGN KEY (order_id) REFERENCES Pedido(order_id) ON DELETE CASCADE,
    FOREIGN KEY (movieid) REFERENCES Peliculas(movieid) ON DELETE CASCADE
);

-- =============================================================================
-- Índices para Mejorar el Rendimiento
-- =============================================================================
-- Los siguientes índices están comentados pero pueden ser útiles para
-- optimizar consultas frecuentes. Descomentarlos si se necesita mejorar
-- el rendimiento en búsquedas por año, género o relaciones.
CREATE INDEX idx_peliculas_year ON Peliculas(year);
CREATE INDEX idx_peliculas_genre ON Peliculas(genre);
CREATE INDEX idx_participa_actor ON Participa(actor_id);
CREATE INDEX idx_participa_movie ON Participa(movieid);
CREATE INDEX idx_carrito_pelicula_cart ON Carrito_Pelicula(cart_id);
CREATE INDEX idx_carrito_pelicula_movie ON Carrito_Pelicula(movieid);
CREATE INDEX idx_pedido_pelicula_order ON Pedido_Pelicula(order_id);
CREATE INDEX idx_pedido_pelicula_movie ON Pedido_Pelicula(movieid);
CREATE INDEX idx_calificacion_movie ON Calificacion(movieid);
CREATE INDEX idx_calificacion_user ON Calificacion(user_id);