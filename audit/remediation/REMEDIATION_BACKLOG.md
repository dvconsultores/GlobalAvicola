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
| **17** | `GA-REM-021` | Consumo de agua (R-13) | P1 | 001 | S | bajo | `SPEC_READY` |
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
| `R-13` | Consumo de agua no capturado en 3 etapas | P1 | `GA-REM-021` · `GA-REQ-057` | Wave 2 |
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
| `R-76` | `docs/12 R7` sin implementar: un lote se cierra con registros sin aprobar | P1 — **abierto** |
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

`R-65` y `R-70` son el mismo patrón —entrada no validada que termina en 500— y conviene
tratarlos juntos.

## Frente de mayor palanca pendiente

`GA-TD-014` bloquea **tres** procesos (`P-01`, `P-03`, `P-06`): la OC de SAP se guarda en
`extra_data.sap_order_ref` en vez de `sap_document_ref`, de modo que `validate_oc_limit` sale
por su primera línea y `BR-11` y `BR-18` nunca se aplican.

No es un problema técnico pendiente sino una **decisión de negocio abierta**: activarlo
cambia el comportamiento para los operadores y `C-15` lo dejó diferido a la espera de
`RC-07`. Es lo que conviene preguntar al propietario antes que cualquier otra cosa del
backlog — ningún otro bloqueante accionable pasa de fan-out 1.
