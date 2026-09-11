# BACKLOG PRIORIZADO DE REMEDIACIÓN

Orden derivado de dependencias reales, no del número de spec. Los ajustes respecto al orden conceptual del encargo están justificados en `DEPENDENCY_MAP.md §6`.

Complejidad: XS (<2 h) · S (medio día) · M (1-3 días) · L (1-2 semanas) · XL (>2 semanas).
Riesgo: probabilidad de efectos colaterales al implementar.

## Backlog

| Orden | GA-REM | Título | Prior. | Dependencias | Compl. | Riesgo | Estado |
|---|---|---|---|---|---|---|---|
| **1** | `GA-REM-001` | Gobierno de Spec Development | P0 | — | S | bajo | **`CERTIFIED`** ✅ |
| **2** | `GA-REM-014` | Entorno de test backend aislado | P0 | 001 | M | medio | `SPEC_READY` |
| **3** | `GA-REM-020` | Validación de cobertura vs documentación del cliente (R-15) | P1 | 001 | M | **nulo** — documental | `SPEC_READY` |
| **4** | `GA-REM-004` | Credenciales y cuentas de prueba | P0 | 001 | S | **alto** | `SPEC_READY` |
| **5** | `GA-REM-009` | Persistencia de evidencias | P0 | 001 | S | bajo | `SPEC_READY` |
| **6** | `GA-REM-010` | Semántica de estados SAP | P0 | 001 | M | **alto** | `SPEC_READY` |
| **7** | `GA-REM-005` | Mortalidad y balance de aves | P0 | 001, 014, **023** | S | medio | `SPEC_READY` — `RC-02` resuelto |
| **8** | `GA-REM-011` | Alineación de contratos FE ↔ BE | P0 | 001, 014 | L | medio | `SPEC_READY` |
| **9** | `GA-REM-002` | RBAC: enforcement en backend | P0 | 001, 014 | L | **alto** | `SPEC_READY` |
| **10** | `GA-REM-003` | Contexto de autorización y token | P0 | 001, 014 | M | medio | `SPEC_READY` |
| **11** | `GA-REM-007` | BR-14: segregación | P0 | 001, 002, 014 | S | medio | `SPEC_READY` — `RC-03` resuelto |
| **12** | `GA-REM-012` | Cambio de contraseña | P0 | 001, 002, 003, 014 | S | medio | `SPEC_READY` — `RC-05` resuelto |
| **13** | `GA-REM-006` | Correcciones e integridad del dato | P0 | 001, 011, 014 | M | **alto** | `SPEC_READY` — `RC-01` resuelto |
| **14** | `GA-REM-008` | Trazabilidad generacional | P0 | 001, 011, 014 | M | medio | `SPEC_DRAFT` ⚠ `RC-04` |
| **15** | `GA-REM-013` | Quality gates de CI | P1 | 001, 014 | S | bajo | `SPEC_READY` |
| **16** | `GA-REM-015` | Certificación de tests backend | P1 | 014 | M | medio | **`CERTIFIED`** |
| **17** | `GA-REM-021` | Consumo de agua (R-13) | P1 | 001 | S | bajo | **`PARTIAL`** (`B05`, `B01`, `B02`, `B13` cerrados técnico, enm. A, B y C certificadas; `B03` ◄── `AOD-22` · `B04` ◄── `AOD-14` · `R-156` ◄── `AOD-20`) |
| **18** | `GA-REM-022` | Completitud de KPI (R-14) | P1 | 001, 011 | S | bajo | `SPEC_READY` |
| **19** | `GA-REM-016` | Certificación E2E y de procesos | P1 | 002, 005, 006, 007, 011, 014, 015 | L | medio | `SPEC_DRAFT` |
| **20** | `GA-REM-018` | Recuperación de trazabilidad Spec Dev | P1 | 001 + estabilización | L | bajo | `SPEC_READY` |
| **21** | `GA-REM-017` | Integración SAP real | P1 | 010, 011 + externo | XL | **alto** | **`BLOCKED_EXTERNAL`** |
| **22** | `GA-REM-019` | Reevaluación de deuda P2/P3 | P2 | Fases A–G | M | bajo | `DEFERRED` |

## Justificación del orden

**Posición 2 — habilitante antes que correctores.**
`014` desbloquea la verificación de once specs. Ejecutarla primero evita que esas specs lleguen a `IMPLEMENTED` y se queden ahí sin poder cerrarse por falta de evidencia (`NO VALIDATION = NO COMPLETE`).

**Posición 3 — validación temprana, sin bloquear.**
`020` **no es prerequisito de nadie**: la taxonomía del proyecto se conserva y sigue siendo la unidad de certificación (`RA-05`). Se ejecuta temprano por dos razones prácticas: su riesgo es nulo (no toca código) y puede revelar más huecos como R-13 y R-14, que conviene tener en el backlog **antes** de comprometer el alcance de certificación. Puede correr en paralelo con cualquier otra vía.

**Posiciones 4, 5 y 6 — vía paralela de riesgo activo.**
No dependen de `014`. Las tres reducen daño que se está produciendo **ahora mismo** en producción: credenciales públicas, evidencias que se pierden en cada despliegue y registros que se marcan como enviados a SAP sin haberlo sido. Dado que el despliegue automático se mantiene (`EX-01`), reducir el daño activo tiene prioridad sobre reparar funcionalidad.

**Posición 7 — mayor retorno operativo inmediato.**
`GA-REM-005` desbloquea la operación diaria más frecuente del negocio con complejidad S. Es el primer punto donde el usuario final percibe una mejora.

**Posición 8 antes que 9 — contratos antes que RBAC.**
`011` repara cinco pantallas caídas y es prerequisito de `006`, `008` y `022`. `002` es más arriesgada: al activar el enforcement, un permiso mal sembrado bloquea a operadores reales. Conviene tener las pantallas operativas y la suite de tests en verde antes de tocar la autorización.

**Posiciones 11 a 14 — dependientes de decisiones de negocio.**
Sus specs están redactadas; esperan resolución de `RC-01`, `RC-03`, `RC-04` y `RC-05`. **No requieren trabajo técnico para desbloquearse: requieren una decisión.**

**Posición 19 — punto de convergencia.**
`GA-REM-016` es donde el programa demuestra su resultado: el primer proceso de negocio certificado. Depende de ocho specs previas.

**Posición 21 — bloqueada por el cliente.**
`GA-REM-017` no puede especificarse sin el contrato técnico de SAP. Se marca `BLOCKED_EXTERNAL` y no se simula (Art. 21.3 de la constitución). El trabajo interno que sí puede avanzar está listado en su propia spec.

## Cobertura de hallazgos

| Bloqueador de la auditoría | Spec que lo cubre |
|---|---|
| P0-1 mortalidad → 500 | `GA-REM-005` |
| P0-2 correcciones no aplicadas | `GA-REM-006` |
| P0-3 sin RBAC | `GA-REM-002` |
| P0-4 escalada por refresh | `GA-REM-003` |
| P0-5 cinco pantallas rotas (422) | `GA-REM-011` |
| P0-6 evidencias efímeras | `GA-REM-009` |
| P0-7 SAP simulado en producción | `GA-REM-010` (semántica) + `GA-REM-017` (real) |
| P0-8 credenciales públicas | `GA-REM-004` |
| P0-9 contraseña que no cambia | `GA-REM-012` |
| P0-10 BR-14 eludible | `GA-REM-007` |
| P0-11 trazabilidad auto-referencial | `GA-REM-008` |
| P0-12 sin puerta de calidad | `GA-REM-013` **parcialmente** — la parte de despliegue es `OUT_OF_SCOPE` (`EX-01`) |
| R-13 consumo de agua (nuevo) | `GA-REM-021` |
| R-14 Tasa de Eclosión (nuevo) | `GA-REM-022` |
| R-15 documentación del cliente sin usar para validar (nuevo) | `GA-REM-020` |

**15 de 15 hallazgos tienen spec asignada.** R-15 no es bloqueante: es una validación que alimenta el backlog. P0-12 queda cubierto solo en su dimensión de señal de calidad; su dimensión de puerta de despliegue es riesgo aceptado.

## Riesgos P1 de la auditoría y su destino

| Riesgo P1 | Destino |
|---|---|
| P1-1 migraciones no automatizadas | `GA-REM-013` §alcance, con la limitación de `EX-01` |
| P1-2 fuga multi-compañía | `GA-REM-002` AC05 |
| P1-3 Super Admin ciego en 6 módulos | `GA-REM-002` |
| P1-4 sin logout ni revocación | `GA-REM-003` |
| P1-5 observabilidad nula | `GA-REM-019` — **recomendado adelantar** |
| P1-6 sin backups | `GA-REM-019` — **recomendado adelantar** |
| P1-7 CI de backend inejecutable | `GA-REM-014` + `GA-REM-013` |
| P1-8 BR-11 y BR-12 inertes | `GA-REM-011` AC05, AC06 |
| P1-9 BR-06 anulada | `GA-REM-005` AC06 |
| P1-10 ocho catálogos sin edición | `GA-REM-011` AC07 |
| P1-11 rate limit apagado | `GA-REM-004` AC03 |
| P1-12 auditoría duplicada e incompleta | `GA-REM-003` AC06 + `GA-REM-019` |
| P1-13 aprobación multinivel no operativa | `GA-REM-019` — candidata a spec propia |
| P1-14 BD pública con superusuario | `GA-REM-004` AC07 |
| P1-15 activación manual sin UI | `GA-REM-019` — candidata a spec propia |
| P1-16 filtros de UI inertes | `GA-REM-011` AC04 |

---

# ANEXO — HALLAZGOS INCORPORADOS EN WAVE 1

Descubiertos por `GA-REM-020`. **Ninguno se implementó en Wave 1** (§32 del encargo).

| ID | Hallazgo | Sev. | Destino | Estado |
|---|---|---|---|---|
| `R-13` | Consumo de agua no capturado en 3 etapas | P1 | `GA-REM-021` · `GA-REQ-057` | **CERRADO** (técnico; WAVE B tranche 6, `GA-REM-021-A`) |
| `R-14` | Tasa de Eclosión devuelve texto en vez de número | P1 | `GA-REM-022` | Wave 2 |
| `R-15` | Documentación del cliente sin usar para validar | P1 | `GA-REM-020` | **cerrado** |
| `R-16` | Rotación de huevos: solo booleano; faltan frecuencia y ángulo | P2 | `GA-REM-021` (ampliada) · `GA-REQ-058` | Wave 2/3 |
| `R-17` | 12 KPI exigidos por el cliente en `PARTIAL`: 5 implementados sin consumidor, 7 nunca calculados | P1 | `GA-REM-022` (ampliada) | Wave 2 |
| `R-18` | No existe curva de peso estándar, pese a que `spec.md §4.5` exige la alerta | P2 | backlog | Wave 3 |
| `R-19` | Sin validación de unidad de medida | P3 | backlog | Wave 3 |
| `R-20` | No se consume ningún maestro ni inventario de SAP: 6 de 17 reglas del cliente inaplicables | P1 | `GA-REM-017` | `BLOCKED_EXTERNAL` |
| `R-21` | `SapPayload` declara 3 campos anti-duplicados y ninguno se poblaba | P1 | `GA-REM-010` | **cerrado en Wave 1** |
| `R-22` | Sin bandera de riesgo manual en la inspección | P2 | backlog · `GA-REQ-060` | Wave 3 |

## Desajustes de contrato diferidos (`GA-REM-011`)

| ID | Desajuste | Motivo del diferimiento | Wave |
|---|---|---|---|
| `C-10`…`C-14` | Filtros inertes en Revisión y Auditoría | cambian la semántica de consulta; requieren decisión de comportamiento | 2 |
| `C-15` | `sap_document_ref` nunca enviado | **activa BR-11 y BR-18**, hoy inertes: cambio de comportamiento de negocio | 2 |
| `C-16` | `idempotency_key` nunca enviado | decisión de diseño: idempotencia del lado servidor (`GA-REQ-059`) | 2 |
| `C-18` | Envoltorio `{items, total}` no uniforme | cambio de contrato amplio: 4 módulos y todos sus consumidores | 2 |

## Elementos diferidos de otras GA-REM de Wave 1

| Origen | Elemento | Motivo |
|---|---|---|
| `GA-REM-004` AC07 | Rol de BD con privilegios mínimos y SSL obligatorio | acción de infraestructura fuera del repositorio |
| `GA-REM-009` AC04 | Manejo de evidencia huérfana en la descarga | fuera del alcance mínimo de Wave 1 |
| `GA-REM-009` AC07 | Inventario de evidencias huérfanas en producción | requiere acceso a la base productiva |
| `GA-REM-010` AC07 | Saneamiento de los eventos con referencia `MANUAL-*` | requiere acceso a la base productiva |
| `GA-REM-013` AC02 | Corregir los 5 errores de ESLint | deuda preexistente; §26 prohíbe el cleanup general en Wave 1 |

## `NEW_REQUIREMENT_DISCOVERY`

Ninguno posterior al congelamiento del baseline V1.1. Los 4 `GA-REQ` nuevos (`057`–`060`) se incorporaron **antes** del congelamiento, como parte de `GA-REM-020`.

## Acciones operativas fuera del repositorio

| # | Acción | Origen |
|---|---|---|
| 1 | Rotar las contraseñas de las cuentas existentes en el entorno desplegado | `GA-REM-004` |
| 2 | Verificar 6 intentos de login → 429 | `GA-REM-004` AC03 |
| 3 | Rotar credenciales de BD y SMTP de los `.env` locales | `GA-REM-004` |
| 4 | Rol de aplicación con privilegios mínimos + SSL | `GA-REM-004` AC07 |
| 5 | Entregar las credenciales de prueba por canal seguro | `GA-REM-004` |
| 6 | **Proveer un motor PostgreSQL de pruebas** (local, contenedor o instancia dedicada) | **`GA-REM-014` — bloquea Wave 2** |
| 7 | Decidir `RC-01`, `RC-02`, `RC-03`, `RC-05`, `RC-07` | negocio |
| 8 | Corregir la ambigüedad de `spec.md §4.9` (`RC-04`) | spec |
| 9 | Solicitar al cliente el contrato técnico de SAP | `GA-REM-017` |


---

# Orden recalculado de la Wave 2 — desde la evidencia de ejecución

La Wave 1.5 cambió el orden porque cambió lo que se sabe. Este orden **no** procede del
plan original: procede de lo que la primera ejecución real de la suite y la resolución de
los `RC` pusieron sobre la mesa.

| # | Trabajo | Por qué aquí | Bloquea a | Tamaño |
|---|---|---|---|---|
| **1** | **`R-28`** — fechas relativas en los tests (cierre de `GA-REM-015`) | **tiene fecha límite: 2026-09-21.** `BR-19` cierra períodos a los 90 días y los tests usan fechas literales de junio de 2026. Pasada esa fecha, decenas de tests hoy en verde fallarán solos y la línea base RUN 05 dejará de ser reproducible | **todo lo demás** — sin línea base estable no se puede medir ninguna corrección | XS |
| **2** | **`GA-REM-023`** — `P0-14` + `R-26` | mayor apalancamiento del programa. `R-26` convierte 7 reglas de negocio de 500 a 400: eso transforma 11 fallos de test en aserciones con sentido. `P0-14` restituye `cause_id`, sin el cual `GA-REM-005` no puede registrar la causa de mortalidad | `005`, `006`, y la legibilidad de la mitad de la suite | M |
| **3** | **`GA-REM-005`** — mortalidad y balance | `P0-1` confirmado en runtime; ningún test lo recorre hoy. Depende de `023` para `cause_id` | `016` | M |
| **4** | `GA-REM-002` — RBAC | absorbe `R-25` (`PUT /users/{id}` sin autorización). Habilita `007` y `012` | `007`, `012`, `016` | L |
| **5** | `GA-REM-003` — contexto de autorización y token | habilita `012` | `012` | M |
| **6** | `GA-REM-012` — cambio de contraseña | `P0-13` confirmado en runtime: la API responde `200` y no cambia nada. `RC-05` resuelto (`RR-05`) | — | S |
| **7** | `GA-REM-006` — correcciones | `RC-01` resuelto (`RR-01`); la pantalla ya carga desde Wave 1 | `016` | M |
| **8** | `GA-REM-007` — `BR-14` | `RC-03` resuelto (`RR-03`); incorpora `R-23` (`complete_review` elude la regla) | `016` | S |
| **9** | `GA-REM-011` — 8 desajustes de contrato restantes | diferidos por alcance, no por conflicto | `016` | M |
| **10** | `GA-REM-008` — trazabilidad generacional | único `RC` de spec pendiente (`RC-04`) | `016` | M |

## Qué cambió respecto del orden anterior

| Cambio | Motivo |
|---|---|
| **`GA-REM-023` entra en el puesto 2** y no existía | `P0-14` y `R-26` se descubrieron en Wave 1.5 |
| **`R-28` pasa al puesto 1** | tiene fecha límite dura; nada más lo tiene |
| `GA-REM-005` gana una dependencia de `023` | sin `cause_id` persistido, la mortalidad no puede registrar la causa que el cliente exige |
| `006`, `007`, `012` dejan de estar marcadas con ⚠ | sus `RC` están resueltos |
| `GA-REM-015` sale del backlog | **`CERTIFIED`** |
| `GA-REM-014` sale del backlog | **`CERTIFIED`** |

## Lo que sigue esperando a alguien que no somos nosotros

| ID | Espera | Bloquea |
|---|---|---|
| `OD-02` (`RC-07`) | decisión contable del propietario sobre mortalidad frente a SAP | solo el mapeo SAP dentro de `GA-REM-017` |
| `RC-04` | corrección de la redacción de `spec.md §4.9` | `GA-REM-008` |
| Contrato técnico SAP | el cliente | `GA-REM-017` |
| `OD-01`, `OD-03` | decisiones de endurecimiento, sin urgencia | nada |


---

# Estado tras la Wave 2 (2026-09-04)

## Cerrado

| GA-REM | Estado |
|---|---|
| `001`, `004`, `009`, `010`, `013`, `014`, `015`, `020` | `CERTIFIED` (Waves 1 y 1.5) |
| **`003`**, **`006`**, **`007`**, **`008`**, **`012`**, **`023`** | **`CERTIFIED`** (Wave 2) |
| **`005`** | **`PARTIALLY CERTIFIED`** — `AC08` (umbral configurable) diferido a `019` |
| **`002`** | **`IMPLEMENTED`** — condicionado a `R-44`, prerrequisito de despliegue |
| `011` | `PARTIALLY CERTIFIED` — 8 desajustes diferidos por alcance |

## Backlog vigente

| # | Trabajo | Prior. | Motivo |
|---|---|---|---|
| **1** | **`R-44`** — completar el catálogo de permisos en producción | **bloqueante** | sin él, el enforcement RBAC deja fuera a todo usuario que no sea Super Admin. Bloquea también la certificación E2E |
| 2 | `GA-REM-016` — certificación E2E y de procesos | P1 | único camino al nivel de madurez 4. Sus dependencias funcionales están ya en verde |
| 3 | `GA-REM-011` — 8 desajustes de contrato restantes | P1 | diferidos por alcance desde la Wave 1 |
| 4 | `GA-REM-018` — recuperación de trazabilidad metodológica | P1 | deuda Spec Development: 9 |
| 5 | `GA-REM-021` (agua) · `GA-REM-022` (KPI) | P1 | reevaluados: ya no compiten con ningún P0 |
| 6 | **`GA-TD-039` / `GA-TD-040`** — observabilidad y respaldo | **P1, al alza** | con `EX-01`, la falta de observabilidad es lo que hace que un despliegue defectuoso pase inadvertido. `R-26` lo demuestra: siete reglas devolvían 500 y nadie lo supo |
| 7 | `GA-REM-019` — deuda P2/P3 | P2 | acumula 9 hallazgos nuevos de la Wave 2 |
| 8 | `GA-REM-017` — SAP real | P1 | `BLOCKED_EXTERNAL` + `OD-02` |

## Lo que sigue esperando a alguien que no somos nosotros

| ID | Espera | Bloquea |
|---|---|---|
| `R-44` | inventario y actualización de permisos en la base de producción | despliegue del RBAC · `GA-REM-016` |
| `OD-02` (`RC-07`) | decisión contable del propietario sobre mortalidad frente a SAP | mapeo SAP dentro de `GA-REM-017` |
| Contrato técnico SAP | el cliente | `GA-REM-017` |
| `OD-01`, `OD-03` | decisiones de endurecimiento, sin urgencia | nada |


---

## Checkpoint `R-68` + `R-67` (2026-09-04)

Dos specs cerradas, ambas nacidas del baseline limpio de `GA-REM-025`:

| GA-REM | Título | Prior. | Estado |
|---|---|:--:|---|
| `GA-REM-026` | Frontera transaccional de la petición (`R-68`) | **P0** | **`CERTIFIED`** |
| `GA-REM-005` | Enmienda `R-67`: el saldo de apertura alimenta el balance | P1 | **`CERTIFIED`** |

`GA-REM-005` pasa de `PARTIALLY CERTIFIED` a `CERTIFIED`: su alcance §2 —«reconstruir y
documentar la regla de balance de aves»— queda completo con `R-67`.

### Deuda añadida a `GA-REM-019`

| ID | Título | Prior. |
|---|---|:--:|
| `R-63` | Tabla de credenciales falsa impresa por `dev_seeds.py` | P2 |
| `R-64` | `integration_seeds.py` roto (`KeyError: 'role_name'`) | P2 |
| `R-65` | 500 en `/audit/{log_id}` con identificador no-UUID | P2 |
| `R-66` | `/me` devuelve la empresa persistida, no la activa | P3 |
| `R-69` | La validación del saldo de apertura rechaza datos legítimos | P2 |
| `R-70` | 500 en `activate-manual` con una fase inexistente | P2 |
| `R-73` | El cierre de lote respondía 500 siempre | P1 — **`CERTIFIED`** `GA-REM-029` |
| `R-74` | `BR-05` validaba el evento `lot_closure`, que no cierra el lote | P1 — **`CERTIFIED`** `GA-REM-029` |
| `R-75` | `end_date` se guardaba a medianoche local y se releía como del día anterior | P1 — **`CERTIFIED`** `GA-REM-029` |
| `R-76` | `docs/12 R7` sin implementar: un lote se cierra con registros sin aprobar | P1 — **`CERTIFIED`** `GA-REM-036` |
| `R-77` | «no duplicar documentos SAP» es `BR-11` en la spec y `BR-10` en el código | P2 — **abierto** |
| `R-60` | Los vínculos de trazabilidad no comprobaban pertenencia ni existencia | P2 — **`CERTIFIED`** `GA-REM-030` |
| `R-78` | El vínculo generacional automático no se crea en el orden natural (despacho → recepción) | P1 — **`CERTIFIED`** `GA-REM-031` |
| `R-79` | La prueba de `GA-REM-008 AC01` no podía fallar | P2 — **`CERTIFIED`** `GA-REM-016` enm. F |
| `R-80` | La fecha de negocio se ancla al día local del servidor y `created_at` a UTC: entre una medianoche y otra, `start_date` queda por delante del alta | P2 — **abierto** |
| `R-81` | Seis de los once módulos declarados no producían ningún registro de auditoría | P1 — **`CERTIFIED`** `GA-REM-032` |
| `R-82` | La vista de auditoría aparentaba filtrar y no filtraba | P1 — **`CERTIFIED`** `GA-REM-032` |
| `R-83` | `AuditLog.company_id` no es nulable: una acción no atribuible a ninguna empresa no puede auditarse | P2 — **abierto** |
| `R-84` | El filtro de fecha comparaba `timestamptz` con texto y devolvía 500 | P1 — **`CERTIFIED`** `GA-REM-032` |
| `R-14` | La tasa de eclosión devolvía texto en un campo numérico | P1 — **`CERTIFIED`** `GA-REM-022` |
| `R-85` | Eclosión, nacimiento y rendimiento tienen denominadores distintos y se fundían en uno | P2 — **`CERTIFIED`** `GA-REM-022` |
| `R-86` | «Fertilidad» era normativa y no tenía productor | P2 — **`CERTIFIED`** `GA-REM-022` |
| ~~`R-87`~~ | ~~El reporte de estados no tiene productor~~ | **RETIRADO** — existe en `event_summary.by_status` |
| ~~`R-88`~~ | ~~La exportación Excel/PDF no existe~~ | **RETIRADO** — existe en el cliente (`utils/export.ts`) |
| `R-89` | El listado de maestros descarta el total y el contador muestra el tamaño de página | P2 — **`CERTIFIED`** `GA-REM-033` |
| `R-90` | Siete maestros normativos sin capacidad de gestión | P1 — **`CERTIFIED`** `GA-REM-033` |
| `R-91` | Esos mismos siete no admitían edición: sin esquema, no hay `PUT` | P2 — **`CERTIFIED`** `GA-REM-033` |
| `R-92` | No existía superficie para administrar roles | P1 — **`CERTIFIED`** `GA-REM-034` |
| `R-93` | `RoleUpdate` no incluía permisos: un rol no podía cambiarlos nunca | P2 — **`CERTIFIED`** `GA-REM-034` |
| `R-94` | No había catálogo de permisos | P2 — **`CERTIFIED`** `GA-REM-034` |
| `GA-TD-014` | La OC no llegaba al campo tipado; el límite no era acumulado | P1 — **`CERTIFIED`** `GA-REM-035` |
| `R-95` | `SapReferenceCreate` no declaraba `quantity`: `BR-18` era inaplicable | P1 — **`CERTIFIED`** `GA-REM-035` |
| `R-96` | La capacidad de cargar la tabla de curva **no existe en el producto**: solo por API | **P1** — **`CERTIFIED`** `GA-REM-037` enmienda A |
| `R-97` | La evaluación de curva solo es observable cuando genera alerta: `WITHIN` y `NO_REFERENCE` son indistinguibles | **P1** — **`CERTIFIED`** `GA-REM-037` enmienda A |
| `R-98` | Ninguna pantalla oculta acciones de escritura por permiso: no hay modelo de permisos en el frontend | P2 — `OPEN` · transversal, pertenece a `P-13` |
| `R-99` | El frontend del entorno compartido no sigue a `main`: artefacto servido congelado desde el 2026-09-05, con tres entregas después | **P1** — `BLOCKED_BY_OUT_OF_SCOPE_DEPLOYMENT` · `EX-01` |

`R-65` y `R-70` son el mismo patrón —entrada no validada que termina en 500— y conviene
tratarlos juntos.

## Frente de mayor palanca pendiente

`GA-TD-014` fue el frente de mayor palanca —bloqueaba `P-01`, `P-03` y `P-06`— y está
**cerrado** desde `OD-04` y `GA-REM-035`. Con `OD-06` resuelta y `GA-REM-037` entregada, `P-03`
queda certificado y ningún bloqueante técnico pendiente alcanza fan-out 2.

Lo que queda de mayor alcance es una **decisión de negocio abierta**, no una tarea:

```
RC-07  · ¿la mortalidad se envía a SAP?   sigue sin resolver, y es un asunto distinto de OD-04
OD-05  · política de escalada de privilegios   abierta desde P-13
```

El resto del backlog son hallazgos de fan-out 1: `R-69`, `R-70`, `R-77`, `R-80`, `R-83`.

`R-96` y `R-97` tuvieron consecuencia de proceso —`P-03` volvió a `PARTIAL`— y están cerrados
desde el 2026-09-06. Ver la corrección de gobernanza al final de este documento.

`R-98` es su residuo: al verificar `AC-FE16` se comprobó que **ninguna** pantalla de la
aplicación oculta acciones de escritura según el permiso del usuario, porque `/me` no expone la
lista de permisos. No es un defecto de las curvas sino transversal, y pertenece a `P-13`. No
impide el acceso: el backend niega y la interfaz presenta la negativa.


---

## Corrección de gobernanza · `R-96` reclasificado (2026-09-06)

`R-96` se registró como `P2 · sin spec de frontend`, apoyándose en que `GA-REM-037` no tenía
criterios de interfaz. **El razonamiento estaba invertido.**

`OD-06` dice que cada línea genética puede tener su tabla de curva y que esa tabla **debe poder
cargarse dentro de Global Avícola**. Que la spec no desarrollara ese punto no elimina el
requisito: demuestra que la spec estaba incompleta.

```
OWNER REQUIREMENT  >  INCOMPLETE SPEC
```

De modo que:

```
R-96 = MISSING PRODUCT CAPABILITY + SPEC COVERAGE GAP     no "deuda técnica", no "backlog"
```

Y su consecuencia sobre el proceso:

```
P-03 = PARTIAL     hasta que la capacidad exista en el producto
```

Certificar `P-03` porque `POST /masters/weight-curves` responde `201` habría sido exactamente
lo que `GA-REM-016 AC05` prohíbe: *«ninguna unidad certificada es una pantalla, un endpoint o
un componente»*. El endpoint funciona; el proceso no está completo mientras el administrador no
pueda ejecutarlo desde el producto.

`R-97` apareció al derivar el contrato de esa pantalla y es de otra clase —el backend calcula
la evaluación y no la expone salvo cuando alerta—. Los dos se cierran por la enmienda A de
`GA-REM-037`, que es la autoridad natural de `OD-06`.


---

## `P-14` · el canal existe, el proceso no (2026-09-07)

`OD-07` resolvió que Global Avícola notifica **por dentro**, y `GA-REM-038` lo construyó:
bandeja, campana, contador, lectura, aislamiento por destinatario y `UI_E2E`. Nada de eso
certifica `P-14`.

`docs/02 §3.14` enumera seis tipos de aviso. Al derivar cada uno de sus fuentes —no de la
intuición— solo dos dicen a quién avisar:

| Tipo | Disparador | Destinatario |
|---|:--:|---|
| Registro rechazado | sí | «al operador» — `docs/02 §3.14` |
| Error de envío SAP | sí | rol `Analista SAP` — `docs/10 §6.2` |
| Mortalidad > umbral | sí | **sin definir** |
| Peso fuera de estándar | sí | **sin definir** |
| Pendiente de revisión > 24 h | **no** (temporal, sin planificador) | sin definir |
| Lote próximo a cierre | **no**, y «próximo» tampoco está definido | sin definir |

```
OD-08 = OWNER_DECISION_REQUIRED
P-14  = PARTIAL
```

Se descartaron por escrito tres destinatarios candidatos —`registered_by_id`, el rol
`Supervisor Avícola` y «todos los administradores»— porque ninguno sale de una fuente.
Notificar a la persona equivocada es peor que no notificar: parece que el sistema avisa.


---

## `OD-08` · destinatarios resueltos, semántica temporal abierta (2026-09-07)

`OD-08` fijó a quién avisa `P-14`: quien cargó el dato, los administradores, la contraloría, el
gerente del área y el supervisor de esa empresa. En unión con lo que otras fuentes ya exigían, y
deduplicado — una persona, un aviso.

Al mapear los términos contra los roles reales, cuatro de las cinco funciones resultaron
resolubles y una no:

```
gerente del área    BLOCKED_BY_MODEL_GAP
                    no hay tabla de área, departamento ni unidad organizativa,
                    y el usuario solo se asocia a una empresa y a un rol
```

Y releer los nombres literales de `docs/02 §3.14` desbloqueó uno de los dos eventos temporales:
«Registro pendiente de revisión **> 24h**» lleva su umbral en el nombre. «Lote próximo a cierre»
no: la única aparición de la frase en el repositorio es la línea que la enumera.

```
P-14: 2 de 6 tipos  →  5 de 6

Sigue abierto:
  · OD-08 · qué es «lote próximo a cierre»
  · OD-08 · si el aviso de «> 24h» se repite (mientras tanto, una vez)
  · modelo de área y rol de gerencia, para AC-R04
```

De paso queda anotado un desfase anterior a este trabajo: `docs/02 §6.1` enumera **once** roles
y hay **seis** sembrados. No se corrige aquí — `GA-REM-034` permite crearlos y el resolutor
funciona con los que existan.


---

## `OD-08` completa · `P-14` certificado (2026-09-07)

Los dos bloqueos que quedaban eran de clase distinta, y tratarlos igual habría llevado a pedir
al propietario algo que no era suyo:

```
«lote próximo a cierre»   una DECISIÓN   →  OD-08: tres días antes de la fecha prevista
gerente del área          un MODELO      →  GA-REM-039: el área no existía
```

```
P-14: 5 de 6 tipos  →  6 de 6      CERTIFIED
```

Queda un hueco de requisito que **no bloquea**: ninguna fuente dice si el aviso de «> 24h» se
repite. Se emite una vez, con idempotencia.

Y queda `R-99`: el frontend del entorno compartido sigue por detrás de `main`, de modo que el
**runtime compartido** de la interfaz de `P-14` está `NOT VERIFIED`. La certificación es del
entorno aislado, que es donde el programa ejecuta sus suites.

## `GA-REM-040` especificada · la cola cambia de forma (2026-09-07)

Hasta aquí el backlog era una lista de **defectos**. `GA-REM-040` es lo primero que entra siendo
una **capacidad que falta**, y eso cambia cómo se prioriza: no hay nada roto que arreglar, hay
algo que no existe.

```
GA-REM-040    SPEC_READY · 30 tareas · 11 fases · 0 líneas de código
```

### Lo que sale del backlog

```
BU-D01 · BU-D02 · BU-D09 · BU-D11 · BU-D12     resueltas → OD-09 y OD-10
```

### Lo que se queda, y por qué no urge

```
BU-D03 · BU-D04 · BU-D06 · BU-D07 · BU-D08 · BU-D10
```

Ninguna bloquea. `OD-09` y `OD-10` dieron los mecanismos con los que se resuelven durante la
construcción: la transversalidad concedida explícitamente cubre `BU-D03` y `BU-D04`; el estado de
clasificación pendiente cubre `BU-D06`; el plano de control cubre `BU-D07`. `BU-D08` quedó
acotada como extensión futura, y `BU-D10` tiene sus reglas operativas fijadas y le falta solo la
formalización.

### Lo que sigue abierto de antes

```
OD-05     quién puede conceder qué permiso — abierta desde Wave 2, nunca bloqueante
R-69 · R-70 · R-77 · R-80 · R-83 · R-98 · R-99
R-100 … R-110     hallazgos de la auditoría de acceso; los cierra GA-REM-040 por fases
P-08      BLOCKED_EXTERNAL · GA-REM-017 · contrato SAP
BU-D05    gate FIRST_REAL_CUSTOMER_READINESS
```

### Frente de mayor palanca

```
GA-REM-040 FASE 1 — fundamento
catálogo · habilitación por empresa · concesión por usuario · resolutor central
```

Y con una condición que la spec deja escrita: **la fase 4, los agregados, no puede ir al final.**

## `R-111` · el sub-recurso no heredaba la pertenencia de su padre (2026-09-07)

```
CLASE          PERTENENCIA DE INQUILINO / RECURSO — IDOR PREEXISTENTE
NO ES          hueco de aislamiento por unidad de negocio
SEVERIDAD      P1
SPEC           GA-REM-002 · enmienda A · AC12   (no hace falta GA-REM nuevo)
DESCUBIERTO    siguiendo la cadena de seguridad de GA-REM-040 fase 3
ANTERIOR A     GA-REM-040
ESTADO         CORREGIDO · con pruebas · sin certificación nueva
```

### Un hallazgo raíz, tres superficies

No son tres defectos: es **una omisión repetida** en el mismo router, y por eso se registra
como uno solo con sus tres manifestaciones.

| Superficie | Qué hacía | Principio que incumplía |
|---|---|---|
| `GET /lots/{id}/phases` | consultaba por `lot_id` sin comprobar **nada** | `AC05` — lectura de recurso ajeno |
| `GET /lots/{id}/opening-balance` | ídem | `AC05` |
| `POST /lots/{id}/phases` | creaba la fila sin comprobar de quién era el lote | `AC10` — escritura contra lo ajeno |

### La causa raíz, dicha con precisión

La ruta **sí** exigía sesión y permiso: el fallo no era de autenticación ni de `RBAC`.

```
AUTENTICACIÓN DE RUTA        existía
PERMISO RBAC                 existía
PERTENENCIA DEL PADRE        NO se comprobaba en el camino anidado
```

`GA-REM-002` ya había narrado esta lección para las claves foráneas —«existir no basta», «la
lección no se extendió»— y quedó sin extender un nivel más abajo:

```
DETALLE PROTEGIDO   ≠   SUB-RECURSO PROTEGIDO
```

### Lo que NO se registra como defecto de producto

Al escribir las pruebas aparecieron cuatro fallos que eran de la **fixture**, no del sistema, y
se corrigieron sin registrarlos como hallazgos: `limit` topa en 100, `LotUpdate` no acepta
`notes`, faltaba el permiso `lots:create` —la denegación habría venido de la capa equivocada— y
faltaba un campo obligatorio en la activación manual.

Se dejan escritos por método, no por trazabilidad de defecto: **un rojo que viene de la capa
equivocada no demuestra nada**, y comprobarlo antes de usarlo como evidencia es parte del gate.

### `T-073-06`

Su **control** empezó a fallar en la fase 3 —el sujeto no podía cerrar ni su propio lote— porque
carecía de unidades concedidas. Es `OD-09.c` funcionando, no una regresión: se le configuró la
empresa, que es lo que hará un cliente real en su alta. **La prueba no se debilitó.**

## `R-112` · ocho superficies SAP sin proyección declarada (2026-09-07)

```
CLASE        CONTRATO DE RESPUESTA NO DECLARADO
SEVERIDAD    P2
DESCUBIERTO  mutación de sensibilidad de `OD-12` · flujo 5
ESTADO       1 de 9 corregida · 8 registradas
```

### Qué pasa

Nueve de las diez rutas de `/api/v1/sap/` no declaran `response_model`: devuelven objetos `ORM`
crudos que `FastAPI` serializa con lo que el modelo tenga en ese momento.

```
✓ corregida    /consolidated   — es la superficie del contrato transversal (`AC-SAP08`)
✗ pendientes   /references · /references/import · /consolidate · /retry
               /sync/jobs · /payloads · /errors · /connection-check
```

### Por qué no filtra **hoy**, y por qué importa igual

`ConsolidatedMovement` no tiene relaciones, y sus columnas coinciden con el esquema. Es decir: la
respuesta era correcta **por coincidencia**, no por contrato. Una relación nueva, o una columna
añadida al modelo, habrían empezado a viajar sin que nadie lo decidiera — y en una superficie
transversal, donde el actor alcanza filas de las cuatro cadenas, eso es exactamente lo que no
puede pasar.

Lo detectó una mutación: añadir un campo al esquema **no rompió nada**, porque el esquema no se
estaba aplicando.

### Por qué las otras ocho no se corrigen aquí

Cambiar ocho formas de respuesta sin pruebas que las sujeten es un riesgo que no corresponde a
esta tanda: el frontend las consume y la fase 9 es la que lo gobierna. Se corrigió la del
contrato porque `AC-SAP08` la exige y porque su equivalencia de campos es verificable.

```
DESTINO   fase 7 o tanda propia, con cobertura de contrato de respuesta
```

---

## `R-113` · nadie administra el acceso por unidad salvo el Super Admin (2026-09-08)

```
CLASE        DECISIÓN DE PROPIETARIO PENDIENTE  ·  no es un defecto de código
SEVERIDAD    P2
DESCUBIERTO  `GA-REM-040` fase 7 · lo señaló `test_rbac.py` al exigir coherencia de roles
ESTADO       REGISTRADO — la capacidad funciona; falta decidir quién la ejerce
```

### Qué pasa

La fase 7 añade las cuatro superficies de administración y su módulo `RBAC` propio
(`business_units:read` · `update` · `create` · `delete`). **Ningún rol sembrado las tiene.**

`test_rbac.py` exige que todo permiso que una ruta reclame lo conceda algún rol o conste como
exclusivo del Super Administrador. Al no haber rol, las cuatro entraron en `SOLO_SUPER_ADMIN`, y
eso hizo saltar el segundo guardián —el que vigila que esa lista no crezca— con el diagnóstico
correcto: **falta un rol administrativo**.

### Por qué no se inventó uno

Ninguno de los cinco roles sembrados administra accesos:

```
Supervisor Avícola   supervisa producción
Operador de Granja   registra en campo
Aprobador            aprueba registros
Analista SAP         opera la integración
Auditor              lee
```

Y no es una cuestión de encaje estético. `business_units:create` permite conceder a cualquier
usuario de la empresa, incluido uno mismo —`§51` lo comprueba y lo documenta—, de modo que
dárselo a «Supervisor Avícola» convertiría a todo supervisor en alguien capaz de concederse las
cuatro cadenas. Eso no es configurar un rol: es decidir el modelo de autoridad de la empresa.

### La pregunta que va al propietario

```
¿Quién administra el acceso por unidad de negocio en una avícola?
¿La misma figura que administra usuarios, o una distinta?
¿Puede esa figura concederse unidades a sí misma, o hace falta separarlo?
```

La tercera no es teórica: hoy la respuesta es **sí puede**, por la política vigente, y queda
auditada con actor y objetivo. Separarlo sería una decisión, no una corrección.

### Mientras tanto

El valor por defecto es **cerrado**, que es el lado correcto en el que equivocarse. El permiso
consta en el catálogo (`AuthService.MODULOS`), de modo que el propietario puede crear el rol que
corresponda a su organización desde `/roles` sin tocar código. Y el Super Administrador puede
administrar una empresa situándose en ella con `switch-company`, que deja rastro en `P-09`.

**No lo resuelve la fase 7.** Decidir quién manda no es trabajo de quien implementa.

---

# AUDITORÍA MAESTRA DE SPEC/PRODUCTO — 2026-09-08

Doce hallazgos. Ninguno estaba registrado; ninguno tiene prueba que lo cubra. Todos verificados
sobre el código en `HEAD = e245157`, sin modificar nada.

**El hilo común de los cinco primeros:** el filtro de empresa nunca llegó a la superficie de
administración. `docs/02 §3.1.4` lo declara CRÍTICO y exige `WHERE company_id = ?` en *todas*
las consultas; `/users` y `/masters/companies` no lo aplican.

**Por qué convivieron con 687 pruebas verdes y tres guardas de arranque:** ninguna guarda vigila
el filtro de inquilino, y `users:read/create/update` constan en `SOLO_SUPER_ADMIN`, de modo que
en las semillas solo los alcanza quien legítimamente ve todo. **Están latentes, no ausentes**:
se activan el día que se responda `R-113` y alguien cree un rol de administración.

## `R-114` · `P0` · `/users` no filtra por empresa
`AuthService.get_users` → `select(User)` sin `where` de empresa. `get_user` tampoco. Quien tenga
`users:read` enumera nombre, correo, teléfono, rol y empresa de **todos** los inquilinos.
Contradice `RQ-03` / `02 §3.1.4`. Sin remediación existente.

## `R-115` · `P0` · `/masters/companies` no acota y expone `sap_config`
`Company` no tiene columna `company_id`, así que `hasattr(self.model, "company_id")` es falso y
`_apply_company_filter` es un **no-op** sobre ese maestro. `masters:read` lo tienen los cinco
roles sembrados → cualquier usuario autenticado lista todas las empresas con `tax_id`, `country`,
`currency`, `approval_levels` y `sap_config`, que `CompanyRead` expone entero.
`docs/03 §686` asumía «la mayoría de entidades tienen `company_id`»; `Company` es la que no puede.

## `R-116` · `P0` · usuario sin empresa → maestros sin filtrar
`if not self.user_company_id: return query`. El comentario del propio código no resolvió la
intención: «return empty or filter by id». Un usuario sin empresa que no sea Super Administrador
ve los maestros de todas. Es `fail-open` donde `GA-REM-040` eligió `fail-closed`.
`POST /users` permite crear usuarios así: `company_id` es `Optional`.

## `R-117` · `P0` · `update_user` cruza inquilinos y reasigna el rol
`select(User).where(User.id == user_id)` sin empresa, y `UserUpdate.role_id` se aplica por
`setattr` en bucle. Con `users:update` se le asigna a **cualquier** usuario de **cualquier**
empresa un rol con el comodín `("*", ...)`, que es Super Administrador. Escalada de privilegios
que cruza inquilinos por la ruta documentada de edición.
`GA-REM-034` cerró lo análogo para roles y `GA-REM-002 AC12` para sub-recursos de lote; la
lección no llegó a `/users`.

## `R-118` · `P1` · `create_user` acepta la empresa del cliente
El router obtiene `current_user` y **no lo pasa** al servicio; `company_id=data.company_id` entra
sin validar. Un administrador de A crea usuarios en B. El patrón correcto ya existe en la casa:
`GA-REM-040` fase 7 resuelve la empresa en vez de recibirla.

## `R-119` · `P1` · el frontend no comprueba permisos en ninguna pantalla
Cero ocurrencias de `hasPermission`/`usePermission` en `frontend/src`. `navigationConfig.ts` es
un array estático sin campo de permiso, módulo ni unidad: las nueve entradas se dibujan para
cualquiera. `docs/02 §3.1.3` pide «módulos accesibles» por rol.
**No es agujero de seguridad** —el backend deniega— sino producto que enseña puertas cerradas.
Depende de `GA-REM-040` fase 8 para tener contrato de capacidades del que tirar.

## `R-120` · `P1` · la interfaz confunde denegación con conjunto vacío
`UsersPage` hace `Promise.all` de cuatro llamadas y las envuelve en `catch { console.error }`.
Si una falla, `users` queda en `[]` y la tabla se dibuja con cabeceras y sin filas.
**Es la explicación del `/users` vacío que motivó esta auditoría**: `/users` y `/roles` exigen
`users:read`, que ningún rol sembrado concede. Barato de arreglar y de alto retorno.

## `R-121` · `P1` · los roles no se acotan por empresa
`Role.company_id` existe en el modelo. `get_roles` devuelve todos los activos sin filtrar y
`create_role` no lo asigna: el catálogo de roles es global y un rol de la empresa A aparece en la
lista de la B. Requiere decidir si el catálogo es de producto o de inquilino.

## `R-122` · `P2` · falta la columna Empresa en el listado de usuarios
`docs/02 §3.1.2` la exige. El formulario de alta/edición **sí** tiene el selector; la tabla no
muestra la columna. `PARTIAL`, no `MISSING`.

## `R-123` · `P2` · `Permission.scope_type` se almacena y no se evalúa
`tiene_permiso` compara `(módulo, acción)` y descarta el alcance, salvo para detectar Super
Administrador con `("*", scope="all")`. `docs/02 §3.1.4` pide `all` / `company` / `farm`.

## `R-124` · `P1` · **RESUELTO — `OD-24` (decisión A, 2026-09-11)** · ¿vienen de SAP las Empresas y las Granjas?
`docs/10 §3.1` lista lo que SAP importa: Centros, Almacenes, Materiales, Proveedores, Lotes, OC,
OT. **Ni Empresas ni Granjas.** `docs/02 §3.2.1` las lista como catálogos base locales con campos
propios. **El código cumple la spec; la spec no cumple la expectativa del propietario.**
No es defecto de implementación: es requisito no escrito. Preguntas a decidir:
```
¿Es SAP el dueño de Empresas? ¿Y de Granjas? ¿Contra qué objeto SAP?
¿Réplica de solo lectura, o copia con extensión local declarada?
¿Qué pasa con las creadas localmente hasta hoy?
¿Y con `sap_config`, hoy campo editable de la empresa?
```
**RESUELTA — `OD-24` (2026-09-11, decisión A):** importadas de SAP y no editables post-integración (Sociedad↔Empresa; Centro/Planta↔Granja, mapeo a fijar en SPEC); régimen provisional local declarado pre-P-08 (PL-05/06); sin código hoy. Texto: `audit/final-frontend-audit/GA_OD_24_COMPANIES_FARMS_OWNERSHIP_DECISION.md`.

## `R-125` · `P1` · `OWNER_DECISION_REQUIRED` · módulos activables por empresa
Cero coincidencias en `docs/` y `specs/`; no existe `CompanyModule` ni equivalente.
**`RBAC` no lo sustituye:** `Permission.module` dice qué puede hacer una persona, no qué ha
contratado una empresa. Hoy falta una dimensión entera de la pila de autorización.
A decidir: ¿se vende por módulos contratables, o es producto único acotado por `RBAC`?

---

## Cierre de `R-114`, `R-117` y `R-118` · y `R-120` (2026-09-08)

```
R-114   CERRADO   `/users` listar, leer y editar acotados · `GA-REM-002` `AC13` `AC14`
R-117   CERRADO   escalada de autoridad entre inquilinos · `AC15`
R-118   CERRADO   el alta resuelve la empresa en vez de recibirla · `AC14`
R-120   CERRADO   cinco estados distinguibles en `/users` · `AC16`
R-116   PARCIAL   `fail-closed` en `/users`; `MasterService` sigue abierto
```

Evidencia en `USER_TENANT_ISOLATION_P0_EVIDENCE.md`. 9 mutaciones, 9 detectadas.

## `R-126` · `P2` · `OWNER_DECISION_REQUIRED` · ¿acota `switch-company` a la autoridad global?

Al cerrar `R-114` escribí una prueba afirmando que el Super Administrador situado en la empresa
`A` con `switch-company` solo debía ver usuarios de `A`. **Estaba equivocada.**

`docs/02 §3.1.4` dice literal: «Super Admin (rol con `module="*"`, `scope_type="all"`) ve TODAS
las compañías», y `get_company_filter` lo aplica así en todo el producto —`MasterService`
incluido—. Acotarlo solo en `/users` habría hecho que esa ruta se comportara distinto de
`/masters` sin norma que lo pidiera, y rompió dos pruebas certificadas.

La pregunta es legítima y sigue abierta: **¿situarse en una empresa debe acotar también a la
autoridad global?** Hoy la respuesta del producto es no. Cambiarla afecta a todos los servicios
y es decisión de propietario, no un parche en una ruta.

---

## Cierre de `R-115` y `R-116` · nuevo `R-127` (2026-09-08)

```
R-115   CERRADO   `Company` acotada por su propia clave · `_INQUILINO_POR_IDENTIDAD`
R-116   CERRADO   sin empresa efectiva → cero filas · `fail-closed`
```

Bajo `RQ-03` y `AC05`. **Sin `GA-REM` nueva**: la autoridad ya existía y lo que faltaba era la
cobertura de recursos. Evidencia en `MASTER_TENANT_ISOLATION_EVIDENCE.md`.
7 mutaciones, 7 detectadas — una rehecha por inválida y contada como tal.

## `R-127` · `P1` · `/masters/companies` devuelve `500` si la empresa tiene `sap_config`

```
CLASE        INCOHERENCIA DE TIPO ENTRE MODELO Y ESQUEMA
DESCUBIERTO  al construir la fixture de `R-115`
ESTADO       REGISTRADO · no remediado
```

`Company.sap_config` es columna **`String`** tipada como `Mapped[Optional[dict]]`, y
`CompanyRead.sap_config` la valida como `dict`. Cualquier empresa con configuración `SAP`
poblada rompe el endpoint **para todo el mundo**, incluido el Super Administrador.

**Corrige la redacción original de `R-115`**, que decía que se exponía `sap_config`: la
exposición estaba **latente detrás de este 500**, no activa. El campo no podía filtrarse porque
la ruta se rompía antes. Lo que sí era alcanzable era la fuga de la fila entera, y eso es lo que
`R-115` ha cerrado.

No se remedia aquí: no lo gobierna `R-115` y corregirlo exige decidir si `sap_config` debe ser
`JSON` en la base —migración— o `str` en el esquema. Es una decisión de diseño pequeña pero
real, y esta tanda es de aislamiento de inquilino.

Nota de alcance: `docs/02 §3.1.4` declara «Configuración SAP por compañía», de modo que el campo
es legítimo. Lo que no está decidido es si debe viajar entero en el listado de maestros o solo
en una superficie administrativa — pregunta adyacente que se registra aquí y no se responde.

---

## Cierre de `R-121` y `R-126` · `RQ-03` = `COMPLETE` (2026-09-08)

```
R-121   CERRADO   `OD-13` · el permiso es de producto, el rol tiene alcance
R-126   CERRADO   `OD-14` · cada superficie declara su clase, sin clase por omisión
RQ-03   COMPLETE  54 recursos recorridos · 0 sin clasificar · 5 excepciones escritas
R-113   READY_TO_RESUME · con una pregunta de segregación abierta
```

Evidencia: `RQ-03-TENANT-ISOLATION-CLOSURE-EVIDENCE.md`, `R-113-REEVALUATION-NOTE.md`,
`ROLE_PERMISSION_COMPANY_SCOPE_MATRIX.md`,
`GLOBAL_TENANT_SURFACE_CLASSIFICATION_MATRIX.md`.

Sensibilidad acumulada del aislamiento: **27 mutaciones, 27 detectadas, 5 corregidas antes de
contarlas** — una no instalada, una que fallaba por `NameError`, una que no quitaba la
propiedad, una que medía la página equivocada y una fuera del camino de la prueba.

## `R-128` · `P2` · `OWNER_DECISION_REQUIRED` · ¿puede concederse unidades a sí mismo quien las reparte?

`business_units:create` autoriza a conceder a cualquier usuario de la empresa efectiva, **uno
mismo incluido**. Documentado desde la fase 7, probado y auditado con actor y objetivo.

Con el aislamiento cerrado el alcance es exactamente: puede darse cualquier cadena que su
empresa **ya tenga habilitada**; no puede habilitar cadenas nuevas —es otra acción—, no puede
salir de su empresa, y no puede fabricar autoridad global.

Riesgo acotado y visible, no escalada. Pero es una pregunta de segregación de funciones
legítima y bloquea la ratificación de `R-113`, no su reanudación técnica. Si el propietario
quiere separarlo, cabe en la misma capa que `AC15`.

---

## Cierre de `R-128` y `R-113` (2026-09-09)

```
R-128   CERRADO   `OD-15` · quien reparte accesos no se sirve a sí mismo
R-113   CERRADO   `OD-15 §6` · rol «Administrador de Accesos», cuatro permisos exactos
```

Evidencia: `R-128-BUSINESS-UNIT-SELF-GRANT-EVIDENCE.md`,
`R-113-ACCESS-ADMINISTRATION-CLOSURE-EVIDENCE.md`.

```
PRUEBAS        16 nuevas · rojo previo 4/16
SENSIBILIDAD   10 mutaciones · 10 detectadas · 2 intentos iniciales inválidos
               y 2 pruebas mías reforzadas por ellas — una vacua, una débil
REGRESIÓN      backend 754 passed · 49 skipped · frontend 87 · 0 ficheros TS/TSX
MIGRACIÓN      ninguna
```

**El tope de `SOLO_SUPER_ADMIN` vuelve de 17 a 15**: los cuatro permisos de `business_units`
salen de la excepción porque ya los concede un rol. Primera vez que esa lista baja.

Sensibilidad acumulada del aislamiento y la administración: **37 mutaciones válidas · 37
detectadas · 7 intentos iniciales inválidos corregidos antes de contarlos**.

---

## `GA-REM-040` fase 8 · COMPLETE (2026-09-09)

```
T-040-20   la sesión entrega habilitadas · concedidas · efectivas · capacidades
FASE 8     COMPLETE · contrato aditivo · sin migración · 0 ficheros de frontend
```

Evidencia: `GA_REM_040_PHASE_8_EVIDENCE.md`.
16 pruebas · rojo previo 15/16 · sensibilidad 11/11 · 1 rehecha por inválida.

## `R-129` · `P3` · superficie de candidatos para la administración de acceso

La fase 9 necesitará ofrecerle al `Administrador de Accesos` los usuarios de su empresa a los
que conceder una unidad. Hoy no puede: `OD-15 §6` le negó `users:read` **a propósito**, porque
`users:*` es el conjunto que mantuvo cuatro `P0` latentes.

Hace falta una superficie propia y mínima —identificador y nombre de los usuarios de la empresa
efectiva— sin conceder lectura general de usuarios. **No se implementa en la fase 8**: no la
pide `§14.1` ni ninguna `AC` vigente, y construirla aquí sería ampliar el alcance por
comodidad.

Queda como dependencia explícita de la fase 9.

---

## Cierre de `R-129` · fase 8 cerrada formalmente · preflight de la fase 9 (2026-09-09)

```
FASE 8   COMPLETE   cierre formal con las cuatro precisiones de `§4`–`§7`
R-129    CERRADO    `GET /business-units/{code}/grant-candidates` · sin `users:read`
FASE 9   BLOQUEADA  por `R-127` — una causa exacta, ver `PHASE_9_DEPENDENCY_PREFLIGHT.md`
```

Evidencia: `R-129-BUSINESS-UNIT-GRANT-CANDIDATES-EVIDENCE.md`.
14 pruebas · rojo previo 12/14 · sensibilidad 8/8 · 0 intentos inválidos · 2 N/A con motivo.

**`R-127` pasa de `P1` a bloqueo duro de la fase 9.** El selector de empresa
(`company.store.ts:39`) solo puede leer de `GET /masters/companies`, que devuelve `500` en
cuanto una empresa tiene `sap_config` poblado, y la sesión no expone empresas a propósito.
`§70` prohíbe esquivarlo en el frontend. Necesita tanda propia con decisión de propietario:
¿columna `JSON` (migración) o esquema `str`? ¿Y viaja `sap_config` en el listado de maestros?

Sensibilidad acumulada del programa en aislamiento y administración: **56 mutaciones válidas ·
56 detectadas · 8 intentos iniciales inválidos corregidos antes de contarlos**.

---

## Hallazgos de la Master 360 y su addendum · alta oficial (2026-09-09 · WAVE A0-G)

Reconciliación completa en `H360_AND_ADDENDUM_TO_OFFICIAL_BACKLOG_RECONCILIATION.md`: 75
hallazgos, 0 sin disposición, 20 mapeados a IDs existentes, 28 IDs nuevos. Cada entrada conserva
su `source_finding`. Ninguno se remedia en esta ola.

| ID | Sev. | Título | `source_finding` | Requisito raíz | Ola | Autoridad prevista | Decisión |
|---|:--:|---|---|---|:--:|---|---|
| **`R-130`** | **P1** | `cull_recording` y `bird_exit` no validan contra el saldo: la población puede quedar negativa; sin test | `H360-P01` | `BR-01` · invariante | B | enm. `GA-REM-005` | — |
| **`R-131`** | **P1** | «FCR» = `total_feed_kg / 1000` (`reports/service.py:155`), propagado a índice de producción e IPE; edad con `date.today()` en lotes cerrados | `H360-K01`, `H360-K07` | `Bases` p.2/p.13 | C | enm. `GA-REM-022` | — |
| **`R-132`** | **P1** | % de mortalidad con denominador solo de `OpeningBalance` → 0 % en lotes activados por recepción; tendencia sin filtro de estado; sin % contra población actual | `H360-K02`, `H360-K13` | `Bases` p.3 · Rec. §9 | C | enm. `GA-REM-022` | `AOD-10.e` |
| **`R-133`** | **P1** | eficiencia de vacunación cuenta eventos (`/1000`) y no aves | `H360-K03` | `Bases` p.10 | C | enm. `GA-REM-022` | — |
| **`R-134`** | **P1** | AFCR suma `BirdMovement.quantity` como gramos; sin peso de muertos | `H360-K06` | `Bases` p.13 | C | enm. `GA-REM-022` | — |
| **`R-135`** | **P1** | `RETURNED` no se reenvía; `REJECTED` es terminal | `H360-P03`, `H360-D09` | `docs/12 §4` | B | enm. `GA-REM-006` | — |
| **`R-136`** | **P1** (SAP) | tabla `reversals` sin servicio ni ruta; `BR-16` sin mecanismo | `H360-P05` | `BR-16` · Rec. §24 | B · D | **`GA-REM-041`** (interno, **`CERTIFIED`**) | **`OD-19`** ✓ · **PARTIAL**: interno **CERRADO** (tranche 5) · post-SAP `SAP_DEFERRED` (`AOD-04`/`OD-12`) · consolidados `DEFERRED` · huevos/incubación `BLOCKED_BY_R-161` |
| **`R-137`** | **P1** (D) | `lots` sin identificador del lote productivo SAP | `H360-S05` | Rec. §3.3, §25.3 | D | enm. `GA-REM-017` | **`AOD-03`** |
| **`R-138`** | **P1** (D) | materiales (`feed_types`, `vaccines`, `medications`) sin clave SAP; sin material por raza/sexo/huevo/pollito; proveedor por dos vías | `H360-S01`, `H360-S02`, `H360-S03` | Rec. §5, §15 | D | enm. `GA-REM-017` | `AOD-01` parcial |
| **`R-139`** | **P1** | 8 atajos `is_super_admin` sobre dato productivo/maestros no conformes con `OD-14.c/d` (`operations:762,810,978,997` · `lots:351` · `curves:75` · `masters/router:139,161`); 0 tests | `H360-A01` = `H360A-08` · verificado en `A01_SUPER_ADMIN_SHORTCUT_VERIFICATION.md` | `OD-14` | **A** (tanda propia; precede a la fase 9) | enm. `GA-REM-002` clase C o `GA-REM-040` | — |
| `R-140` | P2 | `cancel` sin motivo ni restricción de rol; no bloquea `SAP_CONFIRMED`/`SAP_ERROR` (latente) | `H360-P04` | `docs/12 §4` fila 13 | B | enm. `GA-REM-006` | — |
| `R-141` | P2 | KPI de segundo orden: hen-day ×30 · bienestar heurístico · % sanos con denominador «cargados» · ganancia diaria aproximada | `H360-K04`, `K05`, `K11`, `K08` | `Bases` | C | enm. `GA-REM-022` | `AOD-10` |
| `R-142` | P2 | `CORRECTED` usado como «pendiente de aprobador» sin corrección (`review/service.py:292`) | `H360-P06` | `docs/12 §4` fila 6 | B | enm. `GA-REM-006` | — |
| `R-143` | P2 | `docs/12 R2` (quien corrige no aprueba) no implementada: la segregación compara con `registered_by_id` | `H360-P10` | `docs/12 §6` | B | enm. `GA-REM-007` | — |
| `R-144` | P2 | resumen de cierre sin FCR ni peso final aunque `BR-05` exige pesaje para el FCR | `H360-P08` | `BR-05` · Rec. §13 | B/C | enm. `GA-REM-029` | `AOD-08` |
| `R-145` | P2 | preparación SAP: backoff fijo 1 min (docs/10: 1/5/15) · consolidación sin validación de integridad · outbox pasivo · `external_transaction_id` solo tras éxito y `sap_reference_item` nunca poblado · OT no validada en alimento | `H360-S07`, `S10`, `S11`, `S13`, `S04`, `D11` | `docs/10 §5-6` · `docs/12 §10` · Rec. §8, §19 | D | enm. `GA-REM-010` | — |
| `R-146` | P2 | sin `idempotency_key` de cliente: el reenvío móvil duplica registros | `H360-S12` | Rec. §17 | E | enm. `GA-REM-011` | `AOD-16` rel. |
| `R-147` | P2 | constantes y tipos sin fuente normativa: unidad de medida sin catálogo · umbrales T°/H° fijos · `sex` `String` vs `SexEnum` · capacidad de incubadora no validada · pasos de aprobación por nombre de rol | `H360-B06`, `B07`, `B10`, `B12`, `B08` | Rec. §17 · `docs/02:516` | B/C | spec propia | — |
| `R-148` | P2 | inmutabilidad de `audit_logs` solo en aplicación (listeners); sin trigger/regla en BD | `H360-D04` | `docs/13 §8` | B | enm. `GA-REM-032` | — |
| `R-149` | P2 | deriva documental: `OD-04/06/08` sin archivo · `spec §14` → `docs/17` inexistente · `BR-17…19` fuera de `spec §5` · `GA-REM-016` en borrador amparando 15 certificaciones · `docs/03 §3.5` con tres tipos de ave (**la deriva de `INDEX.md` se cierra en este commit**) | `H360-D01`, `D02`/`D12`, `D03`, `D05`, `H360A-07` | `GA-REM-001` | A (documental) · F | — | — |
| `R-150` | P2 | estados de error (`prohibido` / `error` / vacío) solo en `/users`; el resto de páginas no distingue denegación de vacío | `H360-F02` | `R-120` (generalización) | E | enm. `GA-REM-011` | — |
| `R-151` | P2 | evidencia solo adjuntable en el detalle, no en el acto de captura móvil | `H360-F03` | Rec. §6 · `docs/02 §7` | E | spec propia | `AOD-16` rel. |
| `R-152` | P2 | `grandparent_import` sin estructura para el plan de importación (`docs/02 §3.4.1`): país, cantidades comprada/embarcada/recibida, mortalidad en traslado, cuarentena, adjuntos tipados | `H360A-02` | `docs/02 §3.4.1` · `spec §4.4` | B | spec propia | — |
| `R-153` | P3 | el lote de abuelas no se crea automáticamente al completar la importación | `H360A-03` | `docs/02 §3.4.2` | B | spec propia | — |
| `R-154` | P3 | estados y campos sin productor: `DRAFT` · dos artefactos «cierre» (`LOT_CLOSURE` vs `POST /lots/{id}/close`) · `version` nunca incrementa · `LotStatus.CANCELLED` | `H360-P02`, `P09`, `P11` | `docs/12 §4` · `docs/13` | B | — | `AOD-08` |
| `R-155` | P3 | período cerrado = 90 días fijos sin fuente (`BR-19`) | `H360-S06` | Rec. §15 | D | — | **`AOD-15`** |
| `R-156` | P3 | peso reportado por el proveedor vs peso en granja (paridad con la app anterior, nivel 6) | `H360-B11` | legado p.18 | B | enm. `GA-REM-021` | — |
| **`R-157`** | **P1** (D) | payload no mapeable a documento SAP (sin material, centro, almacén, objeto de costo, tipo de movimiento) · sin matriz formal por proceso (Rec. §24) · sin confirmación entrante SAP → app; `SENT_TO_SAP`/`SAP_CONFIRMED`/`SAP_ERROR` sin productor | `H360-S08`, `H360-S09` | Rec. §16, §18, §22, §24, §26 | D | enm. `GA-REM-017` | `AOD-01…05` |

Mapeados sin ID nuevo (misma causa raíz): `H360-B05`/`H360A-10` → `R-13` · `H360-F01` → `R-98`/`R-119` ·
`H360-B09` → `R-80` · `H360-B01/B02/B03/B04/B13` → `GA-REM-021` (enmienda pendiente) · `H360-K10` → `GA-REM-022` ·
`H360-C01` → `GA-REM-011` · `H360-T01` → `GA-REM-013` · `H360-D06`/`H360A-06` → `R-124` · `H360A-01` → `GA-REM-040` fase 9 ·
`H360A-04` → `GA-REM-016` · `H360A-05` → `GA-REM-040` fases 10-11 · `H360A-09` → `BU-D07` · `H360-D07/D08/D10` → `AOD-07/08/10`.

Estado de los abiertos previos, sin cambio: `R-77` · `R-80` · `R-83` · `R-98`/`R-119` · `R-99` (`BLOCKED_BY_OUT_OF_SCOPE_DEPLOYMENT`, no tocar) ·
`R-111` · `R-112` (verificar cierre frente a `OD-12`) · `R-122` · `R-123` · `R-124` · `R-125` · **`R-127`** (tanda `WAVE A1`, gobernada por `OD-18`) · `BU-D10` (`PENDING_RATIFICATION`).

---

## Cierre de `R-127` · catálogo seguro de empresas (2026-09-09 · WAVE A1)

```
R-127    CERRADO    GA-REM-033 enmienda A · OD-18 · CompanyCatalogRead sin sap_config · 11/11 · sensibilidad 3/3 válidas
R-127.b  DEFERRED   escritura de sap_config (POST/PUT con dict sobre columna String) · OD-18.b · sin migración · SAP_DEFERRED
FASE 9   FROZEN     bloqueo técnico de R-127 retirado · R-139 pendiente · autorización del propietario: NO
```

Evidencia: `R-127-SAFE-COMPANY-CATALOG-EVIDENCE.md`. Rojo previo 9/11 con la aserción `500 == 200` y
control verde con el mismo rol y ruta; causa reproducida sin revertir código (`dict_type` en
`sap_config`). Regresión completa: **795 passed · 49 skipped · 0 failed** (539 s; 784 previas + 11 de `test_company_catalog.py`; los 49 saltados son `test_upgrade_path` y `test_runtime_startup`, que exigen su script dedicado). Vitest: 87 passed / 8 archivos.

### Hallazgo nuevo de la ola A (no procede de la Master 360)

| ID | Sev. | Título | Evidencia | Ola | Autoridad |
|---|:--:|---|---|:--:|---|
| `R-158` | P2 | `npx tsc -b --noEmit` falla con 6 errores (`TS6133` variables sin uso en `AuditPage.tsx:3`, `LotFormPage.tsx:47,85`; `TS2493` índice de tupla en `LotFormPage.tsx:85`); **preexistente en `7ee72a1`** (reproducido en worktree temporal; frontend sin cambios en la ola A). `quality-gates.yml:87` ejecuta exactamente ese comando, luego la puerta de frontend está roja | `scratchpad/tsc_A.txt` | A (`GA-REM-013`) · E | enm. `GA-REM-013` / `GA-REM-011` |

---

## Cierre de `R-139` · `OD-14.c/d` en el dato productivo · `WAVE A COMPLETE` (2026-09-09)

```
R-139    CERRADO    GA-REM-002 enmienda C · 8/8 superficies INQUILINO · primitivo verificar_pertenencia falla cerrado
                    35/35 · rojo previo 24/35 · sensibilidad 8 válidas + 1 N/A (S5 reconstruida tras un intento inválido)
R-159    P2 · NUEVO get_alerts sin predicado de unidad para actores de empresa (fase 3 lo dejó «parcial», evidencia :38;
                    route_scope declara «alertas de sus lotes») · alcance de unidad, no de inquilino · fuera de R-139 · WAVE B
WAVE A   COMPLETE   R-127 y R-139 cerrados · R-149 documental y R-158 (tsc) quedan en su ola
FASE 9   TECHNICALLY READY · FROZEN (autorización del propietario: NO)
```

Evidencia: `R-139-OD14-PRODUCTIVE-DATA-EVIDENCE.md`. Regresión completa: **830 passed · 49 skipped · 0 failed** (542 s; 795 previas + 35 de `test_od14_productive_surfaces.py`; los 49 saltados son `test_upgrade_path` y `test_runtime_startup`, que exigen su script dedicado). Por archivo: aislamiento de maestros 16 · usuarios 18 · roles 12 · unidades 31 · guarda 25 · administración 39 · sesión 16 · accesos 16 · candidatos 14 · `test_rbac` 21 (`SOLO_SUPER_ADMIN` ≤ 15 sin tocar) · clasificación pendiente 35 · curvas 16 · multiempresa 5 + 12 · saldo de apertura 12 · filas por unidad 21 · KPI por unidad 15 · catálogo de empresas 11. Vitest 87 passed / 8 archivos. `tsc` 6 errores preexistentes (`AuditPage.tsx`, `LotFormPage.tsx`), mismo número y ficheros que en `7ee72a1` (`R-158`, sin cambio).

---

## Pre-flight de la ola B · hallazgos nuevos (2026-09-09)

| ID | Sev. | Título | Evidencia | Clase | Ola |
|---|:--:|---|---|---|:--:|
| **`R-160`** | **P1** | la **creación y edición de eventos operativos no exigen alcance de unidad**: `POST /operations` pasa solo por `require_permission("operations","create")` y `validate_lot_active` (empresa); `exigir_acceso_a_unidad` no tiene llamadores en `app/`; un actor con concesión en `breeder` registra eventos sobre un lote `hatchery` de su empresa, incluso con la unidad apagada. La fase 3 certificó lecturas y la mutación de **lotes** (`GA_REM_040_PHASE_3_EVIDENCE.md:136-137`), no la de eventos | `operations/router.py:70-73` · `operations/service.py` `_apply_business_rules` · `grep exigir_acceso_a_unidad app/` → 0 llamadores | `BUSINESS_UNIT_SCOPE` | B · tranche 2 (con `R-159`) |
| `R-161` | P2 | los saldos de huevos e incubación (`BR-02`, `BR-03`) se leen sin bloqueo de fila: la misma carrera de decrementos concurrentes que `R-130` cierra para las aves | `validators.get_egg_balance`, `get_hatchery_egg_balance` | `DATA_INTEGRITY` | B · tras el tranche 1 |

Matriz completa: `WAVE_B_DEPENDENCY_AND_EXECUTION_MATRIX.md`.

---

## Cierre de `R-130` · el saldo de aves nunca es negativo · WAVE B tranche 1 (2026-09-09)

```
R-130    CERRADO (técnico)   GA-REM-005 enmienda B · validate_bird_decrement + bloqueo de fila · viable real de pollitos
                            21/21 · rojo previo 11/21 · sensibilidad 6 válidas + 1 N/A (S4: R-160) · relacionadas 407/407
                            certificación de proceso: BLOCKED_RUNTIME (no se reclama)
WAVE B   IN PROGRESS        17 ítems (recuento canónico, corregido en el tranche 2: R-161 ya era de la ola B) · 1 cerrado · siguiente tranche: R-160 + R-159 (cerrado abajo)
```

Evidencia: `R-130-POPULATION-INVARIANT-EVIDENCE.md`. Regresión completa: **851 passed · 49 skipped · 0 failed** (589 s; 830 previas + 21 de `test_population_invariant.py`; los 49 saltados son `test_upgrade_path` y `test_runtime_startup`, que exigen su script dedicado). Primera pasada: 850/49/**1** — `test_master_management.py::test_t_090_06` descartaba 3 aves sobre el lote sembrado con saldo 0 (fixture que dependía del defecto); ajustada con recepción previa (`T-130-01b`, aserción intacta) y regresión repetida entera hasta leerla en verde. Vitest 87 passed / 8 archivos. `tsc` 6 errores preexistentes (`AuditPage.tsx`, `LotFormPage.tsx`), mismo número y ficheros que la línea base `R-158`.

---

## Pre-flight del tranche 2 · hallazgos nuevos (2026-09-09)

| ID | Sev. | Título | Evidencia | Ola |
|---|:--:|---|---|:--:|
| `R-162` | P2 | `GET /operations/{id}/evidences/{eid}/download` no aplica predicado de unidad para el actor de empresa (solo empresa, `R-139`); `get_evidences` sí lo hace vía `get_event`. Misma raíz que `R-160`/`R-159`; fuera del tranche 2 (lectura de fichero, no escritura ni alerta) | `operations/service.py get_evidence_for_download` | B |
| `R-163` | **P1** (normalizada en el pre-flight del tranche 4: `POST /lots` sin unidad para todo actor = clase `AC-C05` de `R-160`; lotes sin empresa = clase `R-139`; antes «P2 (P1 en…)») | en `lots` (`PUT /lots/{id}`, `POST /lots/activate-manual`; **inventario del tranche 3**: también `POST /lots/{id}/close`, `POST /lots/{id}/phases`, y **`POST /lots` no exige unidad a ningún actor**) la autoridad global sigue exenta de la **habilitación** de unidad (`masters/service._apply_business_unit_filter`: `if … or self.is_super_admin: return query`), de modo que puede mutar lotes de una unidad apagada; incoherente con la lectura absoluta de `AC-A05`/`OD-16.e` que `GA-REM-040-G` aplica a `operations` | `masters/service.py:113` · fase 3 | B |

Recuento canónico de la ola B: **17** ítems (1 cerrado) + `R-162`, `R-163` = **19**. Detalle en `WAVE_B_DEPENDENCY_AND_EXECUTION_MATRIX.md §6`.

---

## Cierre de `R-160` + `R-159` · la unidad de negocio se exige al operar sobre `operations` · WAVE B tranche 2 (2026-09-09)

```
R-160    CERRADO (técnico)   GA-REM-040 enmienda G · exigir_unidad_operativa (alta · edición con lote y ubicación destino ·
                            submit · cancel · evidencias) · derivación canónica en el servidor (lot.bird_type · clasificación · pendiente)
                            AC-W01…W15 (W08 N/A: sin campo) · 24/24 · rojo previo 14 rojas de 23
R-159    CERRADO (técnico)   mismo predicado en la consulta: lot_id IN lotes_alcanzables antes de ordenar/paginar · resolve con él
                            AC-A01…A13 (A10 N/A: Contraloría sin resolutor) · 16/16 · rojo previo 9 rojas de 23
                            sensibilidad S1–S9: 8 ejecutadas válidas (S4b tras añadir la prueba del lote cerrado) · S3/S8 N/A con motivo
                            relacionadas 397 + 74 (R-139 35/35 · R-130 21/21) · certificación de proceso: BLOCKED_RUNTIME (no se reclama)
WAVE B   IN PROGRESS        19 ítems (17 canónicos + R-162 + R-163 registrados en este tranche) · 3 cerrados (R-130 · R-160 · R-159) · 16 abiertos
                            siguiente tranche (identificado, no iniciado): R-135 + R-143 (+ R-140 motivo/guarda · R-154 DRAFT/version) — OD-17 decidida
```

Evidencia: `R-160-R-159-PRODUCTIVE-BU-ENFORCEMENT-EVIDENCE.md`. Regresión completa: **891 passed · 49 skipped · 0 failed** (838 s; 851 previas + 40 de `test_operations_bu_enforcement.py`; 2.ª pasada tras la dependencia de fixture de `test_t_073_06`, montaje reordenado: la concesión de unidades antes de escribir eventos); los 49 saltados son `test_upgrade_path` y `test_runtime_startup`, que exigen su script dedicado). `vitest` 87/87 · `tsc` 6 errores preexistentes (`R-158`). Sin migración (`s9t0u1v2w3x4`), sin rutas nuevas, sin frontend. `R-161` sigue OPEN. Fase 9 FROZEN. `BU-D10` PENDING_RATIFICATION.

---

## Cierre de `R-163` + `R-162` · la habilitación de la empresa es absoluta para toda escritura productiva · WAVE B tranche 3 (2026-09-09)

```
R-163    CERRADO (técnico)   GA-REM-040 enmienda H · guarda compartida business_units.exigir_unidad_operativa · lots: create (antes sin unidad
                            para nadie; la global sin contexto creaba lotes sin empresa), update, close, activate-manual, phases → 403 sobre
                            unidad apagada para la autoridad global; el actor de empresa sigue en 404 por unidad (fase 3)
                            AC-L01…L15 · 19/19 · rojo previo 10 rojas de 13
R-162    CERRADO (técnico)   descarga de evidencia: empresa (403, R-139) → get_event (404 por unidad) → fichero · AC-E01…E08 · 9/9 · rojo previo 3
                            sensibilidad S1, S2, S4, S5, S7, S9 válidas · S3/S6/S8 N/A con motivo · lecturas de lots de la global sin cambio (AC-L11)
                            certificación de proceso: BLOCKED_RUNTIME (no se reclama) · R-160/R-159 40/40 · R-139 35/35 · R-130 21/21
WAVE B   IN PROGRESS        19 ítems · 5 cerrados (R-130 · R-160 · R-159 · R-163 · R-162) · 14 abiertos
                            siguiente tranche (identificado, no iniciado): R-135 + R-143 (+ R-140 motivo/guarda · R-154 DRAFT/version) — OD-17 vigente
```

Evidencia: `R-163-R-162-LOTS-EVIDENCE-BU-ENFORCEMENT-EVIDENCE.md`. Regresión completa: **919 passed · 49 skipped · 0 failed** (719 s; 891 previas + 28 de `test_lots_bu_enforcement.py`; 2.ª pasada tras la dependencia de fixture de `test_t_038_49`, montaje reordenado: la concesión de unidad antes de registrar el lote); los 49 saltados son `test_upgrade_path` y `test_runtime_startup`, que exigen su script dedicado). `vitest` 87/87 · `tsc` 6 preexistentes (`R-158`). Sin migración (`s9t0u1v2w3x4`), sin rutas nuevas, sin frontend. `R-161` sigue OPEN. Fase 9 FROZEN. `BU-D10` PENDING_RATIFICATION.

---

## Pre-flight del tranche 4 · hallazgos nuevos y trazas parciales (2026-09-09)

| ID | Sev. | Título | Evidencia | Ola |
|---|:--:|---|---|:--:|
| `R-164` | P2 | `lots.company_id` es nulable sin restricción de esquema (`masters/models.py`): la prevención de lotes huérfanos es de aplicación (`AC-L05`), no de base de datos; deuda de datos históricos **`UNKNOWN`** — la consulta `count(*) WHERE company_id IS NULL` contra la base configurada no fue alcanzable (`BLOCKED_RUNTIME`); **nada limpiado**. Exige verificación en entorno certificable, migración `NOT NULL` y decisión sobre filas inválidas si las hay | `WAVE_B_TRANCHE_4_PREFLIGHT.md §B` | B |
| `R-165` | P2 | el plano de revisión (`review/start|return|complete`, `approvals/approve|reject`) no exige la **habilitación** de la unidad a la autoridad global (`_ambito_de_unidad` → `[]` para `is_super_admin`); misma clase que `R-163`; el actor de empresa ya queda fuera por `unidades_efectivas` · **incluido en `GA-REM-041` §1.2** (el reverso se aprueba por ese plano; `OD-19 §13`) | `review/service.py:77-99, 360-383, 561-580` | B |
| `R-166` | P3 | `approve` y `reject` sobre el mismo evento `CORRECTED` no se excluyen (sin bloqueo de fila; el último `flush` gana) | `review/service.py:423-470` | B |
| `R-167` | ~~P3~~ **NO_DEFECTO** (tranche 8: **NOT_REPRODUCED**, cerrado; `R167_ARRIVAL_MORTALITY_ACCOUNTING_MATRIX.md`) | doble contabilización posible de la mortalidad al arribo: campo `dead_on_arrival` de la recepción (`B01`) + evento `mortality_recording` del mismo día (práctica previa, `docs/16:177`); la semántica del KPI de mortalidad respecto a las muertas al arribo no tiene fuente (ola C) | `GA_REM_021_B01_RECEPTION_RECONCILIATION_MATRIX.md §7` | B/C |
| `R-168` | ~~P3~~ **P2** · **CERRADO** (técnico, tranche 8, `GA-REM-021-C §C.2`) | el formulario de recepción envía `bird_movements[i].sample_size` y `BirdMovementSchema` no lo declara: se descarta en silencio (patrón `R-47`); «Muestra tomada» (§6) no se persiste por galpón | `OperationFormPage.tsx:698` · `operations/schemas.py:12-20` | B |
| `R-169` | ~~P3~~ **P2** · **CERRADO** (técnico, tranche 8, `GA-REM-035-A`; es **cantidad vs OC**, no peso) | alerta «diferencia superior al 10 %» recibido vs declarado en el formulario de recepción sin fuente normativa (solo cliente); además inyecta «⚠️ ALERTA …» en `observations` al enviar; `FUNCTIONAL_COVERAGE_MATRIX CV-F07` la cuenta como «validación ±10 %» | `OperationFormPage.tsx:384-395, 613-614, 743-751` · familia `R-147` | B |
| **`R-170`** | **P1** · **CERRADO** (técnico, tranche 8, `GA-REM-005-C` · `BR-21`) | **doble contabilidad de nacimientos**: el formulario emite «Total nacidos» + machos + hembras + «Débiles» como cuatro filas de `bird_movements` y el saldo, los viables y el KPI suman todas (observado: 100 pollitos → viables 200, saldo 200); sin rama de reglas para `BIRTH_REGISTRATION` | `OperationFormPage.tsx:1568-1590` · `service.py:852-892` · `validators.get_viable_chick_balance` | B |
| `R-171` | P2 | la etapa `hatchery` del catálogo no ofrece `cull_recording` ni `mortality_recording`, que son lo que viables y rendimiento restan (`Bases` p.10, Rec. §12) | `processCatalog.ts:226-229, 403-412` | B |
| `R-172` | P2 | `get_egg_balance` suma todas las `egg_type` de la recolección (sucios, rotos, infértiles, descartados) como huevos disponibles para despacho; `BR-02` habla de fértiles disponibles (semántica, no concurrencia) | `validators.py:91-114` | B |
| `R-173` | P2 | mutaciones posteriores al alta con efecto en saldo sin revalidación ni bloqueo: `PUT` que cambia `lot_id` mueve el efecto entre lotes; `cancel` de una entrada (recolección, recepción, nacimiento, recepción de aves) tras salidas deja el saldo negativo; las cuatro familias de saldo | `service.py:1071-1078, 1133-1150` | B |
| `R-174` | P3 | `chick_dispatch` con cantidad 0 se acepta: `if total_qty > 0` salta `validate_chick_dispatch` (residuo de la clase `R-130 AC04`) | `service.py:883` | B |
| `R-175` | P3 | aislamiento de pruebas: `test_lot_start_date`, `test_lots_bu_enforcement` y `test_od14_productive_surfaces` crean una `ProductivePhase` y no la retiran; `test_clean_baseline::test_t_025_07` («las fases se duplicaron: 5») cae en cualquier invocación no alfabética que las ejecute antes (visto en los tranches 7, 8 y 9; demostrado por pares ordenados; en orden alfabético no se manifiesta) | `tests/test_lot_start_date.py:246` · `tests/test_lots_bu_enforcement.py` · `tests/test_od14_productive_surfaces.py` | B (higiene) |

Trazas parciales del tranche 4: **`R-140`** → PARTE A (guarda de estados de `cancel`: `SAP_CONFIRMED`/`SAP_ERROR`/`CANCELLED`) en `GA-REM-006-A`; motivo obligatorio (contrato de ruta que el cliente llama sin cuerpo → UI) y permiso «solo administrador» (`AOD-18`) → OPEN. **`R-154`** → subconjunto `DRAFT` (mapa de transiciones + controles) y `version` (semántica vigente documentada: avanza en `PUT` y corrección; la matriz 360 lo daba por no incrementado) en `GA-REM-006-A`; dos «cierres» (`AOD-08`) y `LotStatus.CANCELLED` → OPEN. `R-163` normalizada a **P1**.

---

## Cierre de `R-135` + `R-143` · continuidad de estados de `P-07` y segregación corrector/rechazador ≠ aprobador · WAVE B tranche 4 (2026-09-09)

```
R-135    CERRADO (técnico)   GA-REM-006 enmienda A · OD-17.a/b · RETURNED/REJECTED reenviables (submit → PENDING_REVIEW, explícito, auditado)
                            · REJECTED editable y corregible · mapa explícito EDITABLES/REENVIABLES/NO_CANCELABLES · cadena inquilino/unidad
                            en POST /corrections · AC-S01…S12 · AC-R01…R07 · AC-D01…D06 · AC-U01…U05 · 24/24 · rojo previo 13 rojas de 23
R-143    CERRADO (técnico)   GA-REM-007 enmienda A · aprobador ∉ {registrador, correctores, quien rechazó} bajo require_segregation (docs/12 R2,
                            OD-17.b) · AC-G01…G07 · 6/6 · rojo previo 3 rojas
R-140    PARTIAL             PARTE A cerrada (cancel denegado desde SAP_CONFIRMED/SAP_ERROR/CANCELLED) · OPEN: motivo obligatorio (el cliente llama
                            cancel sin cuerpo → UI) · permiso «solo administrador» (AOD-18)
R-154    PARTIAL             DRAFT en el mapa de transiciones (editable, no reenviable, no aprobable por edición) · version documentada (avanza en PUT
                            y corrección) · OPEN: dos «cierres» (AOD-08) · LotStatus.CANCELLED sin productor
                            sensibilidad S1–S8, S10, S11 válidas · S9 N/A · relacionadas 353/353 · certificación de proceso: BLOCKED_RUNTIME
WAVE B   IN PROGRESS        22 ítems · 7 cerrados (R-130 · R-160 · R-163 · R-159 · R-162 · R-135 · R-143) · 2 parciales (R-140 · R-154) · 13 abiertos
                            siguiente tranche (identificado, no iniciado): R-136 parte interna (reverso, BR-16) + R-165; alternativa GA-REM-021 agua
```

Evidencia: `R-135-R-143-STATE-CONTINUITY-EVIDENCE.md`. Regresión completa: **949 passed · 49 skipped · 0 failed** (735 s; 919 previas + 30 de `test_state_continuity.py`/`test_segregation_r143.py`); los 49 saltados son `test_upgrade_path` y `test_runtime_startup`, que exigen su script dedicado). `vitest` 87/87 · `tsc` 6 preexistentes (`R-158`). Migración `t0u1v2w3x4y5z6a7b8c9` (autorizada por `GA-REM-021-B §B.5`, tras el commit de spec `f878ab6`). Rutas 211. `R-161` OPEN · `R-164` BLOCKED_RUNTIME · `R-166` OPEN · fase 9 FROZEN · `BU-D10` PENDING_RATIFICATION · SAP no iniciado.

---

## Pre-flight del tranche 5 · `R-136` reverso interno · **STOP sin código** (2026-09-09)

```
R-136    OPEN · P1           componente interno: OWNER_DECISION_REQUIRED (AOD-21) — ninguna fuente define estado, contrapartida, elegibilidad ni
                            autoridad del reverso pre-SAP (BR-16/R16 son post-SAP; OD-17.a lo nombra como clase terminal; Rec. §24 no versionada)
                            componente post-SAP: SAP_DEFERRED (GA-REM-017 BLOCKED_EXTERNAL · AOD-04 · OD-12)
                            corrección documental: la fila 8 de WAVE_B §1 decía «lo gobiernan BR-16 y docs/12 R5» — verificado: no lo gobiernan
R-165    OPEN · P2           evaluado: superficie PRODUCTIVE_REVIEW; misma guarda compartida que G/H; sin decisión pendiente; ejecutable como tranche
                            propio o acompañante (no admitido solo en la forma de este tranche) → sigue OPEN
R-164    BLOCKED_RUNTIME     sin cambio (no se intentó la base remota)
WAVE B   IN PROGRESS        22 ítems · 7 cerrados · 2 parciales (R-140 · R-154 · R-136 · GA-REM-021) · 10 abiertos · decisiones 6
                            siguiente tranche (identificado, no iniciado): GA-REM-021 agua (P1, SPEC_READY; B04 fuera hasta AOD-14) · acompañante posible: R-165
```

Artefactos: `R136_INTERNAL_REVERSAL_PREFLIGHT.md` · `R136_INTERNAL_REVERSAL_EFFECT_MATRIX.md` · `AOD-21`. Sin código, sin migración, sin pruebas nuevas; nada certificado; nada cerrado.

---

## Cierre de `R-136` (interno) + `R-165` · reverso interno de registros aprobados · WAVE B tranche 5 (2026-09-09)

```
R-136    PARTIAL             componente INTERNO CERRADO (técnico): OD-19 · GA-REM-041 · REVERSED (migración t0u1v2w3x4y5z6a7b8c9d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7
                            aprobada por el motor existente · exactamente una (FOR UPDATE + solicitud activa 409) · saldos netos con
                            contrapartidas efectivas (R-130 intacto) · original inmutable · motivo y auditoría · 22/22 · rojo previo 21
                            componente SAP: SAP_DEFERRED · consolidados: DEFERRED · huevos/incubación: BLOCKED_BY_R-161 (OD-19 §11, §18)
R-165    CERRADO (técnico)   el plano de revisión (start · return · complete · approve · reject) exige la habilitación de la unidad a la
                            autoridad global (403) · actor de empresa y plano de control intactos · 5/5 · rojo previo 1
                            sensibilidad: ver evidencia · relacionadas 498/498 · certificación de proceso: BLOCKED_RUNTIME
WAVE B   IN PROGRESS        22 ítems · 8 cerrados (R-130 · R-160 · R-163 · R-159 · R-162 · R-135 · R-143 · R-165) · 3 parciales (R-140 · R-154 · R-136)
                            · 11 abiertos · siguiente tranche (identificado, no iniciado): GA-REM-021 agua (P1, SPEC_READY; B04 fuera hasta AOD-14)
```

Evidencia: `R-136-INTERNAL-REVERSAL-EVIDENCE.md`. Regresión completa: **976 passed · 49 skipped · 0 failed** (807 s; 949 previas + 27 nuevas); los 49 saltados son `test_upgrade_path` y `test_runtime_startup`, que exigen su script dedicado). `vitest` 87/87 · `tsc` 6 preexistentes (`R-158`). Migración `t0u1v2w3x4y5` (autorizada por `OD-19 §1`). Rutas 208 → 211. `R-161` OPEN · `R-164` BLOCKED_RUNTIME · `R-166` OPEN · fase 9 FROZEN · `BU-D10` PENDING_RATIFICATION · SAP no iniciado.

---

## Pre-flight del tranche 6 (2026-09-09): roles del reverso · `B05` gobernado

`OD-19` Aclaración A (propietario): «Supervisor Avícola» → `reversals:create` + `reversals:read`; «Contralor Avícola» (figura de
contraloría, `integration_seeds`) → `reversals:read`; Administrador de Accesos y roles operativos → ninguno; `dev_seeds` no tiene
rol de Contraloría y no se inventa. `GA-REM-041` enmienda A (`REV-R01…R08`). `B05` (`R-13`): `GA-REM-021` enmienda A con matriz de
aplicabilidad y contrato de datos; `RR-10` (litros) y `RR-11` (`> 0`) resueltos por evidencia de nivel 5/6 sin escalado; `AOD-19`
no gobierna `B05`. Sin código en este commit.

---

## Cierre de `B05` (`R-13`) + roles del reverso · WAVE B tranche 6 (2026-09-09)

```
OD-19 Acl. A CERRADA (técnico)  Supervisor Avícola → reversals:create + read · Contralor Avícola → read · Administrador de Accesos y operativos → ninguno ·
                            SOLO_SUPER_ADMIN 15 → 13 · GA-REM-041-A certificada (REV-R01…R08 · 5/5 + RBAC · sensibilidad S9 a/b/c) ·
                            GA-REM-041-B certificada: la decisión llega a instalaciones existentes por migración de datos v2w3x4y5z6a7 y al baseline
                            (matriz compuesta, GA-REM-025 AC03 46 → 48; REV-R09…R12 · 3/3 + t_025_02; S9d/S9e) — hallazgo de la 1ª regresión completa
R-13 / B05  CERRADO (técnico)  evento water_consumption + water_liters (litros, > 0; RR-10/RR-11) · solo Reproductoras y Engorde (Bases p.2/4/12) ·
                            un dato, un registro (prohibido en otros tipos) · aditivo por día · editable y corregible · no reversible · cadena
                            inquilino/unidad/concesión certificada (S3–S5) · migración u1v2w3x4y5z6 · frontend mínimo (catálogo, formulario, reporte) ·
                            16/16 · rojo previo 15 · sensibilidad S1–S6, S9, S10 válidas (S7/S8 N/A)
GA-REM-021  PARTIAL           B05 cerrado · B01 (cuadre) · B02 (pesos en rango) · B03 (alimento) · B13 (sanos/débiles) abiertos (enmienda B pendiente) ·
                            B04 bloqueado por AOD-14 · R-156 bloqueado por AOD-20 · KPI de agua: ola C
WAVE B   IN PROGRESS        22 ítems · 8 cerrados · 4 parciales (R-140 · R-154 · R-136 · GA-REM-021) · 10 abiertos · decisiones 6
                            siguiente tranche (identificado, no iniciado): GA-REM-021 B01 + B02 (cuadre y pesos en rango en recepción, Rec. §6; usan el
                            saldo de R-130) — requiere enmienda B previa; alternativa: R-152 → R-153 (Progenitoras, spec propia)
```

Evidencia: `GA-REM-021-B05-WATER-CAPTURE-EVIDENCE.md`. Regresión completa: **1000 passed · 49 skipped · 0 failed** (819 s, 2ª pasada; la 1ª dejó 2 rojas corregidas por `GA-REM-041-B`; 976 previas + 16 agua + 5 matriz de roles + 3 migración de roles; los 49 saltados son `test_upgrade_path` y `test_runtime_startup`, que exigen su script dedicado). `vitest` 89/89 · `tsc` 6 preexistentes (`R-158`). Migraciones `u1v2w3x4y5z6` (autorizada por `GA-REM-021-A §A.5`, tras el commit de spec `c8447de`) y `v2w3x4y5z6a7` (datos de roles, autorizada por `GA-REM-041-B`, tras `8df04f7`). Rutas 211 (sin cambio). `R-161` OPEN · `R-164` BLOCKED_RUNTIME · `R-166` OPEN · fase 9 FROZEN · `BU-D10` PENDING_RATIFICATION · SAP no iniciado.

---

## Pre-flight del tranche 7 (2026-09-10): `B01` y `B02` gobernados · sin decisión del propietario · sin código

`B01` («hembras + machos + mortalidad + rechazo cuadren contra recibido», Rec. §6) **no** es el contrato de `OD-04`/`GA-TD-014` (la OC,
viñeta anterior del mismo §6, sigue en `BR-18`): es la identidad interna del evento `bird_reception` de reproductoras, con tres datos
nuevos (`received_total`, `dead_on_arrival`, `rejected_on_arrival`) y la regla `BR-20`; las alojadas siguen siendo las entradas del saldo
(`R-130` sin cambio). `B02` («pesos dentro de rango esperado») está gobernado por `GA-REQ-037` + `OD-06` + `GA-REM-037`: el referente es
la curva fijada al lote a la edad del día de la recepción; fuera de rango alerta y no bloquea; la cautela del tranche 6 queda desestimada
(`RR-13`). CASO A: ambos se implementan. Matrices `GA_REM_021_B01_…` y `GA_REM_021_B02_…`; `GA-REM-021` enmienda B; `GA-REM-037` enmienda B;
`RC-11` (`RR-12`, `RR-13`). Hallazgos nuevos `R-167`, `R-168`, `R-169` (P3, no se resuelven aquí). Corrección de la ola B: «`B01` usa el
saldo» → `B01` gobierna lo que **entra** al saldo. Recuento revalidado: 22 · 8 cerrados · 4 parciales · 10 abiertos.

---

## Cierre de `B01` + `B02` · cuadre y pesos en rango en la recepción de reproductoras · WAVE B tranche 7 (2026-09-10)

```
B01 / H360-B01  CERRADO (técnico)  recibido = Σ alojadas + mortalidad al arribo + rechazo (BR-20; RR-12) · tres enteros nuevos (migración
                            w3x4y5z6a7b8) · obligatorios y explícitos en reproductoras · engorde solo mortalidad inicial · alojadas del
                            servidor · edición revalidada · sumandos no corregibles uno a uno · saldo = alojadas (R-130 intacto) · 8/8 ·
                            rojo previo 6 · sensibilidad B01-S1/S4/S5/S6/S7 + SEC-S1…S4 válidas (B01-S2/S3 N/A)
B02 / H360-B02  CERRADO (técnico)  referente = curva fijada al lote a la edad del día (OD-06 · GA-REM-037; RR-13) · alerta, no bloqueo ·
                            NO_REFERENCE declarado · engorde N/A · detalle con evaluación · GA-REM-037 enmienda B (puerta de la alerta;
                            motor intacto) · 8/8 · rojo previo 2 (+1 de arnés) · sensibilidad B02-S1/S2/S3/S5 válidas (B02-S4 N/A)
GA-REM-021  PARTIAL           B05 · B01 · B02 cerrados · B03 (alimento) · B13 (sanos/débiles) abiertos (enmienda C pendiente) · B04 ◄── AOD-14 ·
                            R-156 ◄── AOD-20 · KPI: ola C
WAVE B   IN PROGRESS        22 ítems · 8 cerrados · 4 parciales (R-140 · R-154 · R-136 · GA-REM-021) · 10 abiertos · decisiones 6
                            siguiente tranche (identificado, no iniciado): GA-REM-021 B03 (+ B13 si independiente) — enmienda C previa ·
                            alternativa: R-152 → R-153 (Progenitoras)
```

Evidencia: `GA-REM-021-B01-B02-RECEPTION-EVIDENCE.md`. Regresión completa: **1016 passed · 49 skipped · 0 failed** (935 s; 1000 previas + 16 nuevas; los 49 saltados son `test_upgrade_path` y `test_runtime_startup`, que exigen su script dedicado). `vitest` 89/89 · `tsc` 6 preexistentes (`R-158`). Migración `w3x4y5z6a7b8` (autorizada por `GA-REM-021-B §B.5`, tras el commit de spec `f878ab6`). Rutas 211 (sin cambio). `R-167`/`R-168`/`R-169` registrados (P3). `R-161` OPEN · `R-164` BLOCKED_RUNTIME · `R-166` OPEN · fase 9 FROZEN · `BU-D10` PENDING_RATIFICATION · SAP no iniciado.

---

## Pre-flight del tranche 8 (2026-09-10): `R-167` no reproducido · `R-169`/`R-168` activos · `R-170` (P1) activo · `B13` gobernado · `B03` a decisión · sin código

`R-167`: ninguna ruta descuenta `dead_on_arrival`; el alta no fabrica mortalidad; las alojadas entran una vez (prueba) → **NOT_REPRODUCED**, cerrado
(residuo: doble captura por el operador = instrucción de proceso; KPI → ola C). `R-169`: dos ocurrencias activas en el formulario de recepción
(recuadro ±10 % y texto inyectado en `observations`), cantidad vs OC, sin fuente, contrarias a `OD-04` → `GA-REM-035-A`. `R-168`: «Muestra tomada»
capturada por galpón y descartada por el esquema → `GA-REM-021-C §C.2`. **`R-170`** (nuevo, P1): el nacimiento cuenta el total y su desglose
(viables 200 para 100 pollitos) → `GA-REM-005-C` (`BR-21`), se corrige **antes** de `B13`. `B13`: gobernado (sanos/débiles como atributos,
`≤ nacidos`; igualdad `AOD-23`). `B03`: `OWNER_DECISION_REQUIRED` (`AOD-22`: parciales/diferencia/unidad/persistencia) + `AOD-19` → sin código.
`R-171` registrado. Recuento canónico: **27** (alta formal de `R-167…R-171`, `WAVE_B §18`).

---

## Cierre del tranche 8 · pre-flight de consistencia + `R-170` + `B13` (2026-09-10)

```
R-167    CERRADO (no reproducido)   ninguna ruta descuenta dead_on_arrival; las alojadas entran una vez (prueba) · residuo: instrucción de proceso · KPI → ola C
R-169    CERRADO (técnico)          GA-REM-035-A · sin recuadro ±10 % ni texto inyectado en observations; tarjeta de la OC sin umbral · era cantidad vs OC · P2
R-168    CERRADO (técnico)          «Muestra tomada» como sample_size de evento; sin campos por galpón · control backend · P2
R-170    CERRADO (técnico)          GA-REM-005-C · BR-21 (una fila por sexo · mixed excluyente · Σ ≥ 1) · formulario sin fila total · viables = nacidos · P1
B13 / H360-B13  CERRADO (técnico)   chicks_healthy / chicks_weak · obligatorios y explícitos en incubadora · ≤ nacidos · sin efecto en saldo · débil ≠ descarte ·
                            edición y corrección revalidadas · 6/6 · rojo previo 5 (+1 arnés) · sensibilidad S-R170-1 · S-B13-1/2/3/5/6/7/8/9 · SEC-S1 · S-R169-1 · S-R168-1
B03 / H360-B03  OWNER_DECISION_REQUIRED  AOD-22 (parciales/diferencia/unidad/cero) + AOD-19 · sin código
R-171    OPEN (registrado, P2)      incubadora sin descarte/mortalidad en el catálogo
GA-REM-021  PARTIAL                 B05 · B01 · B02 · B13 cerrados · B03 ◄── AOD-22 · B04 ◄── AOD-14 · R-156 ◄── AOD-20
WAVE B   IN PROGRESS                27 ítems (canónico) · 12 cerrados · 4 parciales · 11 abiertos · decisiones 8 (AOD-08 · 14 · 17 · 18 · 19 · 20 · 22 · 23)
                            siguiente tranche (identificado, no iniciado): R-161 (saldos de huevos/incubación sin bloqueo; P2; sin decisión) + R-171 ·
                            alternativa: R-152 → R-153
```

Evidencia: `WAVE_B_TRANCHE_8_PREFLIGHT_AND_B13_EVIDENCE.md`. Regresión completa: **1024 passed · 49 skipped · 0 failed** (857 s; 1016 previas + 8 nuevas; los 49 saltados son `test_upgrade_path` y `test_runtime_startup`, que exigen su script dedicado). `vitest` 95/95 · `tsc` 6 preexistentes (`R-158`). Migración `x4y5z6a7b8c9` (autorizada por `GA-REM-021-C §C.5`, tras el commit de spec `ec974f0`). Rutas 211. `R-161` OPEN · `R-164` BLOCKED_RUNTIME · `R-166` OPEN · fase 9 FROZEN · `BU-D10` PENDING_RATIFICATION · SAP no iniciado.

---

## Pre-flight del tranche 9 (2026-09-10): `R-161` gobernado · `R-171` UI_ONLY y gobernado, raíz distinta · modo R161_ONLY · sin código

`R-161`: dos saldos (`BR-02` del lote en granja, `BR-03` en incubadora), un decremento cada uno (`egg_dispatch`, `incubation_load`) leído sin
`bloquear_saldo_del_lote`; la fila autoritativa es `lots.id` (misma primitiva que `R-130`); corrección y aprobación N/A; el servicio salta la
validación con cantidad 0 → `GA-REM-005` enmienda D. `R-171`: el backend acepta y contabiliza `mortality_recording`/`cull_recording` en lotes de
incubadora; solo falta el catálogo (`UI_ONLY`, `RR-16`); raíz distinta de `R-161` → queda OPEN, siguiente. Registrados `R-172`, `R-173`, `R-174`
(no se corrigen aquí). Recuento revalidado: 27 · 12 · 4 · 11 (antes de las altas de este pre-flight).

---

## Cierre de `R-161` · saldos de huevos e incubación bajo el bloqueo del lote · WAVE B tranche 9 (2026-09-10)

```
R-161    CERRADO (técnico)   GA-REM-005 enmienda D · validate_egg_dispatch y validate_incubation_load bloquean la fila del lote antes de leer el
                            saldo (misma primitiva que R-130) · cantidad 0 rechazada (sin guarda if total > 0) · carreras observadas (5 × 70 sobre 100
                            en tres lotes por familia: −250) y cerradas ([201, 400 ×4], saldo 30) · bloqueo por recurso · corrección/aprobación N/A ·
                            7/7 · rojo previo 3 · sensibilidad R161-S1…S10 válidas
R-171    OPEN                UI_ONLY · gobernado (RR-16) · raíz distinta → siguiente tranche
R-172 · R-173 · R-174  OPEN  registrados en el pre-flight (P2 · P2 · P3) · R-175 OPEN (P3, aislamiento de pruebas: tres suites dejan una fase productiva)
WAVE B   IN PROGRESS        31 ítems (canónico) · 13 cerrados · 4 parciales · 14 abiertos · decisiones 8
                            siguiente tranche (identificado, no iniciado): R-171 (+ R-173 si independiente) · alternativa: R-152 → R-153
```

Evidencia: `R-161-EGG-INCUBATION-CONCURRENCY-EVIDENCE.md`. Regresión completa: **1031 passed · 49 skipped · 0 failed** (1210 s; 1024 previas + 7 nuevas; los 49 saltados son `test_upgrade_path` y `test_runtime_startup`, que exigen su script dedicado). `vitest` 95/95 · `tsc` 6 preexistentes (`R-158`). Sin migración (cabeza `x4y5z6a7b8c9`). Rutas 211. `R-166` OPEN · `R-164` BLOCKED_RUNTIME · `OD-19 §18` (huevos no reversibles) sin cambio · fase 9 FROZEN · `BU-D10` PENDING_RATIFICATION · SAP no iniciado.

---

## Pre-flight del tranche 10 (2026-09-10): `R-173` gobernado (P1) · `R-172` gobernado · `R-174` gobernado · `R-171` UI_ONLY confirmado · `R-175` NON-BLOCKING · modo A · sin código

Repositorio verificado: `main` · `4f70273` · limpio · local == remoto · cabeza `x4y5z6a7b8c9` · rutas 211.

`R-173` (`R173_EDIT_CANCEL_BALANCE_EFFECT_MATRIX.md`): los cuatro saldos son agregados dinámicos por `lot_id` y `status ≠ CANCELLED`; cambiar `lot_id`
(por `PUT` **y por `POST /corrections`**) mueve el efecto entero sin regla de saldo ni bloqueo, y en la corrección **sin empresa, unidad, lote activo, fecha
ni ubicación** (reasignación entre empresas posible); cancelar una entrada tras salidas deja el saldo `< 0`. Fuentes de nivel 3/4 ya gobiernan (editar
antes de enviar · destino de una edición = alta `AC-W09` · invariante `B.2`/`D.1.4` · auditoría con valores `docs/13`): modelo B, **sin decisión**;
`GA-REM-005` enmienda E corrige la premisa de `B.2`. Severidad normalizada **P1** (saldo negativo + bypass de inquilino). `RC-15`/`RR-18`.
`R-172` (`R172_EGG_TYPE_AVAILABILITY_MATRIX.md`): `Bases` p.7-9, `docs/02 §3.6.4/§3.7.1`, `spec.md :166/:187` despachan y reciben **huevo fértil**;
la implementación suma todos los tipos (100 fértiles + 60 otros → despacha 160). **ACTIVE, gobernado**: predicado único `fertile` para `BR-02` y `BR-03`
(dos saldos, un predicado), sin borrar filas; `GA-REM-005` enmienda F; `RC-14`/`RR-17`. `R-174` (`R174_ZERO_QUANTITY_DISPATCH_AUTHORITY_TRACE.md`):
`B.2` nombra «despacho de pollitos» en `D` con `cantidad > 0` → gobernado; enmienda E §E.3. `R-171` (`R171_…_TRUTH_MATRIX.md §4`): UI_ONLY confirmado
releyendo backend, catálogo, formulario e idiomas → `GA-REM-021` enmienda D. `R-175` (`R175_TEST_ORDER_DEPENDENCY_CONTROL.md`): 4/4 aisladas verdes,
3/3 B→A verdes, 3/3 A→B rojas por «las fases se duplicaron: 5» (residuo reproducido bajo control) → NON-BLOCKING, OPEN, sin limpieza.

**Puerta de composición** (prompt §52): `R-173` ACTIVE · `R-172` ACTIVE · `R-174` ACTIVE · `R-171` UI_ONLY · `R-175` NON-BLOCKING → **modo A**
(`R-173` + `R-172` + `R-174` + `R-171`, en ese orden). Sin decisión del propietario nueva. Sin migración prevista.

Registrados en este pre-flight (fuera del alcance del tranche):

| ID | P | Hallazgo | Dónde | Ola |
|---|---|---|---|---|
| `R-176` | P3 | la edición no vuelve a correr reglas de destino no keyed por lote: `sap_document_ref` (`BR-18`, acumulado de la OC; `validate_oc_limit` tiene `exclude_event_id` sin uso), `house_id` (`BR-17`, capacidad estática), `event_date` sola (`validate_event_date`/`validate_period_open` solo si cambia `lot_id`); sin efecto en los cuatro saldos | `service.py:1071-1088` | B |
| `R-177` | P3 | `egg_type` es `String(30)`/`str` sin lista de valores (enum de `docs/03 :277` no aplicado); el formulario de recepción en incubadora envía categorías de ovoscopía (`dead_early`, `dead_late`, `contaminated`; `docs/02 §3.7.3`) como tipos recibidos; informativo tras `R-172` | `models.py:203` · `schemas.py:25` · `OperationFormPage.tsx:1479-1497` | B |
| `R-178` | P3 | `egg_batches`/`chick_batches` (linaje) se materializan al casar despacho y recepción y no se neutralizan ni re-casan al cancelar o mover de lote un despacho/recepción; no es saldo | `service.py:401-500` | B |

```
R-173    OPEN · P1 (normalizado)   ACTIVE · gobernado (modelo B) · GA-REM-005-E · sin decisión
R-172    OPEN · P2                 ACTIVE · gobernado (fértil) · GA-REM-005-F · sin decisión
R-174    OPEN · P3                 ACTIVE · gobernado (B.2) · GA-REM-005-E §E.3
R-171    OPEN · P2                 UI_ONLY confirmado · GA-REM-021-D
R-175    OPEN · P3                 NON-BLOCKING · matriz de control · sin corrección
R-176 · R-177 · R-178  OPEN · P3   registrados (fuera)
WAVE B   IN PROGRESS        34 ítems (canónico: 31 + R-176 + R-177 + R-178) · 13 cerrados · 4 parciales · 17 abiertos (P1 1 · P2 8 · P3 8) · decisiones 8
```

---

## Cierre de `R-173` · `R-172` · `R-174` · `R-171` · WAVE B tranche 10 (2026-09-10)

```
R-173    CERRADO (técnico)   GA-REM-005 enmienda E · guarda central verificar_destino_de_edicion (PUT y POST /corrections: empresa · unidad · lote activo ·
                            fecha · ubicación · regla de saldo del destino como alta · origen ≥ 0) bajo el bloqueo de los lotes en orden ascendente ·
                            anulación de entradas con saldo ≥ 0 bajo bloqueo y relectura (una sola transición) · auditoría con valores anterior/nuevo ·
                            P1 normalizado · 16/16 · rojo previo 10 (+ 2 carreras con saldo −100 observado) · sensibilidad R173-S1…S5 válidas
R-172    CERRADO (técnico)   GA-REM-005 enmienda F · cuenta_como_disponible(egg_type) = fertile en BR-02 (entrada y salida) y BR-03 (entrada) · el despacho
                            rechaza otros tipos (BR-02) · filas capturadas intactas · formulario de despacho con una sola fila · 9/9 + vitest · rojo previo 8 + 1 ·
                            sensibilidad R172-S1…S5 válidas · R-161 7/7 intacto · RC-14/RR-17
R-174    CERRADO (técnico)   GA-REM-005 enmienda E §E.3 · rama CHICK_DISPATCH sin la guarda if total_qty > 0 · 0 → 400 BR-04 sin fila, sin auditoría, sin
                            notificación · negativo 422 · sensibilidad R174-S1 válida
R-171    CERRADO (técnico)   GA-REM-021 enmienda D · STAGE_OPERATIONS.hatchery + mortality_recording/cull_recording · STAGE_FLOWS.hatchery + dos pasos tras el
                            nacimiento · i18n existente · backend sin cambio (AC-R161-16) · vitest 5/5 · sensibilidad R171-S1/S1b válidas (S2 N/A por arquitectura)
R-175    OPEN (P3)           control documentado (aisladas 4/4 · B→A 3/3 · A→B 3/3 rojas «5 fases») · NON-BLOCKING · sin limpieza (R175_TEST_ORDER_DEPENDENCY_CONTROL.md)
R-176 · R-177 · R-178  OPEN (P3, registrados en el pre-flight)
WAVE B   IN PROGRESS        34 ítems (canónico) · 17 cerrados · 4 parciales · 13 abiertos (P1 0 · P2 6 · P3 7) · decisiones 8
                            siguiente tranche (identificado, no iniciado): R-152 → R-153 (Progenitoras) · alternativa: R-176 + R-178 (edición y linaje) o R-175 (higiene)
```

Evidencia: `WAVE_B_TRANCHE_10_BALANCE_INTEGRITY_EVIDENCE.md`. Regresión completa: **1056 passed · 49 skipped · 0 failed** (1173 s; 1031 previas + 25 nuevas; los 49 saltados son test_upgrade_path y test_runtime_startup, que exigen su script dedicado). `vitest` 102/102 · `tsc` 6 preexistentes (`R-158`).
Sin migración (cabeza `x4y5z6a7b8c9`). Rutas 211. `R-166` OPEN · `R-164` BLOCKED_RUNTIME · `OD-19 §18` sin cambio · fase 9 FROZEN · `BU-D10` PENDING_RATIFICATION · SAP no iniciado.

---

## Pre-flight del tranche 11 (2026-09-10): `R-176` gobernado (P2, absorbe `R-45`) · `R-178` gobernado · `R-177` pre-flight (AOD-24) · `R-175` control · modo R176_PLUS_R178 · sin código

Repositorio verificado: `main` · `80cce71` · limpio · local == remoto · cabeza `x4y5z6a7b8c9` · rutas 211 (guardián `test_ac14`).

`R-176` (`R176_CREATE_EDIT_CORRECTION_VALIDATION_PARITY_MATRIX.md`): seis reglas puras del alta (`BR-17`, `BR-18`, `BR-06`, `BR-19`, `BR-08`,
`BR-11`/`BR-10`) no se reevalúan al editar ni corregir los campos que las disparan (`house_id`, `sap_document_ref`, `event_date`, `farm_id`, `lot_id`);
`POST /corrections` es la segunda superficie. Es la misma raíz que **`R-45`** (Wave 2, P2, «corregir `event_date` no revalida `BR-19`», abierto en
`GA-REM-016`/`GA-REM-019`, documentado en `test_corrections.py` con aserción tolerante): `R-176` lo absorbe. Autoridad: `AC-W09`/`RR-18` (destino de una
edición = alta), `GA-REM-023` (contrato de validación), `GA-REM-035`, `R-30`, `R6`, `spec.md` → paridad sin repetir el alta, en la guarda central de
`R-173`. **Sin decisión.** Severidad normalizada **P2** (la de `R-45`; `BR-18` permite superar la OC moviendo el acumulado) → `GA-REM-023` addendum B.
`R-178` (`R178_LINEAGE_CANCEL_MOVE_INTEGRITY_MATRIX.md`): linaje = trazabilidad generacional (`egg_batches`/`chick_batches`), no genética; el árbol lista
como vigente un traspaso cuyo despacho fue anulado y un evento casado puede moverse dejando el vínculo con orientación falsa. Autoridad: `OD-10 §2.4/2.5/4bis/4bis.5`,
`BR-10`, `GA-REM-008 AC04/AC06`, `GA-REM-031 AC03` → histórico conservado + efectivo derivado en lectura + reasignación denegada si hay vínculo. **Sin
decisión, sin migración** → `GA-REM-031` enmienda A. `R-177` (`R177_EGG_TYPE_OVOSCOPY_DOMAIN_MATRIX.md`): **registro corregido** (el bloque con categorías
de ovoscopía es del evento `ovoscopy`, no de la recepción); DATA QUALITY DEFECT confirmado (cadena libre; UI cruda; `commercial` sin etiqueta) + modelo
(tipo de huevo ≠ resultado de ovoscopía en el mismo campo) → **`OWNER_DECISION_REQUIRED` (`AOD-24`)**; sin código. `R-175`: control ampliado con las
suites nuevas (§4 de la matriz; se ejecuta antes de la regresión completa).

**Puerta de composición** (prompt §50): `R-176` activo · gobernado · sin decisión · ejecutable — `R-178` activo · linaje = trazabilidad generacional ·
gobernado · sin decisión · ejecutable — `R-177` pre-flight completo, sin implementación — `R-175` no bloqueante → **modo `R176_PLUS_R178` (CASE A)**.

```
R-176    OPEN · P2 (normalizado; absorbe R-45)   ACTIVE · gobernado · GA-REM-023-B · sin decisión
R-178    OPEN · P3                              ACTIVE · gobernado · GA-REM-031-A · sin decisión · sin migración
R-177    OPEN · P3 · OWNER_DECISION_REQUIRED    AOD-24 · pre-flight completo · registro corregido · sin código
R-175    OPEN · P3                              control ampliado en curso
R-45     OPEN (Wave 2, P2)                      absorbido por R-176; se cierra con él por prueba (AC-R176-05)
WAVE B   IN PROGRESS        34 ítems · 17 cerrados · 4 parciales · 13 abiertos (P1 0 · P2 7 · P3 6) · decisiones 9 (AOD-24 nueva)
```

---

## Cierre de `R-176` (+ `R-45`) · `R-178` · `R-175` · WAVE B tranche 11 (2026-09-10) — `R-177` OWNER_DECISION_REQUIRED (`AOD-24`)

```
R-176    CERRADO (técnico)   GA-REM-023 addendum B · las reglas puras del alta (BR-08 · BR-06 · BR-19 · BR-11/BR-10 · BR-17 · BR-18) se reevalúan sobre el
                            estado candidato en la guarda central (_reglas_puras_del_candidato), en PUT y en POST /corrections, sin repetir el alta
                            (AC-R176-09) · P2 · 7/7 · rojo previo 5 (+1 aserción corregida, crédito 0) · sensibilidad R176-S1…S5 válidas · absorbe R-45
R-45     CERRADO (técnico)   (Wave 2, P2) corregir event_date vuelve a pasar por BR-19: test_corrections exige ahora el 400 (AC-R176-05)
R-178    CERRADO (técnico)   GA-REM-031 enmienda A · el árbol de trazabilidad muestra el linaje efectivo (despacho anulado: desaparece; recepción anulada:
                            incompleto) derivado del estado de los eventos, sin borrar la fila (BR-10) · un evento casado no se reasigna (lote ni destino
                            declarado) · 7/7 · rojo previo 4 · sensibilidad R178-S1…S3 válidas (S4 N/A: dinámico) · sin migración
R-175    CERRADO (técnico)   GA-REM-015 addendum B · pasó a bloqueante por un rojo falso en el verde dirigido (§49) · las tres suites retiran la fase
                            productiva que crean (teardown por prefijo) · guardián == 4 intacto · matriz de control ampliada verde (aisladas · A→B · B→A ·
                            T11→A · A→T11 · T11→B · B→T11) · regla permanente C ya no obligatoria para estas suites
R-177    OPEN · P3           OWNER_DECISION_REQUIRED (AOD-24) · pre-flight completo · registro corregido (evento ovoscopy) · sin código
WAVE B   IN PROGRESS        34 ítems (canónico) · 20 cerrados · 4 parciales · 10 abiertos (P1 0 · P2 6 · P3 4) · decisiones 9
                            siguiente tranche (identificado, no iniciado): R-152 → R-153 (Progenitoras) · alternativa: R-166 (carrera approve/reject)
```

Evidencia: `WAVE_B_TRANCHE_11_VALIDATION_PARITY_AND_LINEAGE_EVIDENCE.md`. Regresión completa: **1070 passed · 49 skipped · 0 failed** (931 s; 1056 previas + 14 nuevas; los 49 saltados son test_upgrade_path y test_runtime_startup, que exigen su script dedicado). `vitest` 102/102 · `tsc` 6 preexistentes (`R-158`).
Sin migración (cabeza `x4y5z6a7b8c9`). Rutas 211. `R-166` OPEN · `R-164` BLOCKED_RUNTIME · `OD-19 §18` sin cambio · fase 9 FROZEN · `BU-D10` PENDING_RATIFICATION · SAP no iniciado.

---

## Pre-flight del tranche 12 (2026-09-10): `R-152` gobernado (P2, `GA-REM-042`) · `R-153` OWNER_DECISION_REQUIRED (`AOD-25`) · dependencia probada · modo R152_ONLY · sin código

Repositorio verificado: `main` · `5e9bbee` · limpio · local == remoto · cabeza `x4y5z6a7b8c9` · rutas 211 (guardián `test_ac14`).

`R-152` (`R152_R153_DEPENDENCY_TRACE.md`, `R152_R153_PROGENITORAS_FUNCTIONAL_PARITY_MATRIX.md`, `R152_PROGENITORAS_GAP_MATRIX.md`): la importación de
abuelas es un evento genérico sin esquema (`extra_data` libre con cuatro claves inventadas en el frontend; sin identidades; proveedor/transporte sin
pertenencia; adjuntos sin clase; sin regla de tipo de lote). Progenitoras ≠ Reproductoras: la importación es `PROGENITORAS_SPECIFIC` (`docs/02 §3.4.1`,
`spec.md §4.4`); solo se reutilizan primitivas (evento, filas ♂/♀, evidencias, cadena de acceso certificada `AC-W05/W15/L14`, guarda de edición) con
justificación explícita; `BR-20`, `B02` y el agua siguen siendo de Reproductoras; `BR-17`/`BR-18` quedan en la recepción (paso 4). **Gobernado, sin decisión**
→ `GA-REM-042` (`BR-22`, `RC-16`/`RR-19`), sin migración. `R-153` (`R153_PROGENITORAS_GAP_MATRIX.md`): depende de `R-152` (`HARD_DATA_MODEL` +
`HARD_FUNCTIONAL`: hoy la importación exige lote; el lote automático necesita el plan) y el repositorio calla lo implementación-crítico (qué es
«completar», código del lote, si puebla, convivencia con la vía manual) → **`OWNER_DECISION_REQUIRED` (`AOD-25`)**, sin código.

**Puerta de composición** (prompt §44): `R-152` «`grandparent_import` sin estructura para el plan de importación» · P2 · gobernado · ejecutable · sin decisión —
`R-153` «lote de abuelas no se crea automáticamente al completar la importación» · P3 · no gobernado · no ejecutable · `AOD-25` — `R-153` depende de `R-152`: **SÍ**
(HARD) → **modo `R152_ONLY`**.

Registrado (fuera del tranche): `R-179` (P3): `supplier_id`, `transport_id` (y los demás FK de maestros del evento: causas, vacunas, medicamentos,
planta, `destination_plant_id`) no se verifican contra la empresa efectiva en el alta ni en la edición (clase `R-42`; `verificar_ubicacion` solo cubre
granja/galpón/destino). `GA-REM-042` cubre proveedor y transporte **en la importación**; el resto queda en `R-179`.

| ID | P | Hallazgo | Dónde | Ola |
|---|---|---|---|---|
| `R-179` | P3 | referencias a maestros de otra empresa en los eventos (`supplier_id`, `transport_id`, `cause_id`, `cull_cause_id`, `vaccine_id`, `medication_id`, `destination_plant_id`) sin `verificar_pertenencia` en alta/edición/corrección | `operations/service.py` (`_apply_business_rules`, `verificar_destino_de_edicion`) · `tenancy.py` | B |

```
R-152    OPEN · P2                              ACTIVE · gobernado · GA-REM-042 · sin decisión · sin migración
R-153    OPEN · P3 · OWNER_DECISION_REQUIRED    AOD-25 · depende de R-152 (HARD) · sin código
R-179    OPEN · P3                              registrado (fuera)
WAVE B   IN PROGRESS        35 ítems (canónico: 34 + R-179) · 20 cerrados · 4 parciales · 11 abiertos (P1 0 · P2 6 · P3 5) · decisiones 10 (AOD-25 nueva)
```

---

## Cierre de `R-152` · WAVE B tranche 12 (2026-09-10) — `R-153` OWNER_DECISION_REQUIRED (`AOD-25`)

```
R-152    CERRADO (técnico)   GA-REM-042 · el plan de importación de abuelas (docs/02 §3.4.1) se captura tipado en extra_data.import_plan (PlanDeImportacion) y se
                            valida en el alta, la edición y la corrección (BR-22: solo lote grandparent · identidades embarcada = recibida + mortalidad en traslado,
                            recibida = Σ ♂/♀, llegada ≥ salida, fin de cuarentena ≥ llegada · OC y proveedor declarados · proveedor/transporte de la empresa) ·
                            adjuntos clasificados en cinco clases (evidence_type) · documental (no puebla ni acumula contra la OC) · Progenitoras ≠ Reproductoras
                            (solo primitivas compartidas, justificadas; BR-20/B02/agua siguen siendo de Reproductoras) · frontend: formulario, detalle, clase de adjunto,
                            i18n ES/EN · 18/18 backend + 6/6 vitest · rojo previo 13 + 6 · sensibilidad válida · sin migración
R-153    OPEN · P3           OWNER_DECISION_REQUIRED (AOD-25) · depende de R-152 (HARD) · sin código
R-179    OPEN · P3           registrado (FK de maestros de otra empresa en eventos)
WAVE B   IN PROGRESS        35 ítems (canónico) · 21 cerrados · 4 parciales · 10 abiertos (P1 0 · P2 5 · P3 5) · decisiones 10
                            siguiente tranche (identificado, no iniciado): R-166 (approve/reject concurrentes sobre el mismo CORRECTED) · alternativa: R-179 (pertenencia de maestros en eventos)
```

Evidencia: `WAVE_B_TRANCHE_12_PROGENITORAS_IMPORT_EVIDENCE.md`. Regresión completa: **1088 passed · 49 skipped · 0 failed** (1113 s; 1070 previas + 18 nuevas; los 49 saltados son test_upgrade_path y test_runtime_startup, que exigen su script dedicado). `vitest` 108/108 · `tsc` 6 preexistentes (`R-158`). Sin migración (cabeza `x4y5z6a7b8c9`).
Rutas 211. `R-166` OPEN · `R-164` BLOCKED_RUNTIME · fase 9 FROZEN · `BU-D10` PENDING_RATIFICATION · SAP no iniciado · E2E `BLOCKED_RUNTIME` (guion `proceso-p01` actualizado).

---

## Pre-flight del tranche 13 (2026-09-10): `R-179` gobernado (P3 → **P1**) · `R-166` gobernado (P3 → **P2**) · modo R179_PLUS_R166 · sin código

Repositorio verificado: `main` · `a93d4d1` · limpio · local == remoto · cabeza `x4y5z6a7b8c9` · rutas 211.

`R-179` (`R179_MASTER_REFERENCE_AUTHORITY_MATRIX.md`): **reproducido por API** — un evento de la empresa A acepta catálogos de la empresa B en las siete
familias (`supplier_id`, `transport_id`, `cause_id`, `cull_cause_id`, `vaccine_id`, `medication_id`, `destination_plant_id`) y en las tres superficies
(alta `201`, `PUT` `200`, corrección `201`), con la fila persistida (`evento.company_id = A` · `suppliers.company_id = B`). La semántica **ya estaba
escrita**: `GA-REM-002` ADDENDUM Wave 3 fijó «global si es nulo, propio de la empresa si está fijado» y acotó su ampliación a las referencias
estructurales; `R-179` extiende esa misma regla a los catálogos → `GA-REM-002` enmienda D. **Sin decisión.** Severidad normalizada **P1** por la clase de
`R-42`/`R-59` (referencia entre empresas persistida en dato productivo). Control positivo obligatorio: el catálogo compartido (`company_id IS NULL`) sigue
aceptándose desde cualquier empresa.
`R-166` (`R166_REVIEW_DECISION_CONCURRENCY_MATRIX.md`): **reproducido por API** — `approve || reject` concurrentes sobre un evento `CORRECTED` devuelven
ambas `200`; el estado queda `APPROVED` pero se registran **dos decisiones efectivas** (`approval_actions` APPROVED + REJECTED), **dos auditorías de éxito**
y **una notificación de rechazo** de un evento aprobado; `approve || approve` deja dos `ApprovalAction` APPROVED. Fila autoritativa: `operational_events`
(`status`); primitiva: el `SELECT … FOR UPDATE` que ya usa el reverso. Contrato de error existente (`400` «no está en estado aprobable») → **sin decisión**
→ `GA-REM-007` enmienda B. Severidad normalizada **P2**.

**Puerta de composición** (prompt §52): `R-179` activo · P1 · gobernado · sin decisión — `R-166` activo · P2 · gobernado · sin decisión — raíces
independientes (referencia de catálogo vs serialización de la decisión) → **modo `R179_PLUS_R166`**, en ese orden.

Registrado (fuera del tranche): `R-180` (P2): `bird_movements.source_house_id` / `target_house_id` admiten galpones de otra empresa; el ADDENDUM Wave 3
cubrió `house_id` **del evento**, no los del submovimiento. Clase **estructural** (regla de `R-59`, sin el caso «nulo = compartido»), distinta de la de
`R-179`: se registra en vez de mezclarse.

| ID | P | Hallazgo | Dónde | Ola |
|---|---|---|---|---|
| `R-180` | P2 | `source_house_id` / `target_house_id` de los movimientos de aves admiten galpones de otra empresa (clase estructural, `R-59`) | `operations/service.py` · `schemas.py:19-20` | B |

```
R-179    OPEN · P1 (normalizado desde P3)   ACTIVE · gobernado · GA-REM-002-D · sin decisión · sin migración
R-166    OPEN · P2 (normalizado desde P3)   ACTIVE · gobernado · GA-REM-007-B · sin decisión · sin migración
R-180    OPEN · P2                          registrado (fuera)
WAVE B   IN PROGRESS        36 ítems (canónico: 35 + R-180) · 21 cerrados · 4 parciales · 11 abiertos (P1 1 · P2 6 · P3 4) · decisiones 10
```

---

## Cierre de `R-179` y `R-166` · WAVE B tranche 13 (2026-09-10)

```
R-179    CERRADO (técnico)   GA-REM-002 enmienda D · P1 · verificar_catalogo_de_empresa: el catálogo compartido (company_id nulo) se acepta desde cualquier
                            empresa y el propio exige igualdad (BR-07, anti-enumeración) · aplicado en alta, PUT y POST /corrections, en las siete familias del
                            evento, en los submovimientos (feed_type_id, hatchery_id) y en los derivados por su padre (incubator_id, hatcher_id) · razas y
                            fases productivas siguen globales · 26/26 · rojo previo 11 · sensibilidad 5 válidas + 1 N/A (no existe superficie donde el cliente
                            aporte la empresa) · sin migración
R-166    CERRADO (técnico)   GA-REM-007 enmienda B · P2 · _bloquear_evento (SELECT … FOR UPDATE sobre operational_events + relectura del estado) antes de validar
                            la transición, en approve, reject, complete_review, start_review y return_to_operator · una sola decisión efectiva por ciclo:
                            un approval_action, una auditoría de éxito, una notificación · el reverso conserva su propio bloqueo (OD-19) · revisar no serializa
                            el saldo del lote (R-166 ≠ R-161) · 8/8 · rojo previo 5 con carrera observada · sensibilidad 6 válidas · sin migración
R-180    OPEN · P2           registrado en el pre-flight (galpones origen/destino de los submovimientos; clase estructural R-59)
WAVE B   IN PROGRESS        36 ítems (canónico) · 23 cerrados · 4 parciales · 9 abiertos (P1 0 · P2 5 · P3 4) · decisiones 10
                            siguiente tranche (identificado, no iniciado): R-180 · alternativa: R-147 / R-148
```

Evidencia: `WAVE_B_TRANCHE_13_MASTER_TENANCY_AND_REVIEW_CONCURRENCY_EVIDENCE.md`. Regresión completa: **1122 passed · 49 skipped · 0 failed** (1046 s; 1088 previas + 34 nuevas; los 49 saltados son `test_upgrade_path`
y `test_runtime_startup`, que exigen su script dedicado). `vitest` 108/108 · `tsc` 6 preexistentes (`R-158`). Sin migración (cabeza `x4y5z6a7b8c9`).
Rutas 211. `R-164` BLOCKED_RUNTIME · fase 9 FROZEN · `BU-D10` PENDING_RATIFICATION · SAP no iniciado.

---

## Pre-flight de `R-180` · WAVE B tranche 14 (2026-09-10)

```
R-180    ACTIVE · GOBERNADO · sin decisión · severidad P2 → P1
         las referencias ESTRUCTURALES de los submovimientos no se comprueban contra la empresa del evento. Cuatro campos, no dos:
           bird_movements.source_house_id     House → Farm → Company     201 · persistido (galpón de otra empresa)
           bird_movements.target_house_id     House → Farm → Company     201 · persistido
           inspection_details.house_id        House → Farm → Company     201 · persistido   ← no declarado en el alta de R-180
           egg_storage.lot_id                 Lot.company_id             201 · persistido   ← no declarado en el alta de R-180
         Superficie escritora única: el ALTA. PUT no declara listas de submovimientos y la corrección deriva sus campos de OperationalEventUpdate,
         luego ninguno puede fijarlos (se versiona como guardián, AC-R180-14). El reverso copia columnas del original: derivada.
         Hijos mixtos (uno válido, uno ajeno): ambos se persisten hoy — no hay atomicidad porque no hay validación.
         Autoridad: ADDENDUM Wave 3 de GA-REM-002 («las referencias estructurales, aquellas cuya pertenencia define de quién es el dato»; su tabla
         nombra house_id) · AC10 · AC12/enmienda A (el sub-recurso hereda la pertenencia de su padre) · clase R-42/R-59 · RQ-03. No falta la regla:
         faltó su alcance sobre los hijos. Sin decisión del propietario. Sin migración: la cadena House → Farm → Company ya existe.
         Unidad de negocio: House y Farm NO la declaran (se deriva del lote), luego OD-10 no se toca y no se inventa restricción entre unidades ni
         entre granjas de la misma empresa (control positivo obligatorio).
         Artefactos: R180_HOUSE_FARM_STRUCTURAL_OWNERSHIP_MATRIX.md · GA-REM-002 enmienda E · AC-R180-01…14
```

Recuento canónico de entrada (recalculado, con la rectificación de `WAVE_B_DEPENDENCY_AND_EXECUTION_MATRIX §30`): **36 · 23 · 4 · 9** ·
P1 0 · **P2 6** · P3 3 · bloqueados por decisión 5 · `BLOCKED_RUNTIME` 1 · decisiones 10.

---

## Cierre de `R-180` · WAVE B tranche 14 (2026-09-10)

```
R-180    CERRADO (técnico)   GA-REM-002 enmienda E · P2 → P1 · verificar_estructurales_del_submovimiento recorre la cadena autoritativa real
                             (House → Farm → Company para el galpón origen, el galpón destino y el galpón de la inspección; Lot.company_id para el lote
                             del almacenamiento) sobre TODOS los hijos y ANTES de cualquier db.add: con un hijo ajeno no se persiste nada, ni el evento
                             ni los hijos válidos. Se apoya en verificar_pertenencia, no en el helper de catálogos: la clase estructural no tiene el caso
                             «nulo = compartido». PUT y POST /corrections no declaran submovimientos y esa imposibilidad queda versionada (AC-R180-14).
                             No se inventa restricción de unidad ni de granja: House y Farm no declaran unidad de negocio y OD-10 queda intacto; el
                             movimiento entre granjas distintas de la misma empresa se prueba como control positivo.
                             11/11 · rojo previo 8 · sensibilidad 8 válidas (2 reconstruidas, crédito 0 a las inválidas) · sin migración
GUARDA   ESTABLECIDA         MUTATION CHECKPOINT ejecutable: scripts/mutation_guard.py (7 señales fail-closed, restauración desde el commit declarado)
                             + tests/test_mutation_guard.py (casos A…E, 6/6) + MUTATION_CHECKPOINT_GOVERNANCE.md. Probada en ejecución real: con un
                             archivo productivo sucio, el driver ABORTÓ antes de instalar ninguna mutación.
WAVE B   IN PROGRESS         36 ítems (canónico) · 24 cerrados · 4 parciales · 8 abiertos (P1 0 · P2 5 · P3 3) · decisiones 10
                             siguiente tranche (identificado, no iniciado): R-147 (constantes sin fuente) · alternativa R-148 (inmutabilidad de audit_logs)
```

Evidencia: `WAVE_B_TRANCHE_14_SUBMOVEMENT_STRUCTURAL_TENANCY_EVIDENCE.md`. Recuento canónico de salida: **36 · 24 · 4 · 8** · P1 0 · P2 5 (`R-142` · `R-144` · `R-147` · `R-148` · `R-164`) · P3 3
(`R-153` · `R-156` · `R-177`) · bloqueados por decisión 5 · `BLOCKED_RUNTIME` 1 · decisiones 10. Sin migración (cabeza `x4y5z6a7b8c9`). Rutas 211.

---

# AUDITORÍA MAESTRA FRONTEND + RUNTIME DESPLEGADO — reconciliación (2026-09-10 · AUDIT ONLY)

Base auditada: `3808ed5` (`main` · limpio · local == remoto; el encargo llegó rotulado `6ffd73c`, se audita
contra la verdad presente del repositorio y se registra el delta). Runtime: `avicola.globaldv.net` (ENV-01).
Artefactos completos en `audit/frontend-runtime/`. **No se implementó, remedió ni modificó código de producto.**
Esta sección **añade** capa de reconciliación: no reescribe ninguna línea anterior.

## `R-99` · causa raíz demostrada (el frontend congelado tiene un mecanismo reproducible)

```
CAUSA RAÍZ   `tsc -b` rojo en `main` desde `4386f87` (2026-09-06) × `frontend/Dockerfile` = `RUN npm run build`
             (`tsc -b && vite build`). Cada build de imagen de frontend falla en CI → no hay imagen nueva →
             Watchtower no recibe nada → el artefacto servido no cambia desde el 2026-09-05 14:09:27 GMT.
EVIDENCIA    ① f46cb13 (commit del artefacto servido): `tsc -b --noEmit` → exit 0 (worktree temporal).
             ② 4386f87 retira las pestañas «por lote / por usuario» de `AuditPage.tsx` y deja `User, Database`
                en el import → 2 × TS6133 (`noUnusedLocals: true`) → `tsc` RED.
             ③ 950bb21 añade 4 diagnósticos más en `LotFormPage.tsx` (areas/setAreas/areaRes, índice de tupla).
             ④ Los 15 commits de frontend posteriores al congelamiento: `tsc -b` RED en 15/15.
             ⑤ Fingerprint re-medido el 2026-09-10: `Last-Modified` 2026-09-05 14:09:27 GMT, `index-D5dwMXuP.js`
                (idéntico al del 2026-09-07) ≠ build local `index-Cl0MIg8E.js`. Hashes en el artefacto de evidencia.
CONSECUENCIA 15 entregas de frontend no visibles (roles, maestros, curvas, notificaciones, áreas, agua, plan de
             abuelas, cuadre B01, B13, catálogo de incubadora, despacho fértil, filtros de auditoría, UX de
             denegación…). Y tres flujos del runtime compartido HOY EN 400 contra el backend nuevo:
               recepción de reproductoras → BR-20 · nacimiento en incubadora → BR-21 · importación de abuelas → BR-22.
ACOTAMIENTO  La causa NO es caché del cliente ni Watchtower ni etiqueta :latest (el backend sí se despliega en cada
             entrega). Tampoco exige tocar EX-01: se corrige en el árbol de código (los 6 errores de R-158).
DISPOSICIÓN  El hallazgo pasa de «BLOCKED_BY_OUT_OF_SCOPE_DEPLOYMENT · no tocar» a **remediable en alcance**:
             eliminar los 6 errores de `R-158` restituye `npm run build`; el pipeline normal vuelve a desplegar.
             Toda la evidencia y el orden propuesto: `audit/frontend-runtime/DEPLOYMENT_FRONTEND_FINGERPRINT.md`
             y `MASTER_FRONTEND_REMEDIATION_ROADMAP.md` (tranche recomendado `GA-FE-01`, NO iniciado).
```

## `R-158` · normalización de impacto (sin cambio de severidad histórico)

Los 6 errores de `tsc` estaban registrados como «P2 preexistente de quality gates». La auditoría demuestra que
**bloquean todo despliegue de frontend** (mecanismo de `R-99`). Se documenta el impacto; la severidad formal se
deja al programa (propuesta: P2 → **P1 operativo** hasta restaurar el build).

## `R-181` · NUEVO · el envío/reenvío explícito a revisión no tiene control en la interfaz

```
ID            R-181 (siguiente libre tras R-180; ratificación del programa pendiente)
SEVERIDAD     P2
TÍTULO        `POST /operations/{id}/submit` (enviar a revisión / reenviar un devuelto o rechazado) no tiene
              ningún control en la interfaz: `operationsService.submit` no tiene llamadores en todo el historial
              del frontend; 0 refs `/submit` en el bundle desplegado; sin claves i18n; los E2E lo suplen por API.
RAÍZ          vertical de UI nunca cableada — clase distinta de `R-98`/`R-119` (no es permisos) y de `R-135`
              (que cerró el backend, `OD-17.b`).
REQUISITO     `docs/12 §2` («Devuelto → Operador reenvía»; «Rechazado → Operador reenvía (corregido)») · `OD-17.b` · `spec §4.10`.
BACKEND       IMPLEMENTED y desplegado — sin trabajo.
FRONTEND      control «Enviar a revisión / Reenviar» (detalle y móvil) + feedback de estado.
DEPENDENCIAS  ninguna (no fase 9, no decisión del propietario) · Ola E — puede viajar con `T-040-23`.
EVIDENCIA     `audit/frontend-runtime/MASTER_FRONTEND_RUNTIME_AUDIT_EVIDENCE.md §34`.
```

## Deduplicación y alcance de esta auditoría

```
R-98 / R-119   vigentes (0 `hasPermission`; menú estático; `ProtectedRoute.roles` muerto) — no se duplican.
R-135          su frontera backend sigue válida; la vertical UI ausente se registra como R-181 (raíz distinta).
R-140          su parte «motivo → vertical de UI» sigue OPEN como estaba; no se toca.
R-124 / AOD-06 · R-153 / AOD-25   clasificaciones OWNER_DECISION_REQUIRED referenciadas, no duplicadas.
GA-REM-040     fase 9: FRONTEND_MISSING en 5 capacidades + reverso; congelada por autorización del propietario.
GA-REM-041/OD-19   pantalla de reverso aplazada a fase 9 (ya declarado por el programa) — referenciado.
CERTIFICACIONES   reconciliación de frontera en `CERTIFICATION_SCOPE_RECONCILIATION.md`; ningún cierre reescrito.
```

## Conteo de la auditoría (invariante verificado por script)

```
Capacidades user-visible ......... 38   ·  clasificadas 23  ·  bloqueadas por auth 15 (AUTHENTICATED_RUNTIME_BLOCKER)
IMPLEMENTED_AND_VISIBLE .......... 0    IMPLEMENTED_BUT_NOT_EXPOSED ... 1
FRONTEND_MISSING ................. 7    DEPLOYMENT_STALE .............. 13
BROKEN_FLOW (primario) ........... 0    OWNER_DECISION_REQUIRED ....... 2
23 = 0 + 1 + 7 + 13 + 2 ✓
Hallazgos nuevos: R-181 (P2). Addenda: R-99 (causa raíz) · R-158 (impacto). Ningún otro ID.
```

## Solicitud al propietario (bloqueo de la fase autenticada)

Cuentas **de prueba autorizadas** del entorno compartido para ejecutar la fase 7 del plan: Super Admin ·
Administrador de Accesos · Supervisor Avícola · Operador de Granja · Contraloría · usuario multiempresa ·
usuario sin unidades (zero-BU); wish: empresas con unidades en estados mixtos y concesiones mixtas.
Sin ellas, 15 capacidades y los journeys J01–J18 quedan `BLOCKED_AUTH` por diseño del encargo (§38: no se adivina).

---

## GA-FE-01 · REMEDIACIÓN DE ENTREGA FRONTEND (2026-09-10) — `R-99` · `R-158` · `R-182`

```
TRANCHE        GA-FE-01 (baseline 42108b0) — restaurar la cadena de entrega del frontend
COMMITS        397cc02 (C1 spec/preflight) · 08d0197 (C2 fix) · C3 (evidencia, mismo push)
DESPLIEGUE     automático por el mecanismo normal (EX-01) — 0 acciones manuales
```

### `R-158` · CERRADO — TECHNICAL BUILD BLOCKER

6 diagnósticos de `tsc` resueltos semánticamente (2 imports muertos de una remoción gobernada
`GA-REM-032 AC11`; 2 símbolos de un scaffold de áreas jamás cableado — ver `R-182`; 1 tuple
inválido). `tsc -b` 6 → **0** · `vite build` 0 · `npm run build` 0 (comando del Dockerfile) ·
Vitest **108/108** · sin relajación de tsconfig/package/Dockerfile (diff 0 líneas) · sin features
retiradas. Evidencia: `audit/ga-fe-01/` (matriz semántica, replay histórico, gates).

### `R-99` · CERRADO — la generación servida ya no es el congelado del 2026-09-05

Runtime: `index-D5dwMXuP.js` → **`index-kzREeQp6.js`** · Last-Modified 09-05 14:09:27 →
**09-10 21:42:54 GMT** · paridad **byte a byte** con el build del commit `08d0197` (JS/CSS/HTML) ·
asset viejo **404** · marcadores M1–M7 presentes (permissions-catalog · masters/areas ·
notifications/unread-count · weight-curves · import_plan · dead_on_arrival · chicks_healthy) ·
smoke público OK · cliente fresco OK. Restricción declarada: la verificación **funcional
autenticada** sigue `BLOCKED_AUTH` (sin credenciales autorizadas) — la paridad de ENTREGA queda
probada al nivel que el encargo permite sin sesión.

### `R-182` · NUEVO (propuesto · P2) — alta de lote: captura de cierre de plan y área

`LotFormPage` captura `planned_close_date` (control + zod) pero el payload (8 claves) no lo envía;
`area_id` declarado en el esquema sin control ni envío;
`backend/app/notifications/sla.py` selecciona lotes por `Lot.planned_close_date.isnot(None)` +
estado activo → la notificación «lote próximo a cierre» no puede dispararse para lotes creados
por UI. No corregido en GA-FE-01 (fuera de objetivos); registro para el programa.

### Sin cambios

`R-98`/`R-119`/`R-181` vigentes · fase 9 FROZEN · Ola B PAUSADA · severidad formal de `R-158` a
cargo del programa (propuesta de normalización ya registrada en el addendum de la auditoría).

---

## GA-FE-02 · FASE 9 AUTORIZADA Y ENTREGADA (2026-09-11) — `OD-20`

```
AUTORIZACIÓN  OD-20 (fase 9: FROZEN → AUTORIZADA, solo GA-FE-02)
COMMITS       466f9d3 (gobernanza) → 48ffdbb (implementación) → C3 (evidencia)
ENTREGA       contexto de empresa efectivo + switch · Company BU admin (cuatro unidades,
              habilitar/apagar, encender ≠ conceder) · User BU grants (candidatos para el
              Administrador de Accesos + panel por usuario; self sin concesión) · navegación
              admin mínima por permiso · RED 58 rojos → 90 verdes · tsc 0 · build 0 ·
              vitest 198/198 · desplegado con paridad byte a byte (asset anterior 404;
              marcadores presentes)
FRONTERA      AUTHENTICATED E2E: BLOCKED_AUTH (cuentas de prueba requeridas, doc emitido)
INTOCADO      R-98/R-119/R-181/R-182 sin cambio · BU-D10 PENDING_RATIFICATION ·
              Wave B PAUSADA · Wave C / SAP no iniciados · backend sin cambios
```

Nuevos hallazgos de esta tranche: **ninguno** (el único defecto detectado —dependencia
inestable que producía bucle de refetch— se corrigió dentro del propio ciclo RED→GREEN antes
del commit de implementación).

---

## GA-FE-06 · R-182 CERRADO (2026-09-11) — contrato de alta de lote + SLA

```
ENTREGA       `LotFormPage`: selector de área por empresa (`/masters/areas`) + payload con
              `planned_close_date` y `area_id` (null explícito si vacío); `LotDetailPage`:
              fila «Fecha prevista de cierre» (día natural, sin ±1); i18n `lots.area` ES/EN.
COMMITS       C1 10f91db (gobernanza+RED) → C2 23ca59a (implementación) → C4 (evidencia)
GENERACIÓN    index-DcqmSs-R.js (entrada index-WUv1-F9o.js)
RED→GREEN     vitest 4 rojos + 1 control → 5/5 verdes · runtime pre-fix (lote 17: payload de
              8 claves, fresh null) · suite 278/278 · tsc 0 · build PASS · PG-libre 7/7
RUNTIME       E2E-01…16 autenticados (desktop 1440×900 · móvil 390×844 · ES/EN · RBAC 403 ·
              CBU 403 rol/ventana · auditoría verificada · red sin tormenta)
SLA           fuente reparada; regla 0..3 intacta (suite CI); aviso por escáner horario
              (relectura documentada — ver certificación)
CAMBIO        backend 0 · migración 0 · permisos 0 · expansión 0
```

### Nuevos candidatos registrados (con evidencia viva; NO corregidos — fuera de alcance)

- **`R-183` (P2 propuesto, ex N-1)**: `POST/PUT /lots` acepta `area_id` de **otra empresa**
  (probado: 201 y persistido, lote 18 `GA6-XT-CHECK-1`; `farm_id` sí tiene guarda). La UI
  filtra y el inquilino no se cruza en lectura. Recomendación: guarda simétrica + test CI.
- **`R-184` (P2 propuesto, ex N-2)**: `GET /reports/kpi/ipe/{lot}` → **500** con lote recién
  creado (`date.today() − lot.start_date` sobre datetime aware). Reproducido vivo (lote 19).
- Observaciones: N-3 (detalle de lote llama KPIs sin permiso → 403 de consola; P3) ·
  N-4 (`new_values` de auditoría de alta no incluye `planned_close_date`/`area_id`; P3).

INTOCADO: `R-98`/`R-119`/`R-181` CLOSED sin regresión · BU-D10 PENDING_RATIFICATION ·
Wave B PAUSADA · Wave C / SAP no iniciados · GA-FE-06 = FUNCTIONALLY_CERTIFIED /
OWNER_ACCEPTANCE_PENDING (paquete UAT emitido).

---

## GA-FE-06-A · R-182 SEGURIDAD DE ÁREA — RE-CERRADO (2026-09-11)

```
ORDEN         Remediación directa del defecto de propiedad de área entre empresas
              (subhallazgo N-1/R-183), requerida para cerrar R-182.
CORRECCIÓN    Estado previo corregido: R-182 SECURITY_REMEDIATION_REQUIRED ·
              GA-FE-06 PARTIAL · OWNER_UAT_READY NO (addendum, sin reescribir historia).
COMMITS       C5 b48e4ea (gobernanza+RED) → C6 69d0c95 (backend) → C7 (evidencia)
GENERACIÓN    backend 69d0c95 (despliegue observado 500→502→400) · bundle sin cambio
              index-DcqmSs-R.js
CAMBIO        backend/app/lots/service.py (+24): alta y edición validan pertenencia
              del área con `verificar_catalogo_de_empresa` (R-179; BR-07; fail-closed)
RUNTIME       ajena alta 201→400 · ajena edición 200→400 · inexistente 500→400 ·
              positiva/NULL ALLOW · sin persistencia · sin auditoría de éxito ·
              sin fuga (400 idéntico para inexistente y ajena)
GATES         PG-libre 7/7 · vitest 278/278 · tsc 0 · build PASS · suite nueva
              `tests/test_lot_area_ownership.py` (PG/CI)
HIGIENE       revokes + BU 4×OFF + usuarios 120-122 baja + roles 54/55 off +
              áreas 4/5 baja + credenciales destruidas
```

### Disposición de hallazgos

- **`R-183` → ABSORBED_IN_R182** (clasificación A): misma clase ya gobernada por
  `GA-REM-002`/`R-42`/`R-139`/`R-179`; el sitio `lots.area_id` era el hueco. **No se crea
  entrada independiente** (sin deuda duplicada). Evidencia: `audit/ga-fe-06-a/`.
- **`R-184` → SEPARATE / UNCHANGED** (no bloquea R-182; no implementado aquí).
- N-3/N-4: sin cambio.

**`R-182 = CLOSED` · `GA-FE-06 = FUNCTIONALLY_CERTIFIED / OWNER_ACCEPTANCE_PENDING` ·
`OWNER_UAT_READY = YES`.** R-98/R-119/R-181 CLOSED · BU-D10 PENDING_RATIFICATION ·
Wave B PAUSADA · Wave C/SAP no iniciados. Owner UAT **no ejecutado** en esta tranche.

---

## GA-UAT-04 · ACEPTACIÓN DEL PROPIETARIO — GA-FE-06 ACEPTADO (2026-09-11)

```
DECISIÓN      «A) ACEPTO GA-FE-06» (explícita; sin observaciones adicionales)
EFECTOS       GA-FE-06 = FUNCTIONALLY_CERTIFIED · OWNER_ACCEPTED · OWNER_ACCEPTANCE = PASS
              R-182 = CLOSED · OWNER_ACCEPTED (técnicamente cerrado en GA-FE-06-A)
REGISTRO      audit/ga-uat-04/GA_OWNER_ACCEPTANCE_GA_FE_06_RECORD.md
              + guía, observaciones, evidencia de referencia, capturas C01-C10, ledger
LIMPIEZA      BU 4×OFF restaurada · concesión revocada · usuario/rol UAT desactivados ·
              áreas 1/2 devueltas a baja lógica · credenciales destruidas · auditoría preservada
INTOCADO      R-184 SEPARATE_UNCHANGED · BU-D10 PENDING_RATIFICATION · Wave B PAUSED ·
              Wave C / SAP NOT STARTED · GA-FE-02/03/04/05 OWNER_ACCEPTED (registros intactos)
```

### Candidato nuevo registrado (a decisión del programa; NO corregido)

- **Descubrimiento del módulo «Lotes» (UX · P2 propuesto, sin R asignado)**: la
  configuración de navegación no contiene ninguna entrada «Lotes» y ninguna pantalla
  enlaza a `/lots`; el módulo solo es alcanzable por URL directa. Detectado durante la
  preparación de GA-UAT-04 (UAT-01) y **informado y aceptado** por el propietario como
  observación no bloqueante. Clase: navegación/descubrimiento (GA-FE-03), pre-existente;
  no es regresión de GA-FE-06 ni de la remediación de seguridad.
- Notas menores aceptadas: el detalle del lote no muestra el Área (decisión de diseño
  GA-FE-06-C15) · el selector incluye áreas propias de baja lógica (P3; sin regla de
  «activa» inventada).

---

## GA-GOV-01 · TRIAGE POST-UAT-04 (2026-09-11) — SOLO GOBERNANZA

```
ENTRADA      baseline cfdbdee · producto sin cambios · análisis sin implementación
MATRIZ       audit/ga-gov-01/GA_GOV_01_POST_UAT04_TRIAGE_MATRIX.md
DEDUP        audit/ga-gov-01/GA_GOV_01_DEDUP_REPORT.md
DECISIONES   audit/ga-gov-01/GA_GOV_01_CLASSIFICATION_DECISIONS.md
INFORME      audit/ga-gov-01/GA_GOV_01_FINAL_GOVERNANCE_REPORT.md
```

### Disposiciones finales (una por observación; sin R nuevos — regla §23 aplicada)

- **OBS-UAT-01 «Lotes sin entrada de menú» → UX_ENHANCEMENT_ONLY · P2 · sin R.**
  No es defecto: GA-FE-03 inventarió `/lots*` entre las «rutas sin fuente de menú»
  con decisión expresa «sin entradas nuevas salvo Roles» (aceptado en GA-UAT-01).
  No reabre R-119/GA-FE-03/GA-FE-06. Hogar: mejora de navegación P2 (candidata a la
  próxima iteración de navegación junto al filtro de estado).
- **OBS-UAT-04 «área en baja lógica seleccionable» → OWNER_DECISION_REQUIRED · P3 · sin R.**
  Silencio canónico verificado (R-179 solo tenencia; CRUD sin filtro de estado;
  GA-FE-06-A §29 no inventó regla de «activa»). Pregunta A/B/C: A estatus actual ·
  **B (default neutro): filtro de selección en UI sin tocar backend ni histórico** ·
  C regla de dominio completa (backend rechaza referencias nuevas a inactivos).
- **OBS-UAT-06 «área ausente del detalle» → ACCEPTED_DESIGN** (GA-FE-06-C15; ninguna
  spec la exige; el API la expone).
- **UAT-11 «SLA visible» → NOT_A_DEFECT (N/A_BY_DESIGN)** — el aviso es notificación
  interna evaluada por tarea horaria; sin superficie a demanda en ninguna fuente.
- **R-184 → SEPARATE_OPEN sin relación** con las observaciones; no se toca.

INTOCADO: GA-FE-02..06 OWNER_ACCEPTED · R-98/R-119/R-181/R-182 (sin reapertura) ·
BU-D10 PENDING · Wave B PAUSED · Wave C/SAP NOT STARTED · implementación NINGUNA.

---

## GA-FE-07 · R-185 CLOSED_OWNER_ACCEPTED — ELEGIBILIDAD DE REFERENCIAS POR ESTADO (2026-09-11) — `OD-21`

```
DECISIÓN      OD-21 («Option C — Domain Rule Complete», elección explícita del propietario):
              UN RECURSO DADO DE BAJA LÓGICA NO PUEDE USARSE PARA NUEVAS REFERENCIAS.
              La desactivación lógica no borra ni invalida la historia. Implementación
              limitada a Área→Lote (principio general documentado, sin remediación masiva).
FINDING       R-185 (P2, integridad funcional de dominio) — dedup contra R-171/R-179/R-182/
              R-98/R-119: sin dueño previo → creado; técnico CERRADO; ACEPTADO por el propietario (GA-UAT-05, decisión A, 2026-09-11).
ENTREGA       Alta y edición de lote exigen área ACTIVA para referencias nuevas
              (`verificar_catalogo_de_empresa` extendido con `exigir_activo`, default intacto);
              detección de cambio real en edición (H1–H5: omitir/mismo-id/null ⇒ sin regla
              nueva; cambiar ⇒ referencia nueva); selector de lote solo áreas activas;
              administración de maestros INTACTA. 0 migración · 0 permisos · 0 endpoints.
SEMÁNTICA     Inactiva propia ⇒ 400 «Área inactiva»/BR-07 · Ajena/inexistente ⇒ 400
              «Área no encontrado» (anti-enumeración intacta).
COMMITS       C1 511c419 (gobernanza+RED) → C2 5a5bb3f (implementación) → C4 (evidencia)
GENERACIÓN    frontend index-BUthrUt9.js (LM 15:46:08 GMT) · backend 5a5bb3f
GATES         Vitest 280/280 (+2) · tsc 0 · build PASS · PG-libre 7/7 · suites lotes/área/
              elegibilidad en CI (skip local declarado)
RUNTIME       E2E-01…12 PASS (alta/edición DENY sin persistencia ni auditoría de éxito;
              H1/H2/H4 ALLOW; H3/H5 DENY; ajena DENY; NULL intacto; carrera de baja DENY;
              masters admin conserva inactivas; BU/RBAC 403; móvil/consola conformes)
HIGIENE       actores/roles retirados · concesión revocada · BU 4×OFF · áreas a baja ·
              credenciales destruidas · auditoría preservada · humanos intactos
INTOCADO      R-182 CLOSED_OWNER_ACCEPTED · R-184 SEPARATE_OPEN · OBS-UAT-01 UX P2 ·
              BU-D10 PENDING · Wave B PAUSED · Wave C/SAP NOT STARTED
```

### Disposición heredada

- **GA-GOV-01 §OBS-UAT-04** (`OWNER_DECISION_REQUIRED`): **RESUELTA** por OD-21 e implementada aquí.
- Owner UAT corta de GA-FE-07: **EJECUTADA** (GA-UAT-05, 2026-09-11) → **A) ACEPTO GA-FE-07** (registro: `audit/ga-uat-05/GA_OWNER_ACCEPTANCE_GA_FE_07_RECORD.md`).
- Estado final: R-185 = `CLOSED_OWNER_ACCEPTED` · OD-21 = `RATIFIED_IMPLEMENTED_OWNER_ACCEPTED`. Sin tranches nuevas iniciadas.

## R-184 · CLOSED_OWNER_ACCEPTED — KPI/IPE: SEMÁNTICA TEMPORAL + HTTP 500 (2026-09-11)

```
FINDING       R-184 (P2, era «N-2 candidato» de GA-FE-06) — CLOSED (técnico)
SÍNTOMA       GET /reports/kpi/ipe/{lot} → 500 en todo lote con start_date
CAUSA RAÍZ    get_kpi_ipe: date.today() − lot.start_date (date − datetime aware,
              columna DateTime(timezone=True)) ⇒ TypeError  (probado, no supuesto)
FIX           age_days normalizado con _dia() (R-75 / GA-REM-028) — C2 3f88f94
              (1 archivo, +6/−1; fórmula, redondeo y contrato INTACTOS; backend-only)
EVIDENCIA     runtime E2E-01…12 = 14/14 (valores independientes exactos: 556.6 y 37894.7)
              · UI tarjeta IPE visible desktop/móvil · seguridad 404/403/OD-16 PASS
GATES         Vitest 280/280 · tsc PASS · build PASS · backend canónico 7 passed ·
              suite nueva PG/CI (skip local declarado)
REGISTROS     R-186 (candidato): /reports/kpis/production-index → 500 misma clase
              (SEPARATE_OPEN, no implementado por regla de alcance)
              OBS negocio: posible ×100 de escala vs bandas «reference»
              (OWNER_DECISION_REQUIRED futuro; no bloquea)
UAT           GA-UAT-06 (2026-09-11): decisión A) ACEPTO R-184 (6/6 casos, sin
              observaciones) → R-184 = CLOSED_OWNER_ACCEPTED
INTOCADO      R-181/R-182/R-185/OD-21 sin cambio · OBS-UAT-01 UX P2 · BU-D10 PENDING ·
              Wave B PAUSED · Wave C/SAP NOT STARTED
```

## GA-GOV-02 · R-186 FORMALIZADO (P2 · OPEN) + DECISIÓN DE PROPIETARIO PENDIENTE — ESCALA DEL IPE (2026-09-11)

```
GOBERNANZA    GA-GOV-02 (solo análisis y clasificación; cero producto) — audit/ga-gov-02/
R-186         FORMAL_OPEN_FINDING (ex «candidato»): GET /reports/kpis/production-index
              (G-05) → 500 en todo lote con start_date (date − datetime; expresión
              hermana de R-184, línea propia NO tocada por el fix 3f88f94).
              Evidencia: audit/ga-r184/evidence/red/runtime-red.json (prodindex35 = 500).
              Dedup: DISTINCT_NEW_FINDING (R-184 = otro endpoint/AC/línea; R-147 vecino de
              meta-clase; sin dueño previo). ID legítimo: siguiente libre tras R-185.
              Severidad P2 (defecto funcional real; API-only sin consumidor frontend).
              Owner Decision: NO. Implementación: SÍ — EJECUTADA en la tranche R-186 (ver bloque siguiente).
OBSERVACIÓN   Escala del IPE vs bandas «reference» (factor ~100; viabilidad % vs fracción;
              FCR simplificado documentado en contrato): OWNER_DECISION_REQUIRED — 1 decisión
              (opciones A/B/C; recomendada A) en audit/ga-gov-02/GA_GOV_02_OWNER_DECISION_PACKET.md.
              Sin finding hasta la decisión (secuencia OBS→OD→SPEC→…). Implementación: NO.
PRIORIDAD     P1 tranche técnica R-186 · P2 sesión de decisión del propietario · P3 OBS-UAT-01 ·
              BU-D10 espera ratificación · Wave B PAUSED
INTOCADO      R-184/GA-UAT-06 sin reapertura · GA-FE-02..07 y R-181/182/185/OD-21 PRESERVED ·
              OBS-UAT-01 UX P2 · Wave C/SAP NOT STARTED
```

## R-186 · CLOSED — G-05 PRODUCTION INDEX: SEMÁNTICA TEMPORAL + HTTP 500 (2026-09-11)

```
FINDING       R-186 (P2, ex «candidato» de GA-GOV-02) — CLOSED (técnico)
SÍNTOMA       GET /reports/kpis/production-index → 500 en todo lote con start_date
CAUSA RAÍZ    get_kpi_production_index: date.today() − lot.start_date (date − datetime
              aware) ⇒ TypeError  (probado, no supuesto)
FIX           age_days normalizado con _dia() (R-75/GA-REM-028; mismo helper canónico
              de R-184) — C2 0309225 (1 archivo, +4/−1; fórmula, guarda, or-1,
              fallbacks y redondeos INTACTOS; G-06 sin tocar; backend-only)
EVIDENCIA     runtime E2E-01…13 + R-184 = 14/14 (determinista independiente exacto:
              5.1; mismo día 0; incompleto controlado; security 404/403/OD-16) ·
              suite PG nueva (11 casos; skip local declarado)
GATES         Vitest 280/280 · tsc/build PASS · backend canónico 7 passed
OWNER UAT     NOT REQUIRED (API_ONLY verificado; sin superficie de usuario cambiada)
REGISTRO      audit/ga-r186/ · commits C1 d9fa109 · C2 0309225 · C4 (evidencia)
INTOCADO      R-184/G-06 (556.6 intacto) · observación de escala IPE
              OWNER_DECISION_REQUIRED · OBS-UAT-01 UX P2 · BU-D10 PENDING ·
              Wave B PAUSED · Wave C/SAP NOT STARTED
```

## GA-OD-01 · OD-22 RATIFICADA (A) + R-187 FORMALIZADO (P2 · OPEN) — ESCALA DEL IPE (2026-09-11)

```
GOBERNANZA    GA-OD-01 (solo análisis y sesión de decisión; cero producto) — audit/ga-od-01/
              C1 3cf7baf (paquete de decisión: traza fórmula/bandas/unidades · evidencia ·
              impacto · trazabilidad · paquete) → informe §31 → decisión del propietario.
OD-22         RATIFICADA — Opción A («alinear el valor del IPE a la escala estándar/de las
              bandas»): viabilidad en % (0-100); IPE en escala EPEF (retirar el ×100
              duplicado); bandas >300/250-300/≤250 SIN cambios; sin migración (KPI en vivo).
              Línea GA/OD (NO confundir con Wave B «AOD-22»). Registro:
              audit/ga-od-01/GA_OD_IPE_SCALE_OWNER_DECISION.md · 2026-09-11.
OBSERVACIÓN   Escala IPE vs bandas (GA-GOV-02): RESUELTA por OD-22 (RESOLVED_OWNER_DECISION_A).
R-187         FORMAL_OPEN_FINDING (P2 · OPEN) — brecha implementación vs regla OD-22:
              get_kpi_ipe mantiene el ×100 (CONFIRMED_100X_SCALE_CONFLICT); números ~100×
              bandas ⇒ clasificación poco informativa. Dedup: DISTINCT (R-184/R-186 = 500
              temporal, cerrados; R-131 vecino de meta-clase FCR; sin dueño previo).
              Implementación: NO (tranche futura: spec → AC → implementación → UAT propia
              por cambio visible). Evidencia: audit/ga-od-01/GA_OD_IPE_SCALE_IMPLEMENTATION_GAP_R187.md.
PRIORIDAD     Cola técnica post-decisión: R-187 (P2) junto a OBS-UAT-01 (P2) · BU-D10 PENDING ·
              Wave B PAUSED · Wave C/SAP NOT STARTED
INTOCADO      R-184/R-186 sin reapertura ni reutilización · GA-FE-02..07 y R-181/182/185/OD-21
              PRESERVED · certificaciones intactas
```

## R-187 · CLOSED — IPE G-06: ESCALA ESTÁNDAR OD-22 (SIN ×100) (2026-09-11)

```
FINDING       R-187 (P2, ex GA-OD-01) — CLOSED (técnico) · FUNCTIONALLY_CERTIFIED
DECISIÓN      OD-22 (Opción A del propietario) — RATIFIED_IMPLEMENTED
CAMBIO        get_kpi_ipe: ipe = (viabilidad × ganancia_diaria) / (fcr × 10)
              (retirado el ×100 duplicado — la viabilidad ya llega en %). Docstrings alineados.
              Nada más: bandas/labels/umbrales/fechas/FCR/esquema intactos. Backend-only.
EVIDENCIA     runtime E2E-01…14 PASS: DET 333.3 (independiente, exacto) · LOW 241.1 🔴 ·
              MID 282.7 🟡 · fronteras 249.9/250.0/300.0 exactas · lote 11: 5.6 (pre 556.6;
              ratio 99.99) · lote 53: 378.9 (pre 37894.7) · UI detalle/reporte/refresh/
              relogin/móvil 333.3 · seguridad 404/403/BU-OFF/OD-16 PASS · G-05 5.1 intacto ·
              GA-FE-07 spot 400 «Área inactiva»
GATES         tsc/build PASS · Vitest 280/280 · canónico backend 7 passed · suites PG
              (r184/r186/r187) skip local declarado (corren en CI)
REGISTRO      audit/ga-r187/ · commits C1 5a32a6c · C2 f755baa · C4 (evidencia)
OWNER UAT     REQUIRED / READY — acceptance PENDING (guía GA_R187_OWNER_UAT.md)
INTOCADO      R-184 técnico PRESERVADO (556.6 SUPERSEDED, no objetivo de regresión) ·
              R-186 G-05 PRESERVED · GA-FE-02..07/OD-21/R-185 PRESERVED · OBS-UAT-01 P2 ·
              BU-D10 PENDING · Wave B PAUSED · Wave C/SAP NOT STARTED
              Fixtures retenidos: lotes 54-59 (L-R187-*) documentados en el ledger
```

## GA-UAT-07 · R-187 CLOSED_OWNER_ACCEPTED — UAT DEL PROPIETARIO (OD-22) (2026-09-11)

```
DECISIÓN      A) «ACEPTO R-187» (respuesta explícita del propietario; sin observaciones)
UAT           6/6 casos PASS con walkthrough de referencia (333.3 🟢; detalle=reporte;
              refresh/relogin estables; móvil 390×844 overflow 0; 0 errores fatales)
REGISTRO      audit/ga-uat-07/ (guía, observaciones, evidencia, índice C01-C07, ledger)
              C1 paquete d1f9829 · C2 decisión/limpieza (aceptación)
ESTADOS       R-187 = CLOSED_OWNER_ACCEPTED · OWNER_ACCEPTANCE PASS ·
              OD-22 = RATIFIED_IMPLEMENTED_OWNER_ACCEPTED
LIMPIEZA      concesión 141 revocada · operador 141 baja lógica · rol 71 desactivado ·
              BU broiler OFF restaurada (4×OFF) · credenciales/temporales destruidos ·
              ningún humano modificado
INTOCADO      R-184/R-186 sin cambios · OBS-UAT-01 UX P2 · BU-D10 PENDING ·
              Wave B PAUSED · Wave C/SAP NOT STARTED · sin tranche nueva iniciada
```

## GA-BU-D10 · PAQUETE DE DECISIÓN DEL PROPIETARIO — CICLO APAGAR/ENCENDER LÍNEA (2026-09-11)

```
GOBERNANZA    Tranche GA-BU-D10 (solo análisis y sesión de decisión; cero producto) —
              audit/ga-bu-d10/ (9 artefactos: fuentes, modelo, acceso efectivo, toggle,
              grant/revoke, dedup, impacto, paquete, trazabilidad).
PREGUNTA      ¿Al re-encender una unidad de empresa, las concesiones previas vuelven a ser
              efectivas solas (A) o cada usuario requiere concesión nueva explícita (B)?
              (misma empresa · mismo usuario · misma unidad · sin transferencia)
ESTADO HOY    Provisional = A (AC-A06; «al rehabilitar, la concesión previa vuelve a ser
              efectiva»), documentado como provisional desde GA-REM-040 §6.3; B NO elegida,
              NO descartada; ningún código depende de la elección (matriz §7).
DEDUP         GENUINE_OWNER_DECISION_UNRESOLVED (no resuelta por OD-09/10/14/15/16 ni
              R-98/113/121/128/163/185/187; OD-16.e la reservó a propósito).
RECOMENDACIÓN B (coherencia con OD-09.e «volver no prueba el mismo cargo»; enablement ≠
              grant; auditoría explícita; mínimo privilegio). A = conducta actual, coste 0.
C1            Paquete de decisión commiteado y pusheado ANTES de la decisión.
SIGUIENTE     Decisión explícita A/B → OD (ID a inspeccionar al formalizar) → brecha →
              SPEC/AC/RED si B (auto-reactivación actual = defecto a corregir) / reconciliación
              sin código si A → runtime → certificación → UAT si aplica.
POBLACIÓN     Empresa 1 (entorno de prueba): 91 usuarios, 2 con concesión viva (broiler);
              4×OFF hoy ⇒ ninguna efectiva. Sin PII.
INTOCADO      OD-16, GA-FE-02..07, R-184/185/186/187, OD-21/22 · OBS-UAT-01 P2 ·
              Wave B PAUSED · Wave C/SAP NOT STARTED
```

## R-188 · CLOSED — BU-D10 RESUELTA (OD-23 = B): APAGAR TERMINA · RE-ENCENDER NO DEVUELVE (2026-09-11)

```
DECISIÓN      OD-23 (propietario, respuesta explícita «B») — RATIFIED_IMPLEMENTED
              apagar una unidad de empresa TERMINA las concesiones vivas del ciclo (marca
              revoked_at + auditoría individual con causa; nunca borra); re-encender NO
              devuelve — cada usuario requiere concesión nueva explícita; sin migración.
FINDING       R-188 → CLOSED (técnico) · FUNCTIONALLY_CERTIFIED · OWNER UAT REQUIRED /
              READY — acceptance PENDING (no auto-aprobada)
IMPLEMENTACIÓN admin.fijar_habilitacion (marca+audita al apagar; enable intacto) +
              docstrings servicio/router/modelo; pruebas provisionales A reexpresadas a B
              (+ suite RED r188 x10 PG/CI). Cero migraciones; resolutor/proyecciones intactos.
EVIDENCIA     runtime E2E-01…14 PASS (OFF⇒DENY; re-enable⇒404 B; regrant⇒200; sesión activa
              sin privilegio obsoleto; global+OFF 404; RBAC 403; self 403; cross 404;
              conceder-con-OFF 409; auditoría 23 eventos / 9 terminaciones con causa;
              persistencia 6+1 filas) · UI U1-U6 (nav 1/0/0/1; móvil overflow 0; unit-access
              control-plane) · 0×500 · Vitest 280/280 · gate canónico 7 passed · suites PG
              en CI (skip local declarado; baseline idéntico pre/post en local)
REGISTRO      audit/ga-bu-d10/ (17 artefactos + evidence) · C1 067fba6 · C2 0542310 ·
              C3 bee33f5 · C3b 399751c · C4 (este cierre)
LIMPIEZA      4×OFF restaurada · actores baja lógica · roles BU188* desactivados (incl.
              duplicados de re-ejecución, documentados) · credenciales destruidas
INTOCADO      OD-16/OD-09.e/GA-FE-02..07/R-181..187/OD-21/22 PRESERVED · OBS-UAT-01 P2 ·
              Wave B PAUSED · Wave C/SAP NOT STARTED
```

---

## GA-UAT-08 · ACEPTACIÓN DEL PROPIETARIO — R-188 / BU-D10 / OD-23 ACEPTADOS (2026-09-11)

```
DECISIÓN      «A) ACEPTO R-188 / BU-D10 / OD-23» (explícita; sin observaciones)
EFECTOS       R-188 = CLOSED_OWNER_ACCEPTED · BU-D10 = RESOLVED_OWNER_ACCEPTED ·
              OD-23 = RATIFIED_IMPLEMENTED_OWNER_ACCEPTED · OWNER_ACCEPTANCE = PASS
REGISTRO      audit/ga-uat-08/GA_OWNER_ACCEPTANCE_R188_BU_D10_RECORD.md
              + guía (5 casos), observaciones (ninguna), evidencia C01-C08, índice, ledger
UAT           5/5 PASS: acceso válido; apagar quita; re-encender NO devuelve;
              concesión nueva restaura (regrant por UI real); móvil usable
LIMPIEZA      concesión revocada · usuarios 146/147 baja lógica · roles 92/93 off ·
              BU Engorde OFF (catálogo 4×OFF) · credenciales/temporales destruidos
INTOCADO      OD-16/OD-09.e · GA-FE-02..07 · R-181..187/OD-21/22 PRESERVED ·
              OBS-UAT-01 P2 · Wave B PAUSED · Wave C/SAP NOT STARTED · ningún humano tocado
```

### Cierre de ciclo BU-D10

- **BU-D10 → RESOLVED_OWNER_ACCEPTED**: la pregunta «¿re-encender una unidad devuelve el
  acceso solo (A) o exige concesión nueva (B)?» quedó resuelta por **OD-23 = B**, implementada
  (**R-188**, C3 `bee33f5` + C3b `399751c`) y **aceptada por el propietario** (decisión A).
- Nota N-1 (informativa): el home de roles operativos sin `dashboard:read` muestra «Permiso
  requerido» — fallo cerrado pre-existente, ajeno a R-188; sin acción en este ciclo.

---

## GA-FE-08 · OBS-UAT-01 RESUELTA — DESCUBRIBILIDAD DE «LOTES» (2026-09-11)

```
OBSERVACIÓN   OBS-UAT-01 (GA-UAT-04): «Lotes» sin entrada de menú (solo URL directa)
CLASE         MISSING_NAV_CONFIGURATION (no FRAMEWORK_DEFECT; no ALREADY_RESOLVED)
DECISIÓN      Propietario autorizó GA-FE-08 «solo si la observación sigue presente»
              → presente (pre-fix P01-P03) → cambio mínimo de CONFIGURACIÓN de navegación
CAMBIOS       frontend-only (2 archivos): entrada `lots` primera hija de Gestión Avícola
              (hub /menu/poultry) — reusa ruta /lots, permiso lots:read, clave nav.lots,
              icono Layers; expectativa heredada gaFe02 actualizada (anotada)
NO-CAMBIOS    backend 0 · migración 0 · rutas 0 · permisos 0 · motor de navegación intacto
NO-REABRE     GA-FE-03 · R-119 · GA-FE-04 · R-98 · sin R nuevo (OBS-UAT-01 poseía el trabajo)
GATES          RED 7 failed/5 passed → 292/292 vitest (38 archivos) · tsc/build ✓ ·
              backend diff 0 (suites PG en CI, skip local declarado)
RUNTIME       index-DtzHNDMG.js · E2E-01…10 PASS (C01-C09): autorizado descubre y llega
              (desktop/móvil); BU OFF oculta (global incluido); sin concesión oculta;
              OD-23 histórico no revive; regrant por UI restaura; sin RBAC oculta;
              zero-BU/control sin Lotes; tenant 404 spot; overflow 0; ES/EN por reuso
LIMPIEZA      4×OFF restaurada · usuarios 148-153 baja lógica · roles 94-97 off ·
              credenciales/temporales destruidos · login post-baja 403
REGISTRO      audit/ga-fe-08/ (16 artefactos + evidence) · C1 4ba33f6 · C2 a946cec · C3 cierre
ESTADO        OBS-UAT-01 = RESOLVED_OWNER_ACCEPTED · GA-FE-08 =
              FUNCTIONALLY_CERTIFIED_OWNER_ACCEPTED · OWNER_ACCEPTANCE = PASS
              (decisión A «ACEPTO GA-FE-08 / OBS-UAT-01», 2026-09-11; registro
              GA_OWNER_ACCEPTANCE_FE08_RECORD.md; C4 este cierre)
INTOCADO      OD-16/OD-09.e · GA-FE-02..07 · R-181..188/OD-21/22/23 · BU-D10 · Wave B PAUSED ·
              Wave C/SAP NOT STARTED
```

---

## FINAL FRONTEND AUDIT RECONCILIATION — CIERRE DEL INVENTARIO ORIGINAL (2026-09-11)

```
ALCANCE       Auditoría/reconciliación SOLO (sin producto): 38 user-visible + 7 internas + 15 auth-bloqueadas
HISTÓRICO     23 clasificadas (0·1·7·13·2) + 15 bloqueadas = 38 ✓ · 7 internas · «45» = 38+7
RECONCILIADO  38/38 visibles · 7/7 internas · 15/15 auth-bloqueadas (0 desconocidas)
CLASES        F_C_OA 14 · VNC 19 · ODR 2 (AOD-06 · AOD-25) · OOS 2 (ADM-05 · OPS-09) · BE 1 (OPS-13/P-08)
CERO          missing aplicable · stale · broken · auth-blocked · unknown · P0 · aceptaciones pendientes
RESIDUALES    RES-01/AOD-06 P1 · RES-02/ADM-05 P2 · RES-05/R-52 P2 · RES-06/R-112 P2 · RES-08/R-148 P2 ·
              RES-03/AOD-25 P3 · RES-04/OPS-09 P3 · RES-09/AOD-24 P3 · RES-07 hygiene P3 · RES-10 notas P3
VEREDICTO     RECONCILED_WITH_RESIDUALS · FRONTEND_READY_FOR_WAVE_B_RECONCILIATION = YES
GATES         Vitest 292/292 · build ✓ · E2E S01-S21 PASS · 0 fatales · 0 overflow · backend focal declarado
REGISTRO      audit/final-frontend-audit/ (15 artefactos + evidence 26 archivos) · commit de este paquete
INTOCADO      Todo el programa (sin código, sin tranche, sin Wave B/C/SAP)
```

---

## FINAL FRONTEND RESIDUAL CLOSURE — PAQUETE PRE-DECISIÓN (2026-09-11) — SOLO GOBERNANZA

```
CORRECCIÓN    FRONTEND_READY_FOR_WAVE_B_RECONCILIATION: YES → NO/PENDING (gobernanza; contradicción
              reconocida: decisión AOD-06 pendiente + 19 sin certificación + RES-01 P1)
19 VNC        CERT-PATH A 0 · B 11 · C 8 · D 0 · E 0 · F 0 · G 0
              Plan por batches: S · CP · M · Q · E · R (→ F_C_UAT_NOT_REQUIRED) + OPS-GRANJA/INC/GP (→ UAT-1)
DECISIONES    AOD-06 → RESUELTO como OD-24 (decisión A; 2026-09-11; sin producto hoy) ·
              AOD-25 packet (P3; A/B/C) — PENDIENTE · AOD-24 nota de alcance (Wave B, no bloquea)
RES           RES-02 (diseño fase-9) · RES-05/R-52 (ops, no bloquea) · RES-06/R-112 (SAP externo) ·
              RES-07 = las 19 (no ruido) · RES-08/R-148 (interno Wave B) · RES-10 notas P3 — todos reconciliados
REGISTRO      audit/final-frontend-audit/GA_FRONTEND_RESIDUAL_19_CERTIFICATION_MATRIX.md (+9 documentos)
INTOCADO      Producto 0 · Wave B PAUSED · Wave C/SAP NOT STARTED · sin findings nuevos · sin decisiones inferidas
```
