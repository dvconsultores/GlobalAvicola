# PROCESS-07 — REVISIÓN → CORRECCIÓN → APROBACIÓN

| | |
|---|---|
| **Proceso** | `P-07` · tercero del orden de certificación de `GA-REM-016` |
| **Estado final** | **`CERTIFIED`** |
| **Fecha** | 2026-09-04 · **Wave** 3 |

## Spec

`GA-REM-016` (unidad de certificación) · `specs/global-avicola/spec.md §4.10` ·
`docs/12-approval-workflow.md` · `GA-REM-006` y `GA-REM-007`, ambas `CERTIFIED`.

Reglas vigentes: **`RR-01`** (la corrección se aplica en el acto; el registro sigue
requiriendo aprobación) y **`RR-03`** (`BR-14` configurable por paso, segregación por
defecto). `RC-01` y `RC-03` **no se reabren**.

## Requisitos

`spec.md §4.10`: bandeja de revisión, corrección auditada con valor original y corregido,
devolución con observaciones, aprobación multinivel, rechazo con motivo obligatorio.

`BR-09` (toda corrección es auditada) · `BR-13` (nada va a SAP sin aprobación) ·
`BR-14` (segregación) · `BR-15` · `BR-16`.

## Fuentes del cliente

`Recomendación central.pdf` §18 —`OBSERVADO ↓ CORREGIDO ↓ APROBADO`, «Solo el estado
APROBADO puede viajar a SAP»— y §26 —«corregir antes de aprobar»—.

## Actores

Operador (registra) · Supervisor (revisa y corrige) · Aprobador (aprueba o rechaza).
Tres identidades reales, no una.

## Precondiciones

Base de pruebas aislada, migrada por el entrypoint real y sembrada de forma determinista.
Fechas relativas al reloj (`R-28`).

## Datos de prueba

Evento de `feed_registration` con `observations` conocidas, registrado por el **operador**,
enviado a revisión y tomado por el supervisor.

## Happy path

```
operador registra          -> registered
operador envía a revisión  -> pending_review
supervisor toma el caso    -> in_review
supervisor corrige         -> corrected  · el DATO cambia
aprobador aprueba          -> approved   · con aprobador registrado
```

Verificado: el `observations` del evento pasa de «valor original del operador» a «valor
corregido por el supervisor». Eso era `P0-2`, y es lo que distingue corregir de anotar que
se corrigió.

## Pruebas negativas

| Caso | Resultado |
|---|---|
| El operador aprueba su propio registro | **403** — `BR-14` (`RR-03`) |
| Corregir `status`, `approved_by_id` o `company_id` | **400** ×3 — lista blanca |
| Fijar el estado con `PUT /operations/{id}` | **422** — `R-32` |
| El operador aprueba o rechaza | **403** ×2 |

## RBAC

`approvals:approve` y `approvals:reject` exclusivos del rol Aprobador. El operador tiene
`operations:create/read/update` y nada más. Verificado en ejecución.

## Aislamiento entre inquilinos

Corregir, revisar y aprobar un evento de otra empresa: **rechazados los tres**
(`tests/security/test_multitenant_isolation.py`).

## Pertenencia de claves foráneas

`event_id` se resuelve por el servicio con filtro de compañía. Un evento ajeno se comporta
como inexistente.

## Persistencia

El valor corregido se escribe en el dato; `original_value` lo **lee el servidor** del propio
campo, ignorando lo que declare el cliente. `version` avanza. Todo verificado tras releer
por API.

## Balances

No aplica: el ciclo de aprobación no altera cantidades.

## Reglas de negocio

`BR-09` ✅ · `BR-14` ✅ · `BR-15`/`BR-16` ✅ (la corrección se rechaza sobre estados
posteriores a la aprobación) · `RR-01` ✅ (corregido ≠ aprobado, `approved_by_id` nulo).

## Auditoría

Más de una acción registrada por evento, con tipos distintos. **Sin secretos**: se comprueba
que el volcado no contiene `password`.

## Frontend

La sesión se establece por la interfaz —formulario de login real, redirección incluida— y
la ausencia de sesión se verifica navegando a una ruta protegida. El ciclo se ejerce
después por API con esa misma sesión: lo que se certifica es el proceso, no un widget.

## Backend · Base de datos

`app/review/service.py` (`SegregacionMixin`) · `app/corrections/service.py` (lista blanca y
conversión tipada) · estado y auditoría releídos de la base tras cada transición.

## Evidencia

`e2e/proceso-03-revision-correccion-aprobacion.spec.ts` — **7/7 PASS**.
Reproducible con `bash scripts_e2e.sh --project=procesos proceso-03`.

## Huecos abiertos

| Hueco | Sev. | Destino |
|---|---|---|
| Corregir `event_date` no revalida `BR-19` (`R-45`) | P2 | `GA-REM-016` / `GA-REM-019` |
| No se puede corregir un submovimiento (`R-46`) | P2 | `GA-REM-019` |
| Una corrección desde `REGISTERED` deja el evento aprobable sin pasar por revisión | P2 | `GA-REM-019` |

Ninguno bloquea los AC del proceso: los tres son limitaciones conocidas y trazadas, no
fallos del ciclo certificado.

## Estado final

**`CERTIFIED`** — el ciclo funciona de extremo a extremo, la corrección corrige, la
segregación se aplica y la auditoría es evidencia.
