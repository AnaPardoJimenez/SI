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
