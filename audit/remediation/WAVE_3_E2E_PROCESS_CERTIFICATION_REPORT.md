# WAVE 3 — GA-REM-016 · E2E & PROCESS CERTIFICATION

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


**Global Avícola** · 2026-09-04 · **Commit base** `bfccdfb` · **Estado** `COMPLETE`

---

# 1. Executive Summary

```
GATE MULTIEMPRESA (obligatorio, previo)  12/12 PASS
  Endpoints de mutación auditados ......... 90
  FK enviables por el cliente ............. 26  (22 tenant-scoped)
  Escrituras entre inquilinos encontradas .. 3  ← R-59 y dos ampliaciones de R-42

CERTIFICACIÓN DE PROCESOS
  Orden de GA-REM-016 ..................... 3 de 9 pasos CERTIFIED
  Taxonomía P-01…P-15 ..................... 15 evaluados · 1 CERTIFIED · 9 PARTIAL · 5 READY_FOR_E2E
  E2E de procesos ......................... 21/21 PASS

SUITES E2E (AC01)
  Descubiertas ............................ 59 tests en 5 ficheros
  Heredada, primera ejecución ............. 15 PASS · 23 FAIL

REGRESIÓN
  Backend ................................. 265/265 PASS  (2026 y 2028, idéntico)
  Frontend ................................ tsc PASS · vitest 61/61 · i18n 866=866
  Deriva de tablas/columnas/enums ......... 0 / 0 / 0 · 1 head

Hallazgos nuevos ......................... 4  (R-59 P1 · R-60, R-61, R-62 P2/P3)
Regresiones introducidas ................. 0
READY_FOR_RELEASE ........................ NO  (sin cambio: falta copia verificada)
```

**El gate obligatorio encontró que `R-42` se había resuelto a medias.** La corrección de la
Wave 2 cubrió `lot_id`; el resto de claves foráneas estructurales seguía sin comprobarse.
Tres escrituras entre inquilinos eran posibles el día que empezó esta Wave.

---

# 2. Spec que gobierna

`GA-REM-016`. Este prompt organiza la ejecución; **la spec define el comportamiento**.

| Aspecto | Lo que dice la spec | Lo que se hizo |
|---|---|---|
| Unidad de certificación | proceso de negocio, taxonomía propia | ✅ 15 procesos `P-XX`, no la codificación del cliente |
| Orden | 9 pasos por dependencia del dominio | ✅ ejecutados los 3 primeros, en ese orden |
| Piloto | «Recepción de aves» (paso 1) | ✅ |
| Estados | `NOT_STARTED`…`CERTIFIED` | ✅ los de la spec, no otros |
| `AC04` | el primer proceso alcanza `CERTIFIED` | ✅ los tres primeros |

**Desviaciones respecto de la spec: 0. Enmiendas de spec requeridas: 1** — `GA-REM-002`,
activada formalmente desde `GA-REM-016` (§17).

---

# 3. Baseline de entrada

```
READY_FOR_E2E = YES          (Wave 2.75)
READY_FOR_RELEASE = NO       (falta pg_dump/pg_restore verificado)
```

Pendientes operativos, mantenidos aparte y **no ejecutados**: copia de seguridad
(`GA-TD-040`), `R-52` (activación del volumen), `R-58` (verificación con Docker real).

---

# 4. Pre-flight

```
Backend .................. 265/265 PASS
TypeScript ............... PASS
Vitest ................... 61/61
Paridad i18n ............. ES=866 EN=866
Cadena Alembic ........... 1 head
Deriva tablas/columnas ... 0
Deriva de enums .......... 0
Guardas de producción .... PASS  (avicolav2 rechazada)
```

Todo verde. Ningún fallo que clasificar antes de continuar.

---

# 5. Taxonomía de procesos

15 procesos (`audit/06_PROCESS_COVERAGE.md`, `processCatalog.ts`). **`processCatalog.ts` no
se modificó**: la documentación del cliente es fuente de validación de cobertura, no una
estructura a adoptar.

El orden de certificación se tomó de `GA-REM-016`, no de este prompt.

---

# 6. Clasificación de recursos por inquilino

`TENANT_RESOURCE_CLASSIFICATION.md` — 47 tablas:

```
TENANT_SCOPED, company_id obligatorio ..... 10
TENANT_SCOPED por su padre ................ 12
TENANT_SCOPED con company_id anulable ..... 13   (catálogos compartibles)
GLOBAL .....................................  6
SYSTEM .....................................  2
```

**No se aplicó filtro de compañía a todo.** Los catálogos con `company_id` anulable admiten
uso compartido por diseño; bloquearlos sería un defecto, no una protección. La raza
*Ross 308* es la misma para todas las empresas.

---

# 7. Auditoría de escrituras multiempresa

```
Endpoints que mutan estado ................ 90
FK enviables por el cliente ............... 26
Tenant-scoped ............................. 22
Que exigen pertenencia .................... 6
```

Descubiertas **por introspección** de esquemas Pydantic cruzada con las claves foráneas de
SQLAlchemy. No por lista escrita a mano — que es exactamente como `R-42` sobrevivió a la
Wave 2.

Matriz completa en `MULTITENANT_WRITE_ISOLATION_MATRIX.md`.

---

# 8. Pertenencia de claves foráneas

Lo que el gate encontró el primer día:

```
POST /operations     {farm_id:  <granja de la empresa B>}  -> 201
POST /operations     {house_id: <galpón de la empresa B>}  -> 201
POST /masters/houses {farm_id:  <granja de la empresa B>}  -> 201
```

`AC05` de `GA-REM-002` se había verificado sobre **lecturas** y sobre `lot_id`. Las demás
referencias estructurales quedaron fuera.

**`GA-REM-002` se activó formalmente** con `AC10` (pertenencia en escritura) y `AC11` (la
comprobación es única y compartida). La implementación vive en `app/tenancy.py`, en un solo
sitio: *una regla de aislamiento aplicada en un sitio y ausente en otro no es una regla, es
una casualidad.*

**`R-59`** *(nuevo, P1)*: un maestro hijo admitía un padre de otra empresa
(`houses.farm_id`). Corregido en `MasterService`, en creación **y** en edición: mover un
maestro bajo un padre ajeno es la misma escritura entre inquilinos que crearlo ahí.

---

# 9. Regresión de `R-42`

`R-42` no es «falta un filtro de compañía». Es:

```
CROSS-TENANT WRITE INTEGRITY VIOLATION
```

El gate lo verifica por su **efecto**, no por el código de respuesta: mide el saldo de aves
del lote de la empresa B antes y después del intento de escritura de la A.

```
✅ el intento se rechaza
✅ el saldo del lote ajeno no cambia
✅ no se crea fila
✅ no se escribe auditoría
```

Un rechazo que deja rastro sigue siendo una escritura.

---

# 10. `R-48` / `R-54`

Certificados como **un solo flujo**, no por separado:

```
login super admin → switch A → operar en A → refresh → sigue en A
                  → switch B → operar en B → refresh → sigue en B
```

- El lote y el maestro creados tras el cambio pertenecen a la empresa seleccionada.
- El contexto sobrevive a la renovación (`R-54`).
- Un usuario normal que reclama otra empresa en el token: **ignorado**.
- Un usuario normal que intenta `switch-company`: **403**.
- Super Admin hacia una empresa inexistente: **404**.

Fuente de verdad única: `get_current_user`. Un test lo fija sobre el propio código.

---

# 11. Matriz de certificación

`PROCESS_CERTIFICATION_MATRIX.md`.

```
Procesos totales ....... 15
Evaluados .............. 15
CERTIFIED ..............  1   (P-07)
PARTIAL ................  9
READY_FOR_E2E ..........  5
E2E_FAILED .............  0
BLOCKED_BY_DEFECT ......  0
```

Del orden de `GA-REM-016`: **3 de 9 pasos certificados**.

## Por qué solo P-07 alcanza `CERTIFIED`

Los pasos 1 y 2 del orden —recepción y control diario— son **capacidades transversales**:
atraviesan `P-01`…`P-06` sin agotar ninguno. Un proceso de etapa incluye además recolección
de huevo, incubación o cierre de lote, que no se han ejercitado de extremo a extremo.

`P-07` es el único de los 15 cuyo alcance coincide exactamente con un proceso certificado.

Declarar `P-01 CERTIFIED` por transitividad inflaría el recuento y sería justo lo que `AC05`
prohíbe. La distinción es incómoda y deliberada.

---

# 12. Proceso piloto

**Recepción de aves** (paso 1 del orden). 7/7:

autenticación · happy path UI+API+BD (1 000 aves en dos sexos) · `BR-08` · `BR-19` con
fecha **relativa** · autorización · auditoría · aislamiento.

Estable a la primera. Sin defecto sistémico que obligara a detener la ejecución (§36).

---

# 13. Procesos restantes

| Paso del orden | Estado | Motivo |
|---|---|---|
| 2 · Control de producción diario | **`CERTIFIED`** | 7/7 |
| 3 · Revisión → Corrección → Aprobación | **`CERTIFIED`** | 7/7 |
| 4–7 · huevo fértil, incubación, pollitos, engorde | `READY_FOR_E2E` | dependencias resueltas; sin E2E ejecutado |
| 8 · Consolidación y preparación SAP | `PARTIAL` | solo frontera interna (`GA-REM-010`); `GA-REM-017` `BLOCKED_EXTERNAL` |
| 9 · Trazabilidad generacional | `PARTIAL` | ⚠ `R-60` |

---

# 14. Cobertura del requerimiento del cliente

Insumo de `GA-REM-020` (`FUNCTIONAL_COVERAGE_MATRIX.md`):

```
COVERED ........ 57   (59 %)
PARTIAL ........ 25   (26 %)
ABSENT ..........  5   ( 5 %)
OUT_OF_SCOPE ....  6   ( 6 %) + 13 procesos LIVIANAS
NOT_VERIFIABLE ..  2   ( 2 %)
```

Dos procesos certificados quedan con **cobertura parcial** pese a su E2E en verde:

| Proceso | Hueco | Consecuencia |
|---|---|---|
| Control diario | consumo de agua (`GA-REM-021`) | `docs/02 §3.14` lo enumera; `GA-REM-016` no lo incluye en el alcance del proceso. Se registra la cobertura parcial en lugar de ocultarla. **No se implementa**: `GA-REM-021` no está autorizada en esta Wave |
| `P-15` Reportes y KPI | KPI incompletos (`GA-REM-022`) | entregable separado, no AC de un proceso certificado |

```
PROCESS E2E PASS  ≠  CLIENT COVERAGE COMPLETE
```

---

# 15. Cobertura E2E de requisitos

**Denominador vigente: 60** (Functional Baseline V1.1), no los 56 de la auditoría inicial.

```
Requisitos aplicables ......... 60
E2E certificados .............. 21
Parciales ..................... 18
Sin cobertura E2E ............. 21

E2E COVERAGE:  21 / 60 = 35 %
```

Antes de esta Wave: **12 / 60 = 20 %**, y esos 12 eran una estimación documental, no una
medición: **cero pruebas E2E se habían ejecutado nunca**. Los 21 de ahora corresponden a
casos que se ejecutan y pasan.

`BACKEND PASS ≠ E2E CERTIFIED`: los 265 tests de backend no cuentan aquí.

---

# 16. Hallazgos nuevos

| ID | Hallazgo | Sev. | Estado |
|---|---|---|---|
| **`R-59`** | Un maestro hijo admitía un padre de otra empresa | **P1** | **corregido** (`GA-REM-002 AC10`) |
| `R-60` | Las claves de trazabilidad no comprueban pertenencia | P2 | abierto → `GA-REM-008`. Solo alcanzable por Super Admin |
| `R-61` | Dos instalaciones de Playwright con versiones distintas | P3 | abierto → `GA-REM-019` |
| `R-62` | 23 tests heredados fallando | P2 | **clasificado** 2026-09-05 → [`PLAYWRIGHT_FAILURE_CLASSIFICATION.md`](PLAYWRIGHT_FAILURE_CLASSIFICATION.md). El diagnóstico preliminar («interfaz de junio de 2026») se cumple en **12 de 23**; los otros 11 fallan por credenciales o falta de autenticación |

Todos `PRE_EXISTING_NEWLY_DISCOVERED`. **`INTRODUCED_BY_REMEDIATION`: 0.**

Ninguno es P0: ninguno permite mutación entre inquilinos, corrupción de datos, saltarse la
autenticación ni una aprobación falsa.

---

# 17. Remediaciones activadas

| Spec | Motivo | Qué se hizo |
|---|---|---|
| **`GA-REM-002`** | El gate demostró `AC05` verificado a medias | `AC10`+`AC11` añadidos por enmienda; `app/tenancy.py`; validación en operaciones y maestros |
| `GA-REM-016` | Spec activa | `AC01`: una línea de `tests/operations.spec.ts` que tumbaba el descubrimiento del directorio entero |

**Ninguna corrección cruzada sin trazabilidad.** La de `GA-REM-002` se activó formalmente,
con enmienda de spec y AC, antes de tocar código.

---

# 18. Regresión backend

```
265 passed · 0 failed · 49 skipped   (calendario real)
265 passed · 0 failed · 49 skipped   (calendario 2028)
```

+12 tests del gate multiempresa. Cero regresiones.

# 19. Regresión frontend

```
TypeScript ....... PASS
Vitest ........... 61/61
Paridad i18n ..... ES=866 EN=866
```

**Sin cambios en `frontend/src`** durante esta Wave.

# 20. Integridad de base de datos

```
Deriva de tablas ..... 0
Deriva de columnas ... 0
Deriva de enums ...... 0
Heads de Alembic ..... 1   (l2m3n4o5p6q7)
```

Ninguna migración nueva.

---

# 21. P0 restantes

**0.**

| Momento | P0 |
|---|---:|
| Auditoría inicial | 12 |
| Wave 1 | 8 |
| Wave 1.5 | 10 |
| Wave 2 | 0 |
| Wave 2.5 · 2.75 | 0 |
| **Wave 3** | **0** |

# 22. P1 restantes

**3**: `R-42` residual en trazabilidad (`R-60`, P2 tras acotarlo), `R-45`, `R-47`.
`R-59` se cerró en esta Wave.

---

# 23. Frontera SAP

`GA-REM-017` sigue `BLOCKED_EXTERNAL`. **No se implementó SAP real.**

El paso 8 del orden queda `PARTIAL`: lo que `GA-REM-010` autoriza —evento internamente
listo, estado correcto, preparación del *payload*— es lo único certificable, y no se
declara «SAP integrado».

---

# 24. Release blockers

Sin cambios respecto de la Wave 2.75:

| ID | Blocker | Estado |
|---|---|---|
| `GA-TD-040` | Copia de seguridad verificada | **ABIERTO** |
| `R-52` | Activación del volumen (`docker compose up -d`) | precondición, no bloqueante |
| `R-58` | Verificación con Docker real | pendiente del primer despliegue |

**Ninguno se cerró artificialmente.** Wave 3 no puede cambiar `READY_FOR_RELEASE` aunque
todos los procesos pasaran.

---

# 25. Madurez del producto

```
NIVEL 4 — OPERATIONAL BETA
```

Sube de 3 a 4: por primera vez existen procesos de negocio certificados de extremo a
extremo, con aislamiento multiempresa auditado en escritura y no solo en lectura.

**No puede ser NIVEL 5** mientras `READY_FOR_RELEASE = NO`. Y aunque se resolviera la copia
de seguridad, 1 de 15 procesos certificados no sostiene una declaración de producción.

---

# 26. Recomendación

| # | Acción | Motivo |
|---|---|---|
| 1 | **`GA-TD-040`** — copia verificada | único bloqueante de publicación; es trabajo de una tarde |
| 2 | Publicar, con `R-52` en el mismo despliegue, y verificar `R-58` | la compatibilidad está certificada por tres caminos |
| 3 | **Continuar `GA-REM-016`**: pasos 4–7 del orden | el arnés existe y el piloto demostró que es estable |
| 4 | `R-60` antes de certificar trazabilidad | el paso 9 no puede certificarse con esa clave sin comprobar |
| 5 | `GA-REM-021` (agua) · `GA-REM-022` (KPI) | ahora sí bloquean cobertura de proceso, no solo backlog |
| 6 | `R-62` — suite heredada | 23 tests rotos; decidir entre actualizar o retirar, con spec |
| 7 | `GA-TD-039` — observabilidad | `PRE-PRODUCTION` |

---

# 27. Evidence index

| Artefacto | Contenido |
|---|---|
| `playwright.config.ts` | configuración única; `AC01` |
| `scripts_e2e.sh` | arnés reproducible: base aislada + backend + frontend |
| `e2e/proceso-01…03-*.spec.ts` | 21 casos E2E, 21 PASS |
| `backend/tests/security/test_multitenant_isolation.py` | gate sistémico, 12 PASS |
| `backend/app/tenancy.py` | pertenencia de recursos, un solo sitio |
| `TENANT_RESOURCE_CLASSIFICATION.md` | 47 tablas por ámbito |
| `MULTITENANT_WRITE_ISOLATION_MATRIX.md` | 90 endpoints, 26 FK |
| `PROCESS_CERTIFICATION_MATRIX.md` | 15 procesos con estado |
| `E2E_TEST_INVENTORY.md` | 59 tests descubiertos; suite heredada medida |
| `processes/PROCESS-07-*.md` · `PROCESS-ORDEN-01/02-*.md` | informes por proceso |
| `specs/remediation/GA-REM-002-*.md` | enmienda con `AC10`/`AC11` |
| `BACKEND_TEST_BASELINE_RUN_01.md` | **congelado, no sobrescrito** |
