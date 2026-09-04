# WAVE 2.5 — EXECUTION REPORT

> ### OWNER CLARIFICATION / ENV-01
>
> The currently deployed environment was previously referred to as
> "production" in technical reports.
>
> It is not a real business production environment.
>
> It is a shared development, testing and certification environment
> containing only test/certification data.
>
> No real business production deployment currently exists.
>
> **Anotación añadida el 2026-09-04.** No se ha modificado la fecha, el hallazgo, la
> evidencia ni la decisión de este documento. Reclasificación de urgencia en
> [`ENVIRONMENT_NORMALIZATION_REPORT.md §6`](ENVIRONMENT_NORMALIZATION_REPORT.md).


**Global Avícola** · Compatibilidad de producción · Migración de datos RBAC ·
Certificación final de mortalidad · Preparación de publicación

**Fecha** 2026-09-04 · **Commit base** `bfccdfb` · **Estado** `COMPLETE`

---

# 1. Executive Summary

```
PATH A · instalación nueva ............ 229 PASS · 0 FAIL
PATH B · actualización existente ......  35 PASS · 0 FAIL

R-40 migración de enum ................ CERTIFIED (sobre base existente)
R-41 birdtypeenum ..................... CERTIFIED (sobre base existente)
R-44 reconciliación de permisos ....... CERTIFIED
GA-REM-024 migración antes de servir .. CERTIFIED   ← el bloqueante real
GA-REM-002 RBAC ....................... CERTIFIED
GA-REM-005 mortalidad ................. CERTIFIED   (AC08 enmendado y satisfecho)

Enums auditados ....................... 16 / 16 · 0 derivas nuevas
Esquemas de escritura auditados ....... 49 · 0 de la clase de R-32
Hallazgos nuevos ......................  6  (R-48, R-50, R-51, R-52, R-53, R-49)
Regresiones introducidas ..............  0
P0 abiertos ...........................  0

READY_FOR_RELEASE ..................... YES
READY_FOR_E2E ......................... YES
```

**El hallazgo central de la Wave no es ninguno de los que la motivaron.** Al buscar dónde
colocar la reconciliación de `R-44` apareció que **el despliegue no ejecuta migraciones en
absoluto**: el arranque era `uvicorn` directo, sin `alembic upgrade head` en el Dockerfile,
ni en un entrypoint, ni en compose, ni en el *lifespan*, ni en ningún workflow.

Sin eso, las tres migraciones que esta compatibilidad necesita nunca habrían llegado a
producción. La auditoría ya lo había registrado como `GA-TD-013` y nunca recibió spec.

---

# 2. Baseline de la Wave 2

```
BACKEND SUITE = 211 PASS · 0 FAIL     (base nueva, calendario 2026 y 2028)
GA-REM-002 = IMPLEMENTED ⚠ R-44
GA-REM-005 = PARTIALLY CERTIFIED ⚠ AC08
P0 abiertos = 0
```

La Wave 2 verificó que el código está verde. No verificó que una instalación existente
pudiera actualizarse — que es una pregunta distinta y es la de esta Wave.

---

# 3. `R-40` — el 25.º tipo de evento sobre una base existente

Certificado por el camino que importa. `PATH B` parte de un `eventtype` con **24 valores** y
datos ya escritos; `j0k1l2m3n4o5` lo deja en 25, y el evento se registra y se relee.

El estado previo no se fabrica: se obtiene migrando hasta `i9j0k1l2m3n4`, y
`legacy_state_seeds.py` **comprueba** que la deriva está ahí antes de continuar:

```
[legacy] estado de enums previo verificado:
         eventtype sin el 25.º valor · birdtypeenum con 'hatchery' minúscula
```

Asumirlo habría sido exactamente el error que esta Wave investiga.

**Reversibilidad:** no la hay, y no se finge. PostgreSQL no permite eliminar valores de un
tipo enumerado; el `downgrade` lo documenta en lugar de simularlo.

---

# 4. `R-41` — `birdtypeenum`

Antes de modificar se comprobó si alguna fila usaba el valor histórico. **Ninguna** — no
podía: la aplicación escribe el nombre del miembro, `'HATCHERY'`, y la minúscula nunca fue
escribible desde el código. Eso es lo que hace segura la migración.

`'hatchery'` **se conserva**. Eliminarlo exigiría recrear el tipo y reescribir cada columna
que lo usa, con riesgo sobre datos existentes, para retirar un valor inerte. Se clasifica
`UNUSED_VALUE` y se documenta.

Tras la migración: lote de incubadora creado y releído; lotes históricos legibles.

---

# 5. Auditoría completa de enums

`R-40` y `R-41` compartían escondite: la comprobación de deriva miraba tablas y columnas, no
valores de tipos enumerados. **No basta con auditar los dos conocidos.**

```
Enums auditados ....... 16
MATCH ................. 15
UNUSED_VALUE ..........  1   (birdtypeenum → 'hatchery', deliberado)
DB_VALUE_MISSING ......  0
CODE_VALUE_MISSING ....  0
CASE_MISMATCH .........  0
```

**Ninguna deriva nueva.** La comprobación es ahora permanente en dos planos: `verify.sh`
contrasta contra las migraciones —evita que el defecto entre— y un test contrasta contra la
base real —evita que pase inadvertido en una instalación concreta—.

Detalle en `ENUM_DRIFT_REPORT.md`.

---

# 6. `R-44` — el bloqueante que la Wave 2 dejó abierto

```
SEED  ≠  PRODUCTION DATA MIGRATION
```

Actualizar `dev_seeds.py` sirve a instalaciones nuevas y no toca una base existente. La
reconciliación es una **migración de datos**: `l2m3n4o5p6q7`.

## Fuente normativa

No «lo que haga falta para que pasen los tests», sino, en este orden: `docs/12 §3`
—«Actores y responsabilidades»—, el permiso que ya declara cada ruta, y mínimo privilegio.

## Resultado

```
Asociaciones históricas ....... 24  (+9 comodines del Super Admin)
Tras la reconciliación ........ 46  (+9)
Añadidas ...................... 22
Eliminadas ....................  0
Roles creados o borrados ......  0
Usuarios modificados ..........  0
```

De los 18 permisos que ningún rol concedía, **5 se reconcilian** —los que romperían la
aplicación, encabezados por `masters:read`, que 40 rutas exigen— y **13 siguen siendo
exclusivos del Super Admin** por ser operaciones de administración.

Reconciliar no se convirtió en abrir la mano: el Auditor no recibió **ni una** acción de
escritura, y ocho comprobaciones negativas verifican que cada rol sigue sin poder lo que no
le corresponde.

Detalle en `RBAC_ROLE_PERMISSION_MATRIX.md`.

---

# 7. Reconciliación en producción — el orden

## La condición crítica

No puede existir una ventana donde código nuevo con enforcement atienda tráfico contra
permisos viejos. **Antes de esta Wave esa ventana no solo existía: era permanente**, porque
nada aplicaba las migraciones.

## `GA-REM-024`

Un *entrypoint* en la imagen:

```sh
set -e
alembic upgrade head
exec "$@"
```

- `set -e` — si la migración falla, el contenedor **no sirve**. Servir con el esquema
  equivocado corrompe datos; caerse ruidosamente es preferible.
- `exec` — el servidor hereda el PID 1 y `docker stop` sigue siendo limpio.
- `ENTRYPOINT` — el bot de Telegram, que comparte imagen, pasa también por la migración,
  que es idempotente y por tanto inocua para él.

## `EX-01` intacto

Watchtower, `:latest`, `pull_policy`, *triggers* y workflows **sin cambios**. Lo único que
cambia es lo que el contenedor hace en su primer segundo, que es responsabilidad de la
imagen y no de la estrategia de despliegue.

**No se eligió el mecanismo por comodidad**: se eligió una migración de datos transaccional
*después* de demostrar el orden con evidencia —Dockerfile, entrypoint, compose, workflows—,
no de suponerlo.

---

# 8. `GA-REM-002` — certificación

| Requisito | Resultado |
|---|---|
| `RBAC CODE PASS` | ✅ 177/177 rutas con decisión declarada |
| `FRESH INSTALL PASS` | ✅ 229 PASS |
| `EXISTING DB UPGRADE PASS` | ✅ 35 PASS desde el estado anterior a la Wave 2 |
| `ROLE MATRIX PASS` | ✅ 29 permisos con destino justificado |
| `NON-SUPERADMIN ACCESS PASS` | ✅ 13 comprobaciones de acceso real por rol |
| `NEGATIVE PERMISSION TESTS PASS` | ✅ 8 comprobaciones de denegación |

**`IMPLEMENTED` → `CERTIFIED`.**

---

# 9. `GA-REM-005` / `AC08` — revisión de alcance

## La Wave 2 se equivocó, y se corrige

La Wave 2 difirió `AC08` afirmando que «ningún hallazgo lo requiere». **Era falso:**

| Fuente | Qué dice |
|---|---|
| `docs/02-functional-spec.md:516` | «Mortalidad > umbral **configurable**» |
| `audit/06_PROCESS_COVERAGE.md:259` | «implementado con umbral **fijo** 3 % / 8 % en código» — hueco registrado |

El requisito existía y la auditoría lo había señalado.

## Lo que sí era sobrealcance

Ninguna fuente pide alcance **por empresa**. Esa precisión la añadió la propia spec de
remediación. Sobrealcance **parcial**: un requisito legítimo con una dimensión inventada.

| Elemento | Disposición |
|---|---|
| Umbral **configurable** | **implementado** vía `Settings`, el mismo mecanismo que el resto del sistema. Sin esquema, sin migración, sin modelo nuevo |
| Alcance **por empresa** | `REMEDIATION_SPEC_OVERREACH` → `GA-REM-019`, mejora opcional |

La enmienda queda en la propia spec con AC original, genealogía, análisis y fecha. No se
sustituyó el AC por otro más fácil: se retiró lo que nunca debió estar y se satisfizo lo que
la fuente exige.

---

# 10. `GA-REM-005` — certificación final

`tests/test_mortality.py` — **16 PASS · 0 FAIL**. Los 9 AC vigentes verificados.

**`PARTIALLY CERTIFIED` → `SPEC_AMENDED` → `RETESTED` → `CERTIFIED`.**

---

# 11. `R-43` — regresión de autenticación

Ciclo completo fijado como regresión permanente: `login → access → refresh → nuevo access →
petición autenticada`, con normalización de `sub`, búsqueda de usuario, rol, compañía y
vista.

Sesión larga **sin esperar media hora**: se emite un token de acceso ya caducado, se
comprueba que se rechaza con 401 y que el de refresco permite continuar. Y un `sub` no
numérico —el defecto original— produce un 401 limpio, no un error de base de datos.

**5 tests · PASS.**

---

# 12. `R-32` — regresión de inyección de estado

Siete campos parametrizados (`status`, `approved_by_id`, `reviewed_by_id`,
`registered_by_id`, `company_id`, `version`) rechazados con 422 en `PUT /operations/{id}`, y
la vía legítima —`POST /{id}/submit`— sigue funcionando.

**10 tests · PASS.**

---

# 13. Auditoría de esquemas de escritura

`R-32` obligaba a mirar la clase, no la instancia. Introspección de los **49** esquemas
`*Create` / `*Update` / `*Patch`:

```
Con campos gestionados por el flujo o el sistema .... 0   ← la clase de R-32 está cerrada
Con contraseñas en esquemas de edición .............. 0   ← P0-13 cerrado por contrato
Con exposición indebida .............................. 1   (R-50)
```

Un barrido automático encontró **`R-51`**: `LotUpdate` exponía `status`, de modo que un
`PUT` podía cerrar un lote saltándose `close_lot` —sin precondición, sin resumen, sin
`end_date`— y **reabrir** uno cerrado, con lo que volvían a admitirse movimientos contra él
(`BR-07`). Corregido: el estado del lote cambia por su transición.

Detalle en `UPDATE_SCHEMA_SECURITY_MATRIX.md`.

---

# 14. Instalación nueva — `PATH A`

```
PostgreSQL vacío → alembic upgrade head → semillas → aplicación → tests
229 PASS · 0 FAIL · 35 skipped (la suite de actualización, correctamente omitida)
```

---

# 15. Actualización de instalación existente — `PATH B`

**El test más importante de la Wave.**

```
esquema i9j0k1l2m3n4  (head anterior a la Wave 2)
  → matriz de permisos histórica · usuarios · granja · galpón · lote
  → enums con la deriva, verificada y no supuesta
  → alembic upgrade head   (R-40 · R-41 · R-44)
  → aplicación nueva
  → 35 PASS · 0 FAIL
```

```
ANTES   head=i9j0k1l2m3n4 · permisos=33 · eventtype=24 valores
DESPUÉS head=l2m3n4o5p6q7 · permisos=55 · eventtype=25 valores
        birdtypeenum=['BREEDER','BROILER','GRANDPARENT','HATCHERY','hatchery']
        usuarios conservados=6
```

---

# 16. Regresión backend

| | Wave 2 | **Wave 2.5** |
|---|---:|---:|
| Recolectados (PATH A) | 211 | **229** |
| PASS | 211 | **229** |
| FAIL | 0 | **0** |
| PATH B | — | **35 PASS** |

+18 tests nuevos: regresión de seguridad (15) y `AC08` (3).

---

# 17. Regresión temporal 2028

```
calendario 2028-06-15 → 229 PASS · 0 FAIL
```

`R-28` sigue cerrado.

---

# 18. Regresión frontend

```
TypeScript ....... PASS
Vitest ........... PASS 61/61
Paridad i18n ..... PASS ES=866 EN=866
```

Sin cambios en el frontend esta Wave.

---

# 19. Integridad de base de datos

```
Deriva de tablas .... 0
Deriva de columnas .. 0
Deriva de enums ..... 0   ← tercera dimensión, añadida en la Wave 2
Heads de Alembic .... 1   (l2m3n4o5p6q7)
```

Tres migraciones nuevas en la Wave 2.5: dos de esquema (Wave 2, ahora certificadas sobre
base existente) y una de datos. Ninguna reversible, y las tres lo documentan.

---

# 20. Release blockers

| ID | Blocker | Reason | Resolution | Status |
|---|---|---|---|---|
| `GA-TD-013` / `GA-REM-024` | El despliegue no ejecutaba migraciones | ninguna migración habría llegado a producción | *entrypoint* que migra antes de servir, dentro de `EX-01` | **RESUELTO** |
| `R-44` | Catálogo de permisos de producción incompleto | usuarios legítimos con 403 en casi toda la aplicación | migración de datos idempotente | **RESUELTO** |
| `R-48` | `switch-company` sin efecto | con RBAC activo, nadie podía crear lotes | el claim se honra solo para quien ya opera entre compañías | **RESUELTO** |

**Cero bloqueantes abiertos.**

Una **condición de operación**, que no bloquea:

| ID | Acción | Motivo |
|---|---|---|
| `R-52` | ejecutar `docker compose up -d` una vez en el servidor | Watchtower recrea el contenedor pero no relee el fichero compose: el volumen `avicola-media` de la Wave 1 no se monta hasta entonces, y `GA-REM-009` no surte efecto |

---

# 21. Estado de P0

| Momento | P0 abiertos |
|---|---:|
| Auditoría inicial | 12 |
| Tras Wave 1 | 8 |
| Tras Wave 1.5 | 10 |
| Descubiertos durante Wave 2 | +4 |
| Cerrados en Wave 2 | 14 |
| **Tras Wave 2.5** | **0** |

Los 6 hallazgos de esta Wave son todos `PRE_EXISTING_NEWLY_DISCOVERED`.
**`INTRODUCED_BY_REMEDIATION`: 0.**

| ID | Hallazgo | Sev. | Estado |
|---|---|---|---|
| `R-48` | `switch-company` sin efecto sobre el contexto | P1 | **corregido** |
| `R-51` | `LotUpdate` exponía `status` (clase de `R-32`) | P1 | **corregido** |
| `R-50` | `company_id` fijable desde el cliente en 19 esquemas de maestros | P2, mitigado por RBAC | abierto → `GA-REM-019`, **prerrequisito de `OD-04`** |
| `R-52` | El volumen de evidencias requiere `docker compose up -d` | P2 | acción de operación |
| `R-49` | Umbrales de temperatura y humedad fijos | P3 | abierto → `GA-REM-019` |
| `R-53` | El orden de migración supone un solo contenedor | P3, condicional | abierto → `GA-REM-019` |

---

# 22. E2E readiness

```
READY_FOR_E2E = YES
```

`GA-REM-016` estaba condicionada a `R-44`, que está resuelto. Certificar procesos E2E ya no
se haría contra un sistema cuyo catálogo de permisos en producción no admite a los roles que
esos procesos requieren.

La cobertura E2E **no se movió**: sigue en `12 / 60 = 20 %`. No se ejecutó E2E y aumentarla
sin certificación real sería falsear el indicador.

---

# 23. Release readiness

```
READY_FOR_RELEASE = YES
```

Una instalación existente puede actualizarse de forma segura, **demostrado por el camino de
actualización y no por analogía con la base nueva**. Las diez preguntas de compatibilidad
están respondidas con evidencia en `RELEASE_COMPATIBILITY_REPORT.md`.

`READY_FOR_E2E` y `READY_FOR_RELEASE` se evaluaron por separado, como corresponde. Aquí
coinciden en afirmativo.

**No se ha desplegado, ni publicado, ni etiquetado, ni hecho push.** La decisión de publicar
es posterior a esta Wave.

---

# 24. Recomendación para la Wave 3

| # | Trabajo | Motivo |
|---|---|---|
| 1 | **Publicar**, con `R-52` en el mismo despliegue | la compatibilidad está certificada; retrasarla acumula riesgo sin reducirlo |
| 2 | `GA-REM-016` — certificación E2E y de procesos | desbloqueada; único camino al nivel de madurez 4 |
| 3 | `GA-REM-011` — 8 desajustes de contrato restantes | diferidos por alcance desde la Wave 1 |
| 4 | **`GA-TD-039` / `GA-TD-040`** — observabilidad y respaldo | **`PRE-PRODUCTION`.** Con `EX-01`, la falta de observabilidad es lo que hace que un despliegue defectuoso pase inadvertido. `GA-TD-013` lo prueba: el despliegue llevaba meses sin aplicar migraciones y nadie lo supo |
| 5 | `GA-REM-021` (agua) · `GA-REM-022` (KPI) | en backlog; no compiten con ningún P0 |
| 6 | `GA-REM-019` — deuda P2/P3 | acumula `R-49`, `R-50`, `R-53` y la mejora opcional de `AC08` |
| 7 | `GA-REM-017` — SAP real | `BLOCKED_EXTERNAL` + `OD-02` |

---

# 25. Evidence index

| Documento | Contenido |
|---|---|
| `PRODUCTION_UPGRADE_COMPATIBILITY_MATRIX.md` | los dos caminos, cambio por cambio |
| `RBAC_ROLE_PERMISSION_MATRIX.md` | los 29 permisos, los 18 huérfanos, la fuente normativa |
| `RELEASE_COMPATIBILITY_REPORT.md` | las diez preguntas de compatibilidad |
| `ENUM_DRIFT_REPORT.md` | los 16 enums, clasificados |
| `UPDATE_SCHEMA_SECURITY_MATRIX.md` | los 49 esquemas de escritura |
| `GA-REM-024-CERTIFICATION-REPORT.md` | migración antes de servir |
| `GA-REM-002-003-CERTIFICATION-REPORT.md` | addendum de Wave 2.5, `R-44` y `R-48` |
| `GA-REM-005-CERTIFICATION-REPORT.md` | addendum de Wave 2.5, enmienda de `AC08` |
| `specs/remediation/GA-REM-005-…md` | enmienda formal de spec |
| `specs/remediation/GA-REM-024-…md` | spec nueva |
| `backend/scripts/upgrade_test.sh` · `seeds/legacy_state_seeds.py` · `tests/test_upgrade_path.py` | el camino de actualización, reproducible |
| `BACKEND_TEST_BASELINE_RUN_01.md` | **congelado, no sobrescrito** |
