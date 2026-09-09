# PRE-FLIGHT DE INTEGRIDAD · WAVE B tranche 4 (2026-09-09) · base `5b64104`

## A. Severidad oficial de `R-163` — normalizada

El cierre del tranche 3 dejó `R-163` como «P2 (P1 en `POST /lots` con actor de empresa)». Una severidad
no puede ser dos. Criterio aplicado: **el del propio backlog**, leído de sus precedentes y no inventado:

| Precedente | Severidad | Qué era |
|---|:--:|---|
| `R-160` | **P1** | escrituras productivas (`operations`) sin alcance de unidad para el actor de empresa |
| `R-139` | **P1** | escrituras y lecturas de dato productivo fuera del alcance de empresa (`OD-14.c/d`), confirmadas |
| `H360-A01` | P2 (PLAUSIBLE) | atajos `is_super_admin` **sin verificar** |
| `R-159` · `R-162` | P2 | lecturas sin predicado de unidad, dentro de la misma empresa |

Evidencia real de `R-163` (matriz previa del tranche 3 §1, evidencia §2, pruebas `l02`…`l05`):
`POST /lots` creaba dato productivo en **cualquier** cadena, apagada o no concedida, para **cualquier** actor
de empresa (clase `AC-C05`, la misma de `R-160`); la autoridad global escribía en unidades apagadas en cinco
superficies; y la autoridad global sin contexto creaba lotes **sin empresa** (`company_id NULL`), que es la
clase de `R-139`. Dos de esas tres clases son P1 en el backlog. **`R-163` = P1.** No se reabre
funcionalmente: sigue `CERRADO` (técnico); solo cambia la severidad registrada y los recuentos.

## B. `lots.company_id IS NULL` — verificación de datos

| Paso | Resultado |
|---|---|
| Prevención | **CERRADA** en `ab71b20` (`AC-L05`: sin contexto → `403`; `S7` la sujeta) |
| Modelo | `Lot.company_id` es `nullable=True` (`masters/models.py`): la base de datos **admite** la fila huérfana; la prevención es de aplicación, no de esquema → hallazgo nuevo `R-164` |
| Consulta en runtime | `SELECT count(*) FROM lots WHERE company_id IS NULL` contra la base configurada (`DATABASE_URL`, host remoto; credenciales no expuestas): **`TimeoutError`** — no alcanzable desde este entorno |
| Estado | **`BLOCKED_RUNTIME`** · recuento **`UNKNOWN`** · **no se infiere cero** · **ningún dato limpiado ni tocado** |
| Base de pruebas | la base aislada (`pgserver`) se siembra en cada ejecución y no es dato histórico: no sirve de evidencia |

Clasificación pendiente de ejecutar la consulta en un entorno certificable: `LEGITIMATE_BY_SPEC` (ninguna: la
spec no admite lotes sin empresa) · `TEST/FIXTURE` · `INVALID_HISTORICAL` · `UNKNOWN`. Hasta entonces la deuda
de datos es **desconocida**, no cero.

## C. Hallazgos nuevos registrados (no remediados aquí)

| ID | Sev. | Título | Evidencia | Ola |
|---|:--:|---|---|:--:|
| `R-164` | P2 | `lots.company_id` nulable sin restricción de esquema; deuda de datos huérfanos **`UNKNOWN`** (`BLOCKED_RUNTIME`) — exige migración (`NOT NULL` tras verificar datos) y decisión sobre filas inválidas si existen | `masters/models.py` · este documento §B | B |
| `R-165` | P2 | las acciones del plano de revisión (`review/start|return|complete`, `approvals/approve|reject`) no exigen la **habilitación** de la unidad a la autoridad global (`_ambito_de_unidad` devuelve `[]` para `is_super_admin`): misma clase que `R-163` en `lots`; el actor de empresa ya queda fuera por `unidades_efectivas` | `review/service.py:77-99, 360-383, 561-580` | B |
| `R-166` | P3 | `approve` y `reject` sobre el mismo evento `CORRECTED` no se excluyen entre sí (estado leído sin bloqueo; el último `flush` gana): carrera de decisión final; no pertenece a la continuidad de estados de `R-135` | `review/service.py:423-470` | B |

## D. Recuento revalidado (ver `WAVE_B_DEPENDENCY_AND_EXECUTION_MATRIX.md §9`)

`19 + R-164 + R-165 + R-166 = 22` · cerrados 5 · `R-163` cuenta como P1.
