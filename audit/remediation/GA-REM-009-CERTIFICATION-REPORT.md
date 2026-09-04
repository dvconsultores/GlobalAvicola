# GA-REM-009 — CERTIFICATION REPORT

| | |
|---|---|
| **GA-REM** | `GA-REM-009` — Persistencia de evidencias y archivos · **Wave** 1 · 2026-09-03 |
| **Estado final** | **`CERTIFIED` (implementación)** — AC01 verificable solo en el entorno desplegado |

## Finding
**P0-6** — Las evidencias adjuntas (`/app/media`) y las exportaciones SAP (`/tmp/sap_exports`) se escribían en el sistema de archivos del contenedor **sin volumen persistente**. Watchtower recrea el contenedor en cada publicación de imagen: **cada despliegue destruía todas las evidencias**, dejando filas en `evidences` apuntando a rutas inexistentes.

## Decisión de arquitectura
**Opción A — volumen nombrado de Docker.** Justificación: §40 del programa desaconseja introducir servicios externos si un volumen resuelve correctamente el problema. Las opciones B (bind mount) y C (almacenamiento de objetos) quedan registradas como alternativas para escala futura.

## Implementation

| Archivo | Cambio |
|---|---|
| `docker-compose.yml` | Volumen nombrado `avicola-media` montado en `/app/media` del servicio `backend`; declaración del volumen; variables `MEDIA_DIR` y `SAP_EXPORT_DIR` inyectadas |
| `frontend/nginx.conf` | `client_max_body_size 12m;` — el backend admite 10 MB y Nginx los rechazaba con 413 a partir de 1 MB |
| `backend/app/integrations/sap/adapter.py` | `ManualSapAdapter.export_dir` pasa de `/tmp/sap_exports` (efímero) a `SAP_EXPORT_DIR`, por defecto `/app/media/sap_exports` — **dentro del volumen** |

## AC — verificación

| AC | Criterio | Resultado |
|---|---|---|
| AC01 | La evidencia sobrevive a un redespliegue | ⚠ **verificable solo en el entorno desplegado** — la configuración es correcta y necesaria; la comprobación empírica requiere recrear el contenedor |
| AC02 | Archivos de hasta 10 MB | ✅ `client_max_body_size 12m` cubre el límite de 10 MB del backend con margen |
| AC03 | El límite del backend se respeta | ✅ `_MAX_SIZE = 10 MB` en `operations/router.py:21` sin cambios; sigue devolviendo 400 |
| AC04 | Evidencia huérfana | ⚠ **`DEFERRED`** — el manejo del archivo inexistente en la descarga se difiere a Wave 2 |
| AC05 | Permisos del volumen | ⚠ verificable en el entorno; el contenedor corre como usuario `avicola` |
| AC06 | **El deployment NO ha sido modificado** | ✅ 0 workflows tocados; `watchtower`, `pull_policy: always` y `:latest` intactos. `git diff --stat docker-compose.yml` → **13 inserciones, 0 eliminaciones** |
| AC07 | Inventario del daño | ⚠ **`DEFERRED`** — requiere consulta contra la base productiva |

## Verificación de EX-01
```
git diff --stat docker-compose.yml   →  13 +++++++++++++, 0 eliminaciones
watchtower / pull_policy / :latest   →  12 referencias, todas intactas
.github/workflows/docker-*.yml       →  0 modificados
```
El cambio es **puramente aditivo**: declara un volumen y tres variables de entorno. No altera el mecanismo de despliegue.

## Regression
`compileall` OK · 176 operaciones OpenAPI · 0 deriva de esquema · `tsc` y `vitest` en verde.

## Final status
**`CERTIFIED`** en cuanto a implementación. AC01, AC05 y AC07 requieren el entorno desplegado; AC04 se difiere explícitamente a Wave 2.
