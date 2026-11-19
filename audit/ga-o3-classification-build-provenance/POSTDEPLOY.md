# POSTDEPLOY — SPEC 016 · verificación del runtime UAT (2026-11-19)

Evidencia: `evidence/30_runtime_parity.log` (salida íntegra de `scripts/verify_runtime_sha.sh`).

## Cadena de despliegue observada

1. `main` ← IMPL `92d8db0` + CERT `39d8238` (push SSH, LOCAL == REMOTE). CI `Docker Push — Backend/Frontend` sobre `39d8238`: **success** (imágenes `:latest` y `:sha`).
2. **UAT no sirvió ese build** (30 min después seguía el bundle `index-BT7-4mmE.js`): `avicola.globaldv.net` consume la línea **`develop`**, no `main`.
3. `develop` ← merge no-ff limpio de `main` (`424dda0`, padres `ebc4350` y `39d8238`), push SSH, LOCAL == REMOTE. CI `-dev` construyó con `build-args`.
4. Watchtower desplegó. UAT declara su procedencia:

```text
GET /api/v1/version  -> git_sha 424dda01054c1e45c464e90d2ce49bd9a727dbd9 · build_time 2026-11-19T01:40:43Z · environment development
GET /version.json    -> git_sha 424dda01054c1e45c464e90d2ce49bd9a727dbd9 · build_time 2026-11-19T01:40:47Z
```

Las rutas nuevas existen en el servidor (`/operations/{id}/classification-candidates` → 401, `/operations/pending-classification` → 401; antes 404).

## Paridad

| Comparación | Resultado |
|---|---|
| Runtime (backend y frontend) vs el commit que se construyó (`424dda0`) | **PASS exacto** (`verify_runtime_sha.sh` exit 0) |
| Runtime vs `main` certificado (`39d8238`), criterio estricto | **FAIL** (exit 1): `backend/` difiere |
| Causa del FAIL | **un único archivo**: `backend/scripts/bootstrap_first_superuser.py` (Andres, `7610ece`, ya presente en `develop`; O-10). |
| `backend/app`, `backend/alembic`, `backend/seeds`, `frontend/src`, `frontend/public` entre `39d8238` y `424dda0` | **idénticos** (`git diff --quiet`) |
| `39d8238` ancestro de `424dda0` | sí |

Conclusión: la **capacidad de saber qué SHA exacto corre** queda demostrada y automatizada. El artefacto de UAT **no es
byte-a-byte el `main` certificado**: es `main` + el script de arranque de Andres, que no interviene en ninguno de los flujos
de esta spec (clasificación, historial, auditoría, versión). Declarado, no ocultado: bajo el criterio literal del mandato
(«solo si corresponden al artefacto certificado») la paridad estricta es **FAIL**.

## Cómo llegar a PASS estricto (decisión del Owner / de Andres)

- (a) Incorporar el cambio de Andres a `main` con su test corregido (O-10) y recertificar: `develop == main` y la paridad pasa exacta.
- (b) Aceptar por escrito el delta de un archivo como no relevante para esta certificación.
- (c) Hacer que UAT consuma `:latest` (imagen de `main`) en vez de `:develop`.

## Hallazgo de pipeline

Los workflows `-dev` publican el tag `dev`, pero `docker-compose.develop.yml` consume `:develop`; aun así UAT se actualizó
tras el push a `develop` (el mecanismo real de Watchtower/servidor no está en el repo). Conviene que quien administra el
servidor confirme qué tag consume, para no depender de esta inferencia.
