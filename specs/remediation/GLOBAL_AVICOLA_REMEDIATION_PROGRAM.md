# GLOBAL AVÍCOLA — PROGRAMA MAESTRO DE REMEDIACIÓN

| | |
|---|---|
| **Documento** | Programa maestro de remediación post-auditoría |
| **Versión** | 1.0 |
| **Fecha de creación** | 2026-09-03 |
| **Tipo** | `POST-AUDIT REMEDIATION PROGRAM` |
| **Baseline de entrada** | Auditoría integral `audit/`, commit `bfccdfb` (2026-07-08) |
| **Estado del repositorio al abrir el programa** | `bfccdfb` — **sin cambios** desde la auditoría (verificado con `git status`) |
| **Baseline de salida previsto** | `GLOBAL_AVICOLA_BASELINE_V1_1.md` |

> Este documento y todas las specs `GA-REM-*` se crean **después** de la auditoría. No pretenden haber existido antes. Ninguna es una spec retroactiva de maquillaje.

---

## 1. Objetivo

Llevar Global Avícola desde **NIVEL 3 — INTEGRACIÓN** hasta **NIVEL 4 — BETA OPERATIVA**, con procesos de negocio certificados end-to-end y trazabilidad metodológica restablecida, sin reescribir la arquitectura existente.

Principio operativo:

```
CONSERVAR → REGULARIZAR → CORREGIR → INTEGRAR → PROBAR → CERTIFICAR
```

## 2. Baseline de entrada

Diagnóstico de la auditoría integral (2026-09-02):

```
Veredicto funcional ............ INTEGRACIÓN INCOMPLETA
Cobertura funcional E2E ........ 12/56 = 21,4 %
Procesos identificados ......... 15  (taxonomía interna del proyecto)
Procesos certificados E2E ......  0
Madurez ........................ NIVEL 3 — INTEGRACIÓN
Veredicto Spec Development ..... CUMPLIMIENTO PARCIAL
Spec Compliance Rate ........... 23,3 %
Disciplina ..................... NIVEL C — INCONSISTENTE
Bloqueadores P0 ................ 12
Riesgos P1 ..................... 16
Deuda técnica total ............ 60
Deuda Spec Development ......... 16
```

### 2.1 Revalidación del baseline (obligatoria antes de intervenir)

Los 12 bloqueadores P0 fueron **reconfirmados contra el código actual** antes de abrir este programa. Resultado: **12/12 confirmados, 0 `ALREADY_RESOLVED`**. Detalle en `audit/remediation/REMEDIATION_READINESS_REPORT.md §2`.

### 2.2 Hallazgos NUEVOS descubiertos durante la revalidación

La revalidación incorporó una fuente que la auditoría había registrado como *disponible y no explotada*: la documentación original del cliente en `Imagen de Procesos Documentado/`. Su explotación produjo tres hallazgos que **no estaban en la auditoría**:

| ID | Hallazgo | Evidencia | Impacto |
|---|---|---|---|
| **R-13** | **El consumo de agua no se captura en ninguna parte.** El documento de requerimientos del cliente (`Bases Consideradas en el Desarrollo de la App Avicola.pdf`, Ing. María E. Arévalo) lo exige como dato diario obligatorio en Reproductora Cría, Reproductora Producción y Pollo de Engorde. El backend **no tiene ningún campo de agua**; `ReportsPage.tsx:30` lee `e.water_liters`, que no existe, y grafica una serie permanentemente en cero. | `grep water backend/app` → 0 resultados; `frontend/src/pages/reports/ReportsPage.tsx:30` | requisito del cliente **no implementado**; gráfica falsa |
| **R-14** | **La Tasa de Eclosión devuelve un texto en lugar de un número.** `get_kpi_hatchery` retorna `"hatchability_pct": "N/A (requiere datos de carga de incubación)"` pese a que `HatcheryParams.quantity_loaded` existe y ya se suma en `get_hatchery_egg_balance`. Es uno de los 5 KPI que el cliente exige para Incubadora. | `backend/app/reports/service.py:145-147` | KPI central inoperante con los datos ya disponibles |
| **R-15** | **La documentación funcional del cliente nunca se ha usado para validar la implementación.** El repositorio contiene 43 documentos del negocio —incluido el documento de requerimientos original y un inventario de 30 procesos— y **ningún artefacto del proyecto los referencia**. Una lectura parcial ya produjo dos requisitos incumplidos (R-13 y R-14), lo que sugiere más huecos sin detectar. | `grep -r "AVI-" specs/ docs/ backend/ frontend/src` → 0; hallazgos R-13 y R-14 | **no existe verificación de que lo implementado cubra lo que el negocio describió** |

**Aclaración de alcance (decisión del propietario):** la documentación del cliente es **fuente de validación**, no estructura a adoptar. Global Avícola **conserva su propia taxonomía** de procesos. `GA-REM-020` comprueba cobertura y completitud; **no** reconcilia identificadores ni reestructura `processCatalog.ts`.

Validación preliminar ya realizada: **los 17 procesos del cliente dentro del alcance v1 tienen cobertura funcional en la implementación**. No se detecta ningún proceso de negocio ausente. Lo que sí aparecen son huecos de **dato y de KPI** (R-13, R-14) y un `SPEC_GAP` (`egg_storage`).

### 2.3 Matiz sobre clasificaciones de la auditoría

La explotación de la documentación del cliente obliga a reclasificar dos hallazgos:

| Elemento | Clasificación en la auditoría | Clasificación corregida | Motivo |
|---|---|---|---|
| Tabla y flujo `egg_storage` | `IMPLEMENTED_WITHOUT_SPEC` | **`SPEC_GAP`** | El cliente **sí** lo exige («Almacenamiento de Huevos: fecha, condiciones, duración»). Lo que falta es la spec del proyecto, no el requerimiento. |
| Condiciones de transporte en recepciones/despachos | sin clasificar | **requisito del cliente cubierto** | El cliente lo exige explícitamente; está implementado en `extra_data`. |

Esto **no** invalida la auditoría: confirma su propia advertencia de que la documentación del cliente estaba disponible y no explotada formalmente.

## 3. Alcance

### 3.1 Dentro del alcance

1. Gobierno de Spec Development (constitución ratificada).
2. Autorización, contexto de sesión y credenciales.
3. Operaciones críticas: mortalidad, correcciones, BR-14, trazabilidad generacional.
4. Persistencia de evidencias y semántica de estados SAP.
5. Alineación de contratos frontend ↔ backend.
6. Quality gates de CI **que no alteren el mecanismo de despliegue**.
7. Entorno de test aislado y certificación de las suites backend y E2E.
8. Certificación de procesos de negocio.
9. Integración SAP real (sujeta a disponibilidad externa).
10. Recuperación de trazabilidad metodológica y baseline v1.1.
11. Reevaluación de deuda P2/P3 tras la estabilización.
12. Brechas de captura y KPI derivadas de la documentación del cliente (R-13, R-14).
13. Validación de cobertura funcional contra la documentación del cliente (R-15), **sin adoptar su taxonomía**.

### 3.2 Fuera del alcance — decisión del propietario

```
DEPLOYMENT AUTOMÁTICO ACTUAL
=
KNOWN_ACCEPTED_RISK
=
OUT_OF_SCOPE
=
NO MODIFICAR
```

Queda **expresamente excluido** de este programa, y ningún `GA-REM` puede introducirlo por vía indirecta:

- modificar los workflows de deployment (`docker-push-backend.yml`, `docker-push-frontend.yml`, `docker-build-push.yml`);
- desactivar o restringir Watchtower;
- eliminar o cambiar la publicación de la etiqueta `:latest`;
- cambiar los *triggers* actuales de despliegue;
- rediseñar la estrategia de ramas **por motivo de deployment**;
- bloquear el push directo a `main` **por motivo de deployment**;
- detener despliegues automáticos.

**Riesgo aceptado y sus consecuencias reconocidas** (se documentan, no se corrigen):

| Consecuencia | Estado |
|---|---|
| Un quality gate en CI **no podrá impedir** que una imagen defectuosa llegue a producción | `KNOWN_ACCEPTED_LIMITATION` |
| El intervalo entre un commit defectuoso y su llegada a producción seguirá siendo ≤ 60 s | `KNOWN_ACCEPTED_LIMITATION` |
| No existirá rollback automatizado ni promoción por etiqueta | `KNOWN_ACCEPTED_LIMITATION` |
| Las migraciones seguirán sin ejecutarse automáticamente en el despliegue **salvo** que se resuelva sin tocar el mecanismo de deploy | ver GA-REM-014 §alcance |

**Mitigación compensatoria autorizada** (no altera el deployment): elevar la señal de calidad *antes* del push mediante quality gates ejecutables localmente y en CI, y publicar un informe de estado visible. GA-REM-013 lo desarrolla.

### 3.2.bis Excluido por decisión del propietario — taxonomía

```
LA TAXONOMÍA DE PROCESOS DEL PROYECTO NO SE ADECÚA A LA DE PROTINAL
```

La documentación del cliente se usa **exclusivamente para validar** procesos, procedimientos, datos, reglas y KPI. Queda excluido: adoptar los códigos `AVI-*` como identificadores, reestructurar `processCatalog.ts`, convertir cada proceso codificado del cliente en unidad certificable, o renombrar etapas y operaciones para alinearlas con su nomenclatura.

### 3.3 Excluido por naturaleza (§40 del encargo)

Renombrados masivos, reorganización de carpetas, cambio de framework u ORM, microservicios, sustitución de librerías estables y rediseño completo de UI. Solo se refactoriza lo que una spec concreta exija.

## 4. Riesgos aceptados

| ID | Riesgo | Decisión | Origen |
|---|---|---|---|
| `RA-01` | Despliegue automático sin puerta de calidad | **ACEPTADO** — no se modifica | propietario |
| `RA-02` | Un quality gate no puede bloquear el despliegue | **ACEPTADO** — derivado de RA-01 | consecuencia |
| `RA-03` | La cadena LIVIANAS/Ponedoras (13 de los 30 procesos oficiales) queda fuera de v1 | **ACEPTADO** — ya declarado en `spec.md §9` | spec vigente |
| `RA-04` | Los 30 formatos de especificación de proceso del cliente son **plantillas vacías** (5 de 30 marcados "LISTO", sin contenido rellenado) | **ACEPTADO como limitación de fuente** — la validación se apoyará en el documento de requerimientos, los manuales técnicos y el inventario de procesos, no en los formatos | evidencia |
| `RA-05` | La taxonomía de procesos del proyecto difiere de la codificación del cliente | **ACEPTADO por decisión del propietario** — la documentación del cliente es fuente de validación, no estructura a adoptar. `processCatalog.ts` no se modifica | decisión |

## 5. Dependencias estructurales del programa

```
GA-REM-001 (gobierno)   ─── habilita ──▶ TODAS las demás
GA-REM-014 (entorno)    ─── habilita ──▶ GA-REM-015 ──▶ GA-REM-016 ──▶ certificación
GA-REM-002 (RBAC)       ─── habilita ──▶ GA-REM-007, GA-REM-012, cierre de seguridad
GA-REM-011 (contratos)  ─── habilita ──▶ GA-REM-006, 008, 016, 022
GA-REM-010 (semántica)  ─── habilita ──▶ GA-REM-017
GA-REM-020 (validación) ─── INFORMA ──▶ GA-REM-016, 021, 022 y el backlog
                            (no bloquea: aporta verificación de cobertura)
```

Mapa completo: `audit/remediation/DEPENDENCY_MAP.md`.

## 6. Orden de ejecución

El orden conceptual propuesto en el encargo se conserva, con **tres ajustes justificados**:

| Ajuste | Justificación |
|---|---|
| **GA-REM-020 (validación de cobertura) se ejecuta pronto, pero sin bloquear** | No es prerequisito de nadie: **informa**. Se ejecuta temprano porque puede revelar más huecos como R-13 y R-14, y conviene tenerlos en el backlog antes de comprometer el alcance de certificación. Descubierta en la revalidación (R-15). |
| **GA-REM-014 (entorno de test) se adelanta por delante de GA-REM-005** | Los AC de mortalidad, correcciones y BR-14 exigen tests ejecutables. Sin entorno aislado, esas specs no pueden cerrarse (`NO TEST = NO COMPLETE`). Ejecutarlo antes evita bloquear tres specs de Fase C. |
| **GA-REM-012 (contraseña) se agrupa con la Fase B** | Es un defecto de autenticación, comparte superficie con GA-REM-002/003 y su AC depende de la política de sesión que define GA-REM-003. |

Orden final: `audit/remediation/REMEDIATION_BACKLOG.md`.

## 7. Specs previstas

22 specs `GA-REM-001` … `GA-REM-022`. Índice: `specs/remediation/INDEX.md`.

## 8. Criterios generales de cierre

Reglas de este programa, sin excepción:

```
NO SPEC              = NO DEVELOPMENT
NO ACCEPTANCE CRITERIA = NO IMPLEMENTATION
NO VALIDATION        = NO COMPLETE
NO E2E               = NO PROCESS CERTIFIED
```

Una `GA-REM` solo puede marcarse `CERTIFIED` cuando existan **todos** estos elementos:

1. Spec aprobada con AC verificables en formato `Given/When/Then`.
2. Tasks derivadas de la spec, cada una vinculada a un AC.
3. Implementación cuyos commits referencian la `GA-REM`.
4. Tests que ejercitan cada AC, ejecutados y en verde.
5. Evidencia registrada (comando, salida, ruta y línea).
6. E2E cuando el AC tenga superficie de usuario.
7. Control de regresiones superado (§9).
8. `GA-REM-XXX — CERTIFICATION REPORT` emitido.

Estados admitidos: `DISCOVERED` · `SPEC_DRAFT` · `SPEC_READY` · `IMPLEMENTING` · `IMPLEMENTED` · `TESTING` · `E2E_VALIDATION` · `CERTIFIED` · `BLOCKED_EXTERNAL` · `DEFERRED` · `ACCEPTED_RISK` · `ALREADY_RESOLVED`.

## 9. Control de regresiones obligatorio

Cada `GA-REM` implementada debe verificar, antes de cerrarse:

| # | Verificación | Comando de referencia |
|---|---|---|
| 1 | El problema declarado está resuelto | test específico del AC |
| 2 | Todos los AC de la spec se cumplen | matriz AC↔test |
| 3 | Los tests preexistentes siguen pasando | `vitest run` · `pytest` (entorno aislado) |
| 4 | Ningún otro proceso se rompe | suite E2E disponible |
| 5 | La base de datos mantiene integridad: **0 deriva, 1 head Alembic** | script AST `Base.metadata` vs `upgrade()` |
| 6 | El frontend compila | `tsc -b --noEmit` |
| 7 | El backend compila | `python -m compileall app seeds tests` |
| 8 | La paridad i18n se mantiene (865 = 865, 0 faltantes) | script de comparación de `translation.json` |

## 10. Componentes protegidos — NO TOCAR sin necesidad demostrada por spec

La auditoría verificó estos componentes como técnicamente sólidos. Antes de modificar cualquiera de ellos hay que responder *«¿es necesario para cumplir un AC de esta spec?»*. Si la respuesta es no: **no tocar**.

| # | Componente | Verificación que lo respalda |
|---|---|---|
| 1 | Modelo de datos y migraciones | 47 tablas, 21 migraciones, **0 deriva**, 1 head, 1 base |
| 2 | Modelo unificado `OperationalEvent` + 6 submovimientos | sustituye 12+ tablas legacy; diseño acertado |
| 3 | Adapter pattern de SAP (ABC + DTOs) | desacoplamiento correcto; solo falta la implementación concreta |
| 4 | Idempotencia y bitácora SAP (SHA-256, `SapPayload`/`SapResponse`) | mecanismo correcto |
| 5 | Validadores de reglas de negocio | correctos salvo BR-06 (objeto de GA-REM-005) |
| 6 | i18n | 865/865 claves, paridad total |
| 7 | Cabeceras de seguridad y validación de arranque de `config.py` | aborta con secretos por defecto |
| 8 | Ausencia de SQL crudo — 100 % ORM | sin superficie de inyección |
| 9 | `processCatalog.ts` como fuente única de taxonomía | **no se modifica** — es la unidad de certificación del proyecto (`RA-05`) |
| 10 | Estructura modular por dominio del backend | 11 módulos coherentes |
| 11 | Tipado del frontend a nivel de compilación | `tsc -b` en verde |

## 11. Regla sobre modificaciones de base de datos

La integridad verificada (`0 tablas de deriva · 0 columnas de deriva · 21 migraciones · 47 tablas · 1 head`) es un activo del proyecto.

- Toda modificación de esquema se hace **exclusivamente** por migración Alembic formal.
- Nunca se altera la estructura manualmente ni desde el ORM sin migración.
- El docstring de cada migración nueva debe citar la `GA-REM` y el AC que la autorizan.
- El control de regresiones §9.5 verifica que la deriva siga siendo cero.

## 12. Regla sobre tests

Prohibido, sin excepción:

- borrar un test porque falla;
- marcar `skip` sin justificación escrita en la spec;
- rebajar aserciones;
- alterar el resultado esperado para acomodarlo al bug;
- mockear funcionalidad central para conseguir verde.

Ante un test en rojo, el orden de decisión es:

```
SPEC → REGLA DE NEGOCIO → TEST → IMPLEMENTACIÓN
```

La spec vigente decide quién está equivocado. Si la spec no lo resuelve, se abre un `REQUIREMENT_CONFLICT` (§13) y **no se desarrolla** hasta determinar la regla vigente.

## 13. Regla de contradicción entre fuentes

Cuando `DOCUMENTACIÓN DEL CLIENTE ≠ SPEC ≠ CÓDIGO ≠ AUDITORÍA`, no se elige arbitrariamente. Se registra un `REQUIREMENT_CONFLICT` con alternativas, impacto, evidencia y comportamiento actual, y se escala.

Conflictos ya abiertos por la revalidación: `audit/remediation/REMEDIATION_READINESS_REPORT.md §6`.

## 14. Trazabilidad exigida

```
HALLAZGO → GA-REM → AC → TASK → CÓDIGO → TEST → E2E → CERTIFICACIÓN
```

Cada commit del programa debe poder asociarse a una `GA-REM` o a una task suya. Formato de mensaje recomendado:

```
<tipo>(GA-REM-XXX): <resumen>

AC cubiertos: AC01, AC03
```

## 15. Métricas a actualizar tras cada GA-REM certificada

`audit/remediation/MASTER_REMEDIATION_MATRIX.md` mantiene el marcador vivo:

```
Requerimientos E2E completos · Cobertura E2E · Procesos certificados
Tests backend PASS · Tests E2E PASS · P0 abiertos · P1 abiertos
Spec Compliance Rate · Traceability Rate · AC Coverage · Spec Test Coverage
```

No se espera al final del programa para volver a medir.

## 16. Objetivo de salida

El programa **no** termina cuando el código compila ni cuando los defectos dejan de verse. Termina cuando:

- los 12 bloqueadores P0 están cerrados con test de regresión;
- existe al menos un conjunto de procesos de negocio `CERTIFIED` con E2E;
- la trazabilidad `HALLAZGO → CERTIFICACIÓN` es demostrable;
- el baseline v1.1 está publicado;
- Global Avícola puede evaluarse objetivamente como **NIVEL 4 — BETA OPERATIVA**.
