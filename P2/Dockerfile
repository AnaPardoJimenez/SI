# ==============================================================================
# Dockerfile - Contenedor Docker para Sistema de Catálogo de Películas
# ==============================================================================
#
# Este Dockerfile crea una imagen base para ejecutar los servicios del sistema
# de catálogo de películas y gestión de usuarios.
#
# La imagen incluye:
#   - Python 3.12
#   - Dependencias del proyecto (requirements.txt)
#   - Código fuente del proyecto
#
# Autor: Juan Larrondo Fernández de Córdoba y Ana Pardo Jiménez
# Fecha de creación: 28-10-2025
# Última modificación: 28-10-2025
#
# Uso:
#   Este Dockerfile se utiliza automáticamente por docker-compose.yml
#   para construir los contenedores de los servicios.
#
# ==============================================================================

# Imagen base: Python 3.12 oficial
FROM python:3.12

# Establecer directorio de trabajo dentro del contenedor
WORKDIR /app

# Copiar archivo de dependencias
COPY requirements.txt requirements.txt

# Instalar dependencias sin caché para reducir tamaño de imagen
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el resto del código al contenedor (api.py, user.py, cliente.py, schema.sql, etc.)
COPY . .

# Exponer ambos puertos (los usará docker-compose)
EXPOSE 5050
EXPOSE 5051
EXPOSE 5432
EXPOSE 9999

# No fijamos un CMD aquí, lo define docker-compose con "command"
CMD ["python3"]
