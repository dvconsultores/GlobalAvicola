# PRODUCTION UPGRADE COMPATIBILITY MATRIX

**Fecha** 2026-09-04 · **Wave** 2.5

```
FRESH DATABASE PASS  ≠  PRODUCTION UPGRADE PASS
```

Toda modificación de las Waves 1 y 2 que afecte a estado persistente se verifica por **dos
caminos**: una instalación nueva y la actualización de una existente. La segunda es la que
faltaba, y es la que revela lo que la primera no puede.

---

## 1. Los dos caminos

| | `PATH A` — instalación nueva | `PATH B` — actualización |
|---|---|---|
| Base | `global_avicola_test` | `global_avicola_upgrade_test` |
| Punto de partida | PostgreSQL vacío | esquema en `i9j0k1l2m3n4` (*head* anterior a la Wave 2) |
| Datos | semillas actuales | **matriz de permisos histórica** (24 asociaciones + 9 comodines), usuarios, granja, galpón, lote, y los enums con la deriva |
| Ejecución | `bash backend/scripts/run_tests.sh` | `bash backend/scripts/upgrade_test.sh` |
| Resultado | **229 PASS · 0 FAIL** | **35 PASS · 0 FAIL** |

El estado previo **no se fabrica**: se obtiene migrando hasta el *head* anterior, y
`legacy_state_seeds.py` se limita a **comprobar** que la deriva está ahí. Asumirlo sería
exactamente el error que esta Wave investiga.

```
[legacy] estado de enums previo verificado:
         eventtype sin el 25.º valor · birdtypeenum con 'hatchery' minúscula
```

---

## 2. Matriz

| Change | Fresh DB | Existing DB | Schema Migration | Data Migration | Runtime Test | Status |
|---|---|---|---|---|---|---|
| **`R-40`** · `EGG_RECEPTION_CLASSIFICATION` en `eventtype` | ✅ 25 valores | ✅ **24 → 25** sobre un tipo ya poblado | `j0k1l2m3n4o5` (`ADD VALUE IF NOT EXISTS`) | — | evento creado y releído | **`CERTIFIED`** |
| **`R-41`** · `HATCHERY` en `birdtypeenum` | ✅ | ✅ **4 → 5**; `'hatchery'` histórico conservado | `k1l2m3n4o5p6` | — | lote de incubadora creado y releído; lotes históricos legibles | **`CERTIFIED`** |
| **`R-44`** · permisos de rol | ✅ semillas completas | ✅ **24 → 46** asociaciones, 0 eliminadas | — | `l2m3n4o5p6q7` idempotente | 13 rutas accesibles por rol + 8 prohibidas | **`CERTIFIED`** |
| **`GA-REM-024`** · migración antes de servir | n/a | ✅ *entrypoint* en la imagen | — | — | orden garantizado por construcción | **`CERTIFIED`** |
| `R-48` · contexto de empresa al cambiar | ✅ | ✅ | — | — | el Super Admin crea tras `switch-company` | **`CERTIFIED`** |
| `P0-14` · 14 campos de operación | ✅ | ✅ columnas preexistentes | **ninguna** — verificado contra `information_schema` antes de escribir código | — | 24 tests de ida y vuelta | `CERTIFIED` (Wave 2) |
| `R-26` · contrato de error | ✅ | ✅ sin estado persistente | — | — | 9 tests | `CERTIFIED` (Wave 2) |
| `P0-13` · cambio de contraseña | ✅ | ✅ sin estado persistente | — | — | 11 tests | `CERTIFIED` (Wave 2) |
| `R-32` / `R-51` · inyección de estado | ✅ | ✅ solo contrato | — | — | 15 tests de regresión | **`CERTIFIED`** |
| `GA-REM-009` · volumen de evidencias | ✅ | ⚠ **requiere `docker compose up -d`** para que el volumen se monte; Watchtower recrea el contenedor pero no reconcilia volúmenes declarados después | — | — | — | **acción de operación** (`R-52`) |

---

## 3. `R-52` — el volumen de evidencias exige una acción manual

`docker-compose.yml` declara `avicola-media:/app/media` desde la Wave 1. Watchtower recrea
el contenedor con la imagen nueva, pero **no vuelve a leer el fichero compose**: un
contenedor recreado por Watchtower conserva la definición de volúmenes con la que se creó.

Consecuencia: en la instalación existente, las evidencias seguirán perdiéndose en cada
recreación hasta que alguien ejecute `docker compose up -d` en el servidor.

No es un defecto del código ni un bloqueante de la publicación —el sistema funciona—, pero
sí una **acción de operación obligatoria** para que `GA-REM-009` surta efecto en producción.
Se registra aquí porque es exactamente la clase de cosa que la certificación de instalación
nueva no puede descubrir.

---

## 4. Migraciones aplicadas en el camino de actualización

```
i9j0k1l2m3n4  (punto de partida: instalación existente)
   -> j0k1l2m3n4o5   añade EGG_RECEPTION_CLASSIFICATION a eventtype
   -> k1l2m3n4o5p6   añade HATCHERY a birdtypeenum
   -> l2m3n4o5p6q7   reconcilia los permisos de rol (R-44)
```

Estado antes y después, medido sobre la base:

```
ANTES   head=i9j0k1l2m3n4 · permisos=33 · valores de eventtype=24
DESPUES head=l2m3n4o5p6q7 · permisos=55 · valores de eventtype=25
        birdtypeenum=['BREEDER','BROILER','GRANDPARENT','HATCHERY','hatchery']
        usuarios conservados=6
```

`permisos` incluye los 9 comodines del Super Admin: 24 + 9 = 33 antes, 46 + 9 = 55 después.

> Corregido en la Wave 2.75 tras medirlo sobre el arranque real: este informe cifraba 41 y 50.

---

## 5. Reversibilidad

| Migración | `downgrade` | Motivo |
|---|---|---|
| `j0k1l2m3n4o5` | **no elimina el valor** | PostgreSQL no permite quitar valores de un tipo enumerado. Hacerlo exigiría recrear el tipo y reescribir cada columna que lo usa, con riesgo sobre datos existentes. El valor es aditivo e inocuo |
| `k1l2m3n4o5p6` | ídem | ídem |
| `l2m3n4o5p6q7` | **no revierte** | eliminar las asociaciones dejaría la instalación en el estado que la migración corrige, y no hay forma de distinguir las que añadió de las que un administrador configurara después |

**No se finge reversibilidad.** Las tres son de avance y así están documentadas en su
propio encabezado.

---

## 6. Pérdida de datos

**Ninguna.** Verificado en el camino de actualización:

| Comprobación | Resultado |
|---|---|
| Usuarios conservados y con su rol original | ✅ 6/6 |
| Permisos históricos conservados | ✅ 33/33, cero eliminados |
| Lotes históricos legibles tras el cambio de enum | ✅ |
| Valor `'hatchery'` histórico conservado | ✅ (inerte, pero no se destruye) |
| Roles creados o borrados | 0 |
