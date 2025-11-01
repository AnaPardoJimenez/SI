# ==============================================================================
# Dockerfile - Sistema de Gestión de Usuarios y Archivos con API REST
# ==============================================================================

# Imagen base: Python 3.12 oficial
FROM python:3.12

# Establecer directorio de trabajo dentro del contenedor
WORKDIR /app

# Copiar archivo de dependencias
COPY requirements.txt requirements.txt

# Instalar dependencias sin caché para reducir tamaño de imagen
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el resto del código al contenedor (api.py, user.py, cliente.py, etc.)
COPY . .

# Exponer ambos puertos (los usará docker-compose)
EXPOSE 5050
EXPOSE 5051
EXPOSE 5432
EXPOSE 9999

# No fijamos un CMD aquí, lo define docker-compose con "command"
CMD ["python3"]
