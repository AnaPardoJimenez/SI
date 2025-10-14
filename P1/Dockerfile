# ==============================================================================
# Dockerfile - Sistema de Gestión de Usuarios y Archivos con API REST
# ==============================================================================
#
# Descripción:
#   Imagen Docker para ejecutar el sistema de gestión de usuarios y archivos
#
# Autor: Juan Larrondo Fernández de Córdoba y Ana Pardo Jiménez
# Fecha de creación: 8-10-2025
# Última modificación: 11-10-2025
# Versión: 1.0.0
#
# Imagen base: python:3.12
# Puertos expuestos:
#   - 5050: API de gestión de usuarios
#   - 5051: API de gestión de archivos
#
# ==============================================================================

# Imagen base: Python 3.12 oficial
FROM python:3.12

# Establecer directorio de trabajo dentro del contenedor
WORKDIR /app

# Copiar archivo de dependencias al contenedor
COPY requirements.txt requirements.txt

# Instalar dependencias de Python sin caché para reducir tamaño de imagen
RUN pip install --no-cache-dir -r requirements.txt

# Exponer puerto 5051 (API de gestión de archivos)
EXPOSE 5051

# Exponer puerto 5050 (API de gestión de usuarios)
EXPOSE 5050

# Comando por defecto: iniciar intérprete de Python
CMD ["python"]