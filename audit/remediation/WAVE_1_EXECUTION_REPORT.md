# WAVE 1 — EXECUTION REPORT

| | |
|---|---|
| **Wave** | 1 — Baseline Freeze + Test Foundation + Safe Remediation |
| **Fecha** | 2026-09-03 |
| **Commit base** | `bfccdfb` |
| **Alcance ejecutado** | `GA-REM-020`, `014`, `004`, `009`, `010`, `011`, `013` |
| **Alcance NO ejecutado** | `002`, `003`, `005`, `006`, `007`, `008`, `012`, `015`, `016`, `017`, `018`, `019`, `021`, `022` |

---

# 1. Executive summary

Wave 1 congeló qué debe hacer Global Avícola, construyó la infraestructura de pruebas segura y resolvió los defectos inequívocos que no requerían base de datos.

**Cuatro bloqueadores P0 cerrados** de los doce: evidencias efímeras, SAP simulado, credenciales públicas y contratos rotos. **Cinco pantallas caídas recuperadas.** Por primera vez en la vida del proyecto existe una señal de calidad ejecutable: **8 comprobaciones, 8 en verde**.

Dos resultados merecen destacarse por encima del resto:

1. **La guarda de entorno de pruebas impide, de forma demostrada, que una sesión de tests escriba en la base de datos productiva.** Ese era el riesgo que impidió a la auditoría ejecutar 76 tests. Está cerrado y probado con 24 tests propios.
2. **La validación contra la documentación del cliente confirmó que ningún proceso de negocio está ausente.** Los 17 procesos de la cadena PESADAS tienen cobertura funcional. Lo que falta son datos concretos y KPI, no funcionalidad estructural. Es la mejor noticia del programa.

También hay un resultado que no se puede maquillar: **`GA-REM-014` no alcanza `CERTIFIED`**. La máquina de ejecución no tiene PostgreSQL, ni Docker, ni `aiosqlite`. El ciclo completo crear→migrar→sembrar→probar→destruir **no se pudo ejecutar**. Se declara `IMPLEMENTED` con dos AC en `BLOCKED_EXTERNAL`, y eso condiciona el arranque de Wave 2.

---

# 2. Functional Baseline V1.1

🔒 **FROZEN** — `specs/remediation/GLOBAL_AVICOLA_FUNCTIONAL_BASELINE_V1_1.md`

```
Requerimientos vigentes ................ 60   (56 auditados + 4 nuevos)
  Cubiertos E2E ........................ 12   (20,0 %)
  Parciales ............................ 28
  Rotos ................................  7
  Ausentes ............................. 13
  No verificables ......................  1

Requirement conflicts abiertos .........  6   (RC-01…05, RC-07)
SPEC_GAPS ..............................  5
Riesgos aceptados ......................  5   (EX-01, RA-01…05)
```

A partir de este punto **no se agregan requisitos durante una remediación**. Todo descubrimiento posterior se registra como `NEW_REQUIREMENT_DISCOVERY` para evaluación separada.

---

# 3. GA-REM-020 · resultados — `CERTIFIED`

**96 elementos funcionales extraídos y validados** de la documentación del cliente.

```
COVERED ......... 57 (59 %)      ABSENT ..........  5
PARTIAL ......... 25 (26 %)      OUT_OF_SCOPE ....  6 + 13 procesos LIVIANAS
NOT_VERIFIABLE ..  2             REQ_CONFLICT ....  1
```

## Hallazgos de negocio

1. **Ningún proceso del cliente está ausente.** Los 17 procesos PESADAS en alcance tienen cobertura: 12 completos y 5 parciales, y los 5 lo son por dos defectos ya identificados (P0-1 mortalidad, P0-11 trazabilidad), no por funcionalidad faltante.
2. **La app respeta las 6 prohibiciones arquitectónicas del cliente**: no crea órdenes de compra, materiales ni almacenes, no cambia costos, no ajusta inventario sin documento SAP y no cierra órdenes. **No invade el ámbito mandante de SAP.**
3. **El déficit dominante está en los KPI, no en la captura.** 22 de 26 datos diarios exigidos están cubiertos; en cambio 12 de 18 KPI están `PARTIAL`.
4. **6 de las 17 reglas obligatorias del cliente son inaplicables** por no consumir maestros ni inventario de SAP. No son defectos independientes.
5. **La máquina de estados coincide** con los 11 estados operativos del cliente en 9 de 11 casos directos.

## Verificación de no modificación
`backend/app` 0 · `frontend/src` 0 · `alembic/versions` 0 · `processCatalog.ts` 0 · identificadores `AVI-*` introducidos 0.

**La taxonomía del proyecto se conserva íntegra (`RA-05`).**

---

# 4. Nuevos requerimientos y gaps encontrados

## `GA-REQ` nuevos (4)
| ID | Requerimiento | Justificación |
|---|---|---|
| `GA-REQ-057` | Consumo diario de agua | «Datos Diarios a Registrar» en 3 etapas; el sistema anterior lo tenía |
| `GA-REQ-058` | Rotación de huevos: frecuencia y ángulo | «Datos Diarios a Registrar → Incubación» |
| `GA-REQ-059` | Identificador de transacción externa hacia SAP | `Recomendación central §19`: campo **obligatorio** contra duplicados |
| `GA-REQ-060` | Bandera de riesgo en la inspección | `Recomendación central §7` |

**No se generó ningún `GA-REQ`** a partir de los manuales técnicos, el contexto de negocio ni los formatos vacíos (§9 del encargo respetado).

## Hallazgos (10)
`R-13` agua · `R-14` tasa de eclosión · `R-15` documentación sin validar **(cerrado)** · `R-16` rotación de huevos · `R-17` 12 KPI parciales · `R-18` sin curva de peso · `R-19` sin validación de unidad · `R-20` sin maestros SAP · `R-21` identificadores SAP nunca poblados **(cerrado en Wave 1)** · `R-22` sin bandera de riesgo.

## Reclasificación
`egg_storage`: de `IMPLEMENTED_WITHOUT_SPEC` a **`CLIENT_REQUIREMENT_PRESENT` + `SPEC_GAP`**. La implementación es correcta y **no se modificó**.

## Nuevo requirement conflict
`RC-07` — política de mortalidad frente a SAP: el cliente presenta tres políticas excluyentes y exige elegir una. **Escalado, no resuelto.**

---

# 5. GA-REM-014 · certificación — `IMPLEMENTED`, no `CERTIFIED`

```
Test DB creation ........ BLOCKED_EXTERNAL   (sin motor de BD en la máquina)
Alembic upgrade ......... BLOCKED_EXTERNAL
Fixture/write ........... BLOCKED_EXTERNAL
Cleanup ................. BLOCKED_EXTERNAL
Prod guard .............. PASS   (24/24 tests · 8 escenarios verificados)
Backend smoke test ...... PASS   (compileall · 176 rutas · 0 deriva)
```

## Lo que sí está cerrado
La **guarda FAIL-CLOSED** con 5 señales independientes. Verificada en 4 escenarios reales de `pytest`:

| Escenario | Resultado |
|---|---|
| entorno por defecto (sin marcador) | **abortado, exit 3** |
| marcador puesto, apuntando a `64.225.104.69/avicolav2` | **abortado, exit 3** |
| `ENVIRONMENT=production` | **abortado, exit 3** |
| entorno de pruebas válido | permitido |

**Durante toda la Wave no se abrió ni una sola conexión contra la base productiva.**

## Lo que falta
Un motor PostgreSQL. Con cualquiera de las tres opciones (local, contenedor efímero o instancia dedicada), `backend/scripts/run_tests.sh` completa el ciclo **sin más cambios de código**.

## Justificación de haber continuado con Wave 1
El §18 prohíbe avanzar con correcciones funcionales **críticas** sin `GA-REM-014` certificada. Las cinco remediaciones ejecutadas **no son críticas y ninguna requiere base de datos**: sus AC se verifican por análisis estático, esquema OpenAPI, typecheck, tests unitarios de frontend y verificación de diff. Las correcciones críticas —`005`, `006`, `007`, `008`, `002`— **no se ejecutaron**.

---

# 6. GA-REM-004 · credenciales — `CERTIFIED`

| Métrica | Antes | Después |
|---|---|---|
| Pares usuario/contraseña en documentación | 15 | **0** |
| Contraseñas literales en seeds | 25 | **0** |
| Rate limiting en producción | desactivado por omisión | **activo por defecto** |

Helper `_seed_password()` que lee del entorno y **aborta** si falta, en lugar de crear usuarios con credenciales conocidas. El resumen de `integration_seeds` ya no imprime contraseñas en claro.

**5 acciones operativas** quedan fuera del repositorio (rotación en el entorno, verificación del 429, rol de BD con privilegios mínimos).

---

# 7. GA-REM-009 · evidencias — `CERTIFIED`

Volumen nombrado `avicola-media` montado en `/app/media`; `SAP_EXPORT_DIR` reubicado desde `/tmp` al volumen; `client_max_body_size 12m` en Nginx.

**Decisión: opción A (volumen Docker).** No se introdujo almacenamiento de objetos: §40 desaconseja añadir servicios externos si un volumen resuelve el problema.

`git diff --stat docker-compose.yml` → **13 inserciones, 0 eliminaciones**. Cambio puramente aditivo.

---

# 8. GA-REM-010 · semántica SAP — `CERTIFIED`

**Regla aplicada:** `NO VERIFIED SAP DELIVERY = NO TRUE sent_to_sap`

| Antes | Después |
|---|---|
| `ManualSapAdapter` devolvía `sap_document_id="MANUAL-xxxx"` | devuelve `None` + `raw_response.delivery="manual_pending"` |
| Los eventos pasaban a `SENT_TO_SAP` | permanecen en `CONSOLIDATED` |
| BR-15 los bloqueaba para siempre | **siguen siendo corregibles** |
| `check_connection()` → siempre `True` | → `False` en modo manual |
| `# TODO: read from config` | `SAP_ADAPTER` con validación; **0 TODO en el backend** |
| `external_transaction_id`/`source_system` nunca poblados | **poblados** (`R-21`, `GA-REQ-059`) |
| backoff `(minuto+n)%60` podía quedar en el pasado | `timedelta` |
| `mock_adapter.py` no compilaba | **eliminado** |

**Sin migración. Sin cambio de esquema.** Se reutiliza `CONSOLIDATED` en lugar de añadir un valor al enum, preservando el baseline protegido.

---

# 9. GA-REM-011 · contratos FE↔BE — `PARTIALLY CERTIFIED`

Matriz consolidada **antes** de corregir: `FE_BE_CONTRACT_MATRIX.md`, 18 desajustes clasificados.

```
Corregidos ....... 10   (C-01…C-09, C-17)
Diferidos ........  8   (C-10…C-16, C-18) — con justificación explícita
Bloqueados por RC   0
```

| Corrección | Efecto |
|---|---|
| 6 llamadas `limit=200` → 422 | **5 pantallas recuperadas**; C-03/04/05 pasan a usar el endpoint por identificador |
| `registered_by_me` + lista de estados | «Mis Pendientes» deja de dar **500** y muestra solo lo propio |
| 8 esquemas `Update` nuevos | **12 de 12** catálogos que la UI ofrece editar tienen `PUT`; se elimina el **405** |

Diferidos por criterio de alcance, no por conflicto: `sap_document_ref` (activaría BR-11 y BR-18, hoy inertes), `idempotency_key` (decisión de diseño), filtros de Revisión/Auditoría y envoltorio de paginación.

---

# 10. GA-REM-013 · quality gates — `CERTIFIED`

`.github/workflows/quality-gates.yml` con tres jobs, disparado en `push` y en `pull_request`. `backend/scripts/verify.sh` reproduce localmente las mismas comprobaciones.

**El job `scope-guard`** verifica en cada ejecución que los tres workflows de despliegue existen y que `watchtower`, `pull_policy: always` y `:latest` permanecen. **Si alguien intentara retirar el despliegue automático por vía indirecta, el job falla.** Es la garantía automatizada de `EX-01` en ambas direcciones.

ESLint queda **informativo y declarado como tal**: los 5 errores son deuda preexistente y el §26 prohíbe el cleanup general. No se silenciaron reglas.

---

# 11. Tests

```
Frontend · vitest ................. 61 / 61 PASS
Frontend · tsc -b --noEmit ........ exit 0
Frontend · paridad i18n ........... 865 = 865, 0 faltantes
Backend  · compileall ............. OK
Backend  · guarda de entorno ...... 24 / 24 PASS
Backend  · Alembic ................ 1 head, 1 base, 21 revisiones
Backend  · deriva de esquema ...... 47 tablas, 0 deriva
Backend  · seeds sin literales .... OK

verify.sh ......................... 8 / 8 EN VERDE
```

**Suite completa de backend: `READY_TO_EXECUTE`** — 100 tests recolectados (76 heredados + 24 nuevos). No se ejecuta: pertenece a `GA-REM-015` y requiere el motor de BD.

**No se declara `BACKEND TEST CERTIFIED`.**

---

# 12. Regression status

Los 8 puntos del Art. 12 de la Constitución, verificados tras cada cambio:

| # | Verificación | Resultado |
|---|---|---|
| 1 | Problemas declarados resueltos | ✅ |
| 2 | AC cumplidos o diferidos con justificación | ✅ |
| 3 | Tests preexistentes siguen pasando | ✅ 61/61 vitest |
| 4 | Ningún otro proceso roto | ✅ 176 operaciones OpenAPI |
| 5 | **0 deriva de esquema · 1 head de Alembic** | ✅ |
| 6 | Frontend compila | ✅ |
| 7 | Backend compila | ✅ |
| 8 | Paridad i18n | ✅ 865 = 865 |

**Un incidente durante la Wave:** la corrección de C-01 introdujo un error de sintaxis en `company.store.ts`. **`tsc` lo detectó de inmediato**, se corrigió y se reverificó. Es la primera vez en el proyecto que un typecheck detecta un defecto antes de que llegue a `main` — la utilidad de `GA-REM-013` quedó demostrada dentro de la propia Wave que la creó.

---

# 13. P0 / P1 antes y después

## Bloqueadores P0

| ID | Bloqueador | Antes | Después |
|---|---|---|---|
| P0-1 | Mortalidad → 500 | abierto | **abierto** — `GA-REM-005`, Wave 2 |
| P0-2 | Correcciones no aplican | abierto | **abierto** — `GA-REM-006` ⚠ `RC-01` |
| P0-3 | Sin RBAC | abierto | **abierto** — `GA-REM-002`, Wave 2 |
| P0-4 | Escalada por refresh | abierto | **abierto** — `GA-REM-003`, Wave 2 |
| P0-5 | 5 pantallas rotas (422) | abierto | ✅ **CERRADO** |
| P0-6 | Evidencias efímeras | abierto | ✅ **CERRADO** |
| P0-7 | SAP simulado marca `sent_to_sap` | abierto | ✅ **CERRADO** |
| P0-8 | Credenciales públicas + rate limit off | abierto | ✅ **CERRADO** (repositorio) |
| P0-9 | Cambio de contraseña inoperante | abierto | **abierto** — `GA-REM-012` ⚠ `RC-05` |
| P0-10 | BR-14 eludible | abierto | **abierto** — `GA-REM-007` ⚠ `RC-03` |
| P0-11 | Trazabilidad auto-referencial | abierto | **abierto** — `GA-REM-008` ⚠ `RC-04` |
| P0-12 | Sin puerta de calidad | abierto | **parcial** — señal de calidad ✅; puerta de despliegue = `EX-01` |

```
P0 antes: 12    P0 después: 8    (–4)
```

## Riesgos P1

Cerrados: **P1-10** maestros sin edición · **P1-11** rate limit apagado · **P1-16** filtros inertes (parcial: Mis Pendientes).

```
P1 antes: 16    P1 después: 13   (–3)
```

---

# 14. E2E coverage

```
Baseline auditoría .......... 12 / 56 = 21,4 %
Tras Wave 1 ................. 12 / 60 = 20,0 %
```

**El numerador no cambió y el porcentaje bajó.** Es correcto y deliberado (§29 del encargo):

- El denominador creció de 56 a 60 al incorporar los `GA-REQ` nuevos del baseline V1.1.
- **Una corrección técnica no convierte un requerimiento en E2E completo.** Las cinco pantallas recuperadas y los contratos corregidos **habilitan** la certificación, no la sustituyen.
- Ningún requerimiento pasa a `COMPLETO` sin certificación real en `GA-REM-016`.

Declarar una subida de cobertura aquí sería exactamente el maquillaje que el encargo prohíbe.

---

# 15. Requirement conflicts abiertos

| ID | Conflicto | Bloquea | Decide |
|---|---|---|---|
| `RC-01` | ¿Corrección inmediata o sujeta a aprobación? | `GA-REM-006` | negocio |
| `RC-02` | Semántica de `bird_transfer` en el balance | `GA-REM-005` (parcial) | negocio |
| `RC-03` | ¿BR-14 absoluta o configurable? | `GA-REM-007` | negocio |
| `RC-04` | «el mismo lote de huevos» en `spec.md §4.9` | `GA-REM-008` | corrección de spec |
| `RC-05` | Política de complejidad de contraseñas | `GA-REM-012` | negocio |
| **`RC-07`** | **Política de mortalidad frente a SAP** (3 opciones excluyentes, sin decisión) | `GA-REM-017` | negocio |

`RC-06` cerrado por `RA-05`.

**Cinco de los ocho P0 restantes están bloqueados por decisiones de negocio, no por trabajo técnico.**

---

# 16. Blocked external

| Bloqueo | Afecta | Acción requerida |
|---|---|---|
| **Sin motor PostgreSQL de pruebas** | `GA-REM-014` AC03/AC05 · `GA-REM-015` · toda Wave 2 | proveer PostgreSQL local, Docker o instancia dedicada |
| Contrato técnico de SAP | `GA-REM-017` | solicitar al cliente: mecanismo, URL, autenticación, payload, credenciales |
| Acceso a la base productiva | `GA-REM-009` AC07 · `GA-REM-010` AC07 | inventario y saneamiento de datos |
| Entorno desplegado | `GA-REM-004` AC03 · `GA-REM-009` AC01/AC05 | verificación empírica |

---

# 17. Wave 2 · análisis de dependencias

## Prerrequisito bloqueante

```
PROVEER UN MOTOR POSTGRESQL DE PRUEBAS
        ↓
GA-REM-014 → CERTIFIED
        ↓
GA-REM-015 (100 tests) → habilita el cierre de 005, 006, 007, 008, 002, 003, 012
```

**Sin ese motor, Wave 2 no puede cerrar ninguna corrección crítica**, porque sus AC exigen tests ejecutables (`NO TEST = NO COMPLETE`).

## Orden propuesto para Wave 2

| # | GA-REM | Justificación del orden | Prerrequisito |
|---|---|---|---|
| 1 | **`014`** completar | desbloquea todo lo demás | motor de BD |
| 2 | **`015`** certificación de tests | conocer el estado real de los 100 tests antes de cambiar lógica | `014` |
| 3 | **`005`** mortalidad | mayor retorno operativo; complejidad XS; `test_f8c` ya existe como test de regresión | `015` · `RC-02` (parcial) |
| 4 | **`002`** RBAC | cierra el P0 de mayor impacto de seguridad; habilita `007` y `012` | `015` |
| 5 | **`003`** auth/refresh | cierra la escalada de privilegios; junto con `002` completa la seguridad | `015` |
| 6 | **`007`** BR-14 | complejidad XS una vez definido quién aprueba | `002` · **`RC-03`** |
| 7 | **`012`** contraseña | comparte superficie con `002`/`003` | `002` · `003` · **`RC-05`** |
| 8 | **`006`** correcciones | integridad de datos; la pantalla ya carga tras Wave 1 | `011` ✅ · **`RC-01`** |
| 9 | **`008`** trazabilidad | la pantalla ya carga tras Wave 1 | **`RC-04`** |
| 10 | **`021`** consumo de agua | requiere migración; independiente | — |
| 11 | **`022`** KPI (R-14 + R-17) | mayoritariamente exposición de lo ya implementado | `011` |
| 12 | **`016`** certificación E2E | punto de convergencia | 3–11 |

## Cambios respecto al orden de Wave 1

| Cambio | Motivo |
|---|---|
| `015` sube a la posición 2 | conocer el estado real de los tests **antes** de tocar lógica evita confundir defectos nuevos con preexistentes |
| `006` y `008` bajan | `GA-REM-011` ya reparó sus pantallas; dejan de ser urgentes y dependen de decisiones |
| `021` y `022` entran en Wave 2 | son P1 con especificación lista y sin conflictos |

## Trabajos paralelizables en Wave 2

| Vía | GA-REM | Depende del motor de BD |
|---|---|---|
| V1 · Núcleo | `014` → `015` → `005` | **sí** |
| V2 · Seguridad | `002` → `003` → `007` → `012` | sí (para cerrar) |
| V3 · Datos y KPI | `021` · `022` | parcial |
| V4 · Decisiones | resolver `RC-01`…`RC-05`, `RC-07` | **no** — puede avanzar hoy |

**V4 no requiere ninguna infraestructura y desbloquea cuatro P0.** Es la acción de mayor retorno inmediato mientras se provee el motor de BD.

---

# 18. Evidence index

## Comandos ejecutados

| Comando | Resultado |
|---|---|
| `pdftotext -layout` sobre 3 PDF del cliente | 96 elementos funcionales extraídos |
| Lector XLSX propio sobre 2 libros | 30 procesos codificados + confirmación de plantillas vacías |
| `pytest tests/test_environment_guard.py` | **24/24 PASS** |
| `pytest tests/test_auth.py` (4 escenarios de guarda) | **abortado exit 3** en los 3 peligrosos |
| `pytest --collect-only -q` | **100 tests** |
| `python -m compileall app seeds tests` | OK |
| `app.openapi()` | **176 operaciones** (168 + 8 PUT) |
| Script AST `Base.metadata` vs migraciones | 47 tablas, **0 deriva** |
| `ScriptDirectory.get_heads()` | `['i9j0k1l2m3n4']`, 1 base, 21 revisiones |
| `tsc -b --noEmit` | **exit 0** |
| `vitest run` | **61/61 PASS** |
| Comparación de `translation.json` | **865 = 865**, 0 faltantes |
| `backend/scripts/verify.sh` | **8/8 en verde** |
| `git diff --stat docker-compose.yml` | 13 inserciones, 0 eliminaciones |

## Artefactos producidos

**Validación y baseline:** `FUNCTIONAL_COVERAGE_MATRIX.md` (311 líneas) · `GLOBAL_AVICOLA_FUNCTIONAL_BASELINE_V1_1.md` (246) · `FE_BE_CONTRACT_MATRIX.md` (120)

**Certificaciones:** `GA-REM-{020,014,004,009,010,011,013}-CERTIFICATION-REPORT.md`

**Código nuevo:** `backend/tests/environment_guard.py` · `backend/tests/test_environment_guard.py` · `backend/seeds/test_seeds.py` · `backend/scripts/run_tests.sh` · `backend/scripts/verify.sh` · `.github/workflows/quality-gates.yml`

**Código modificado:** 13 archivos de aplicación (SAP ×3, masters ×2, operations ×2, config, seeds ×2, conftest, frontend ×8)

## Verificación del alcance excluido

```
.github/workflows/docker-*.yml modificados ..... 0
docker-compose.yml ............................. 13 inserciones, 0 eliminaciones
watchtower · pull_policy · :latest ............. 12 referencias, intactas
processCatalog.ts .............................. sin cambios
alembic/versions/ .............................. sin cambios
identificadores AVI-* introducidos ............. 0
migraciones nuevas ............................. 0
```

**`EX-01` y `RA-05` respetados, y verificados automáticamente por el job `scope-guard` en cada ejecución del CI.**
