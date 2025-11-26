# SI
* **P1** (4 semanas): entrega 13-15 de octubre
* **P2** (3 semanas): entrega 3-5 de noviembre
* **P3** (4 semanas): __

### EVALUACIÓN
- Cada práctica cuenta 1/3
- Examen final de prácticas

## P1
1. **Semanas 1 y 2**: API Rest
2. **Semana 3**: Contenedores
3. **Semana 4**: Repaso de dudas
Hay que entregar una **memoria** (no muy larga)


### Funciones
**PARA USER**
* create_user (ej: guardar en un .txt o un csv con pandas)
  * Comprobar si el user existe
  * Creo el user
  * Crear una carpeta UID del usuario (con el secret y lo del hash. También valdría guardar el UID en el .txt o archivo de guardado)
* login = get_user_id
  * Utilizar el secret (o buscar en el fichero donde se guardan los usuarios ; passwords ; UID) y devolver el UID

**PARA FILE**
* List: listado de libros en la librería
  * Hacer un ls de la ruta del user con su UID
* Añadir (add)
  * Coge el fichero (con la ruta obtenida con el UID) y añade
* Borrar (rm)
  * Elimina la ruta del fichero concreto
* Leer (get_book)


### Contenedores
Contenedor: parecido a una máquina virtual pero mucho más compacta
  * No instalo un sistema operativo ni componente para que funcione
  * Mayor rapidez, independencia y compatibilidad con microservicios
Sirven para meter el microservicio a una zona independiente con los recursos que yo diga (en lugar de todos los recursos que ofrece el SO)

#### **Comandos Docker básicos:**
* **docker run**: Crea y ejecuta un contenedor desde una imagen
  * Ejemplo: `docker run mi_imagen python --version`
* **docker start/stop**: Inicia o detiene un contenedor existente
* **docker ps**: Lista contenedores en ejecución
  * `docker ps -a`: Lista TODOS los contenedores (incluso detenidos)
* **docker images**: Lista todas las imágenes disponibles
* **docker network ls**: Lista todas las redes de Docker
* **docker volume ls**: Lista todos los volúmenes de Docker
* **docker rm**: Elimina contenedores
* **docker rmi**: Elimina imágenes

#### **Dockerfile:**
Archivo que define cómo construir UNA imagen. Define:
  * Imagen base (FROM python:3.12)
  * Directorio de trabajo (WORKDIR /app)
  * Copiar archivos (COPY requirements.txt)
  * Instalar dependencias (RUN pip install -r requirements.txt)
  * Exponer puertos (EXPOSE 5050 5051)
  * Comando por defecto (CMD ["python"])

#### **Docker Compose:**
Herramienta para orquestar MÚLTIPLES contenedores. Lee el archivo `docker-compose.yml` y:
  * Define múltiples servicios (user_api, file_api)
  * Configura puertos, volúmenes, redes
  * Levanta todo con un solo comando

**Comandos principales:**
* **Levantar servicios (construye y ejecuta):**
  ```bash
  sudo docker-compose up --build
  ```
* **Levantar en background (detached: libera la terminal tras levantar los contenedores):**
  ```bash
  sudo docker-compose up -d --build
  ```
* **Detener y limpiar:**
  ```bash
  sudo docker-compose down --remove-orphans
  ```
* **Solo construir imágenes (sin levantar):**
  ```bash
  sudo docker-compose build
  ```
  (No es necesario, `up --build` hace ambas cosas)

#### **Limpieza completa (ANTES DE ENTREGAR):**
Para asegurarse de que funciona desde cero en cualquier máquina:

```bash
# Paso 1: Detener y eliminar contenedores (incluye huérfanos)
cd /home/juan/A3Q1/SI
docker-compose down --remove-orphans -v

# Paso 2: Eliminar imágenes de tus servicios
docker rmi p3_user_api p3_api_api
docker image prune

# Paso 3: Eliminar todos los volúmenes (CUIDADO, LOS ELIMINA TODOS)
docker volume prune

# Paso 3: Eliminar imagen base Python (prueba completa)
# sudo docker rmi python:3.12

# Paso 4: Limpiar archivos generados por tests
rm -f resources/users.txt
rm -f resources/files/*.txt

# Paso 4.5: Comprobar que todo está limpio
docker ps -a
docker images
docker network ls
docker volume ls
ls -la resources/
ls -la resources/files/

# Paso 5: Reconstruir y probar desde cero
sudo docker-compose up --build
```

**Nota:** El paso 3 solo hay que hacerlo una vez para probar desde cero. Tarda minutos porque descarga python:3.12 (1.11GB).

#### **Verificar que funciona:**
```bash
# En otra terminal (mientras docker-compose está corriendo) o en la misma si se ha levantado en background (-d)
pytest -vv -s client.py
```
* `-vv`: todos los detalles (-v también vale). Muestra nombres de tests y resultado
* `-s`: no desactivar la captura de salida (deja que print() se muestre en terminal)


  |.     file/UID/nombre_archivo.extension      |.      public/private.        |.       info archivo.       |


## P2
**sudo docker exec -it postgres_si1 psql -U alumnodb -d si1 (15.14 (Debian 15.14-1.pgdg13+1))**: Para probar las query de la base de datos a pelo