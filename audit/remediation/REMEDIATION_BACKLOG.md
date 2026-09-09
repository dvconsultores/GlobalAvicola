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

## `R-124` · `P1` · `OWNER_DECISION_REQUIRED` · ¿vienen de SAP las Empresas y las Granjas?
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
| **`R-135`** | **P1** | `RETURNED` no se reenvía; `REJECTED` es terminal | `H360-P03`, `H360-D09` | `docs/12 §4` | B | spec propia o enm. `GA-REM-006` + `spec §4.10` | **`OD-17`** ✓ |
| **`R-136`** | **P1** (SAP) | tabla `reversals` sin servicio ni ruta; `BR-16` sin mecanismo | `H360-P05` | `BR-16` · Rec. §24 | B · D | spec propia | — |
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

Evidencia: `R-139-OD14-PRODUCTIVE-DATA-EVIDENCE.md`. Regresión completa: **830 passed · 49 skipped · 0 failed** (542 s; 795 previas + 35 de `test_od14_productive_surfaces.py`; los 49 saltados son `test_upgrade_path` y `test_runtime_startup`, que exigen su script dedicado). Por archivo: aislamiento de maestros 16 · usuarios 18 · roles 12 · unidades 31 · guarda 25 · administración 39 · sesión 16 · accesos 16 · candidatos 14 · `test_rbac` 21 (`SOLO_SUPER_ADMIN` ≤ 15 sin tocar) · clasificación pendiente 35 · curvas 16 · multiempresa 5 + 12 · saldo de apertura 12 · filas por unidad 21 · KPI por unidad 15 · catálogo de empresas 11. Vitest 87 passed / 8 archivos. `tsc` 6 errores preexistentes (`AuditPage.tsx`, `LotFormPage.tsx`), mismo número y mismos ficheros que en `7ee72a1` (`R-158`, sin cambio).

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
| `R-165` | P2 | el plano de revisión (`review/start|return|complete`, `approvals/approve|reject`) no exige la **habilitación** de la unidad a la autoridad global (`_ambito_de_unidad` → `[]` para `is_super_admin`); misma clase que `R-163`; el actor de empresa ya queda fuera por `unidades_efectivas` | `review/service.py:77-99, 360-383, 561-580` | B |
| `R-166` | P3 | `approve` y `reject` sobre el mismo evento `CORRECTED` no se excluyen (sin bloqueo de fila; el último `flush` gana) | `review/service.py:423-470` | B |

Trazas parciales del tranche 4: **`R-140`** → PARTE A (guarda de estados de `cancel`: `SAP_CONFIRMED`/`SAP_ERROR`/`CANCELLED`) en `GA-REM-006-A`; motivo obligatorio (contrato de ruta que el cliente llama sin cuerpo → UI) y permiso «solo administrador» (`AOD-18`) → OPEN. **`R-154`** → subconjunto `DRAFT` (mapa de transiciones + controles) y `version` (semántica vigente documentada: avanza en `PUT` y en corrección; la matriz 360 lo daba por no incrementado) en `GA-REM-006-A`; dos «cierres» (`AOD-08`) y `LotStatus.CANCELLED` → OPEN. `R-163` normalizada a **P1**.

---

## Cierre de `R-135` + `R-143` · continuidad de estados de `P-07` y segregación corrector/rechazador ≠ aprobador · WAVE B tranche 4 (2026-09-09)

```
R-135    CERRADO (técnico)   GA-REM-006 enmienda A · OD-17.a/b · RETURNED/REJECTED reenviables (submit → PENDING_REVIEW, explícito, auditado)
                            · REJECTED editable y corregible · mapa explícito EDITABLES/REENVIABLES/NO_CANCELABLES · cadena inquilino/unidad
                            en POST /corrections · AC-S01…S12 · AC-R01…R07 · AC-D01…D06 · AC-U01…U05 · 24/24 · rojo previo 13 rojas
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

Evidencia: `R-135-R-143-STATE-CONTINUITY-EVIDENCE.md`. Regresión completa: **949 passed · 49 skipped · 0 failed** (735 s; 919 previas + 30 de `test_state_continuity.py`/`test_segregation_r143.py`); los 49 saltados son `test_upgrade_path` y `test_runtime_startup`, que exigen su script dedicado). `vitest` 87/87 · `tsc` 6 preexistentes (`R-158`). Sin migración (`s9t0u1v2w3x4`), sin rutas nuevas, sin estados nuevos, sin frontend. `R-161` OPEN · `R-164` BLOCKED_RUNTIME · fase 9 FROZEN · `BU-D10` PENDING_RATIFICATION · SAP no iniciado.
