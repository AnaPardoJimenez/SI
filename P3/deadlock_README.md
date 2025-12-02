# Prueba de Interbloqueo (Deadlock) en PostgreSQL

Scripts para demostrar interbloqueos entre el trigger `update_paid` y una transacción externa.

## 📁 Archivos

- `deadlock_setup.sql` - Prepara los datos de prueba
- `deadlock_cliente1.sql` - Dispara el trigger (ejecutar en Terminal 1)
- `deadlock_cliente2.sql` - Transacción externa (ejecutar en Terminal 2)
- `deadlock_cleanup.sql` - Limpia todos los datos de prueba

## 🚀 Ejecución Rápida

### ⚠️ IMPORTANTE: Antes de ejecutar

**Debes descomentar el `pg_sleep(5)` en el trigger `update_paid`:**

Abre el archivo `actualiza.sql` y en la función `update_paid()` (alrededor de la línea 88), descomenta la línea:
```sql
PERFORM pg_sleep(5);
```

Sin este sleep, el deadlock no ocurrirá porque el trigger se ejecutará demasiado rápido.

### 1. Preparar datos
```bash
cd ~/Documentos/GitHub/SI/P3
docker exec -i postgres_si1 psql -U alumnodb -d si1 < deadlock_setup.sql
```

### 2. Abrir DOS terminales

**Terminal 1:**
```bash
docker exec -i postgres_si1 psql -U alumnodb -d si1 < deadlock_cliente1.sql
```

**Terminal 2 (ejecutar INMEDIATAMENTE después, en menos de 2 segundos):**
```bash
docker exec -i postgres_si1 psql -U alumnodb -d si1 < deadlock_cliente2.sql
```

### 3. Limpiar datos (después de la prueba)
```bash
docker exec -i postgres_si1 psql -U alumnodb -d si1 < deadlock_cleanup.sql
```

## 🔄 Cómo funciona el interbloqueo

**Cliente 1** (dispara el trigger `update_paid`):
1. `UPDATE Usuario` (línea ~84 de `actualiza.sql`) → adquiere lock
2. Espera 5 segundos (línea ~88: `PERFORM pg_sleep(5);` - **debe estar descomentado**)
3. `DELETE Carrito_Pelicula` (línea ~91) → **BLOQUEADO** (Cliente 2 tiene el lock)

**Cliente 2** (transacción externa):
1. `DELETE Carrito_Pelicula` → adquiere lock
2. Espera 5 segundos
3. `UPDATE Usuario` → **BLOQUEADO** (Cliente 1 tiene el lock)

**Resultado:** PostgreSQL detecta el deadlock y aborta una transacción.

## ⚠️ Qué esperar

Una de las terminales mostrará:
```
ERROR:  deadlock detected
DETAIL:  Process X waits for ShareLock on transaction Y; 
         Process Z waits for ShareLock on transaction X.
HINT:  See server log for query details.
```

La otra transacción se completará normalmente.

## 📝 Notas importantes

- ⚠️ **Antes de ejecutar:** Descomenta `PERFORM pg_sleep(5);` en la línea ~88 de `actualiza.sql` dentro de la función `update_paid()`
- ⏱️ Ejecuta ambos scripts **casi simultáneamente** (dentro de 2 segundos)
- 🔄 Si no ocurre el deadlock, vuelve a intentar ejecutándolos más rápido
- 🧹 Usa `deadlock_cleanup.sql` para limpiar los datos después de cada prueba