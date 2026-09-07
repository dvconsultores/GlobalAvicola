# MAPA DE DEPENDENCIAS DEL PROGRAMA DE REMEDIACIÓN

## 1. Grafo de dependencias

```
                         ┌──────────────────────────────┐
                         │ GA-REM-001  GOBIERNO         │ ✅ CERTIFIED
                         │ Constitución ratificada      │
                         └──────────────┬───────────────┘
                                        │ habilita TODAS
        ┌───────────────────────────────┼───────────────────────────────┐
        ▼                               ▼                               ▼
┌───────────────────┐         ┌───────────────────┐         ┌───────────────────┐
│ GA-REM-014        │         │ VÍA PARALELA      │         │ GA-REM-020        │
│ Entorno de test   │         │ 004 · 009 · 010   │         │ Validación de     │
│ aislado           │         │ (riesgo activo)   │         │ cobertura         │
└─────────┬─────────┘         └───────────────────┘         └─────────┬─────────┘
          │ habilita el cierre de 11 specs                            │ INFORMA
          │                                                           │ (no bloquea)
   ┌──────┼──────────┬──────────────┬──────────────┐                  │
   ▼      ▼          ▼              ▼              ▼                  │
┌──────┐┌──────┐ ┌────────┐   ┌────────┐    ┌────────┐                │
│ 005  ││ 002  │ │  011   │   │  015   │    │  013   │                │
│Mortal││ RBAC │ │Contrat.│   │Tests BE│    │ Gates  │                │
└──┬───┘└──┬───┘ └───┬────┘   └───┬────┘    └────────┘                │
   │       │         │            │                                   │
   │  ┌────┴────┐    │            │                                   │
   │  ▼         ▼    │            │                                   │
   │┌──────┐┌──────┐ │            │                                   │
   ││ 007  ││ 003  │ │            │                                   │
   ││BR-14 ││ Auth │ │            │                                   │
   │└──────┘└──┬───┘ │            │                                   │
   │           ▼     │            │                                   │
   │       ┌──────┐  │            │                                   │
   │       │ 012  │  │            │                                   │
   │       │Passwd│  │            │                                   │
   │       └──────┘  │            │                                   │
   │                 │            │                                   │
   │      ┌──────────┼────────┐   │                                   │
   │      ▼          ▼        ▼   │                                   │
   │  ┌──────┐  ┌──────┐ ┌──────┐ │                                   │
   │  │ 006  │  │ 008  │ │ 022  │ │                                   │
   │  │Correc│  │Trazab│ │ KPI  │ │                                   │
   │  └──┬───┘  └──┬───┘ └──┬───┘ │                                   │
   │     │         │        │     │                                   │
   └─────┴────┬────┴────────┴─────┘                                   │
              ▼                                                       │
      ┌───────────────┐  ◀──────────── insumo de cobertura ───────────┘
      │  GA-REM-016   │
      │ Certificación │            ┌──────────────────┐   ┌──────────┐
      │ E2E+procesos  │            │   GA-REM-017     │   │  021     │
      └───────┬───────┘            │   SAP real       │   │  Agua    │
              ▼                    │ BLOCKED_EXTERNAL │   └──────────┘
      ┌───────────────┐            └──────────────────┘   (independiente,
      │  GA-REM-018   │                    ▲               informada por 020)
      │ Trazabilidad  │                    │
      │ Spec Dev      │              GA-REM-010
      └───────┬───────┘              (semántica SAP)
              ▼
      ┌───────────────┐
      │  GA-REM-019   │
      │  Deuda P2/P3  │
      └───────────────┘
```

**Cambio respecto a la versión inicial:** `GA-REM-020` deja de ser bloqueante. Por decisión del propietario, la documentación del cliente es **fuente de validación**, no estructura a adoptar; la taxonomía del proyecto se conserva y sigue siendo la unidad de certificación. `020` **informa** a `016`, `021` y `022`, y alimenta el backlog con los huecos que encuentre.

## 2. Tabla de dependencias

| GA-REM | Depende de | Habilita | Tipo de dependencia |
|---|---|---|---|
| `001` Gobierno | — | todas | **bloqueante absoluta** — sin constitución no hay regla que aplicar |
| `020` Validación de cobertura | `001` | *informa a* `016`, `021`, `022` | **no bloqueante** — aporta verificación de completitud |
| `014` Entorno de test | `001` | `002,003,005,006,007,008,011,012,013,015,016` | **bloqueante de cierre** — sin ella ningún AC ejecutable se puede verificar |
| `004` Credenciales | `001` | — | independiente |
| `009` Evidencias | `001` | — | independiente |
| `010` Semántica SAP | `001` | `017` | independiente para ejecutar |
| `005` Mortalidad | `001`, `014` | `016` (proceso de control diario) | de cierre |
| `002` RBAC | `001`, `014` | `007`, `012`, cierre de seguridad | de cierre |
| `003` Auth/token | `001`, `014` | `012` | de cierre |
| `007` BR-14 | `001`, `002`, `014` | `016` | funcional — necesita saber quién puede aprobar |
| `012` Contraseña | `001`, `002`, `003`, `014` | — | funcional — política de sesión y permisos |
| `011` Contratos | `001`, `014` | `006`, `008`, `016`, `022` | funcional — repara las pantallas que otras specs necesitan |
| `006` Correcciones | `001`, `011`, `014` | `016` | funcional — su pantalla está rota |
| `008` Trazabilidad | `001`, `011`, `014` | `016` | funcional |
| `021` Agua | `001` | — | independiente; `020` le indica en qué etapas capturar |
| `022` KPI | `001`, `011` | `016` | funcional — 4 KPI son endpoints huérfanos |
| `013` Quality gates | `001`, `014` | — | de cierre — el gate de backend necesita el entorno |
| `015` Tests backend | **`014`** | `016` | **bloqueante absoluta** |
| `016` Certificación | `002`, `005`, `006`, `007`, `011`, `014`, `015` | `018` | **de convergencia**; `020` aporta la columna de cobertura validada |
| `017` SAP real | `010`, `011` + **externo** | — | `BLOCKED_EXTERNAL` |
| `018` Trazabilidad Spec Dev | `001` + estabilización | `019` | de secuencia |
| `019` Deuda P2/P3 | Fases A–G | — | de secuencia |

## 3. Rutas críticas

**Ruta crítica principal** (la más larga hasta certificar un proceso):
```
001 → 014 → 011 → 006 → 016
```
Cuatro specs encadenadas antes de poder certificar el proceso de revisión y aprobación. **Se acortó en un paso** al dejar de bloquear con `GA-REM-020`.

**Ruta crítica de seguridad**:
```
001 → 014 → 002 → 007 → 012
```

**Ruta crítica de la operación diaria** (la más corta hasta valor operativo):
```
001 → 014 → 005
```
Tres specs para desbloquear el registro de mortalidad. **Es la ruta de mayor retorno inmediato.**

## 4. Trabajos paralelizables

Tras cerrar `GA-REM-001` (ya certificada), estos bloques no compiten entre sí:

| Vía | Specs | Perfil |
|---|---|---|
| **V1 · Habilitante** | `014` | infraestructura de pruebas |
| **V1b · Validación** | `020` | documental; sin tocar código |
| **V2 · Infraestructura y datos** | `004` · `009` · `010` | configuración; sin dependencias cruzadas |
| **V3 · Contratos** | `011` | frontend + backend |
| **V4 · Proceso** | `013` (parcialmente; su gate de backend espera a `014`) | CI |

`004`, `009` y `010` pueden ejecutarse **en paralelo desde el primer día**, sin esperar a `014`, porque sus AC no requieren la suite de tests de backend.

## 5. Bloqueos activos

| Bloqueo | Specs afectadas | Naturaleza | Acción |
|---|---|---|---|
| ~~`RC-01`~~ flujo de corrección | ~~`006`~~ | **RESUELTO** por evidencia (`RR-01`, Wave 1.5) — la corrección se aplica en el acto y el registro sigue requiriendo aprobación | — |
| ~~`RC-02`~~ semántica de `bird_transfer` | ~~`005`~~ | **RESUELTO** por evidencia (`RR-02`) — intra-lote entre galpones, neutro en el balance; el esquema no admite otra lectura | — |
| ~~`RC-03`~~ ¿BR-14 absoluta o configurable? | ~~`007`~~ | **RESUELTO** por evidencia (`RR-03`) — configurable por paso, `require_segregation` por defecto `True` | — |
| **`RC-04`** «el mismo lote de huevos» en `spec.md §4.9` | `008` | ambigüedad de spec | corrección de spec — **único `RC` técnico abierto** |
| ~~`RC-05`~~ política de contraseñas | ~~`012`~~ | **RESUELTO** por evidencia (`RR-05`) — política única de longitud 8; el conflicto era aparente | — |
| **`RC-07`** política de mortalidad frente a SAP | `017` (solo el mapeo) | **`OWNER_DECISION_REQUIRED`** — el propio cliente la declara pendiente (§25.4). Acotado por `RR-07`: **ya no bloquea `005`** | decisión contable del propietario (`OD-02`) |
| **`023` → `005`** (nueva) | `005` | dependencia técnica: sin `cause_id` persistido, la mortalidad no puede registrar la causa | ejecutar `023` antes que `005` |
| ~~`RC-06`~~ | ~~`020`, `016`~~ | **CERRADO** — desaparece: no se adopta la granularidad del cliente, y la validación preliminar confirma que el «Desalojo» está cubierto funcionalmente por `bird_exit` y `lot_closure` | — |
| **Contrato técnico SAP** | `017` | dependencia externa | **solicitar al cliente** |
| Confirmación de cobertura con el cliente | `020` | deseable, no bloqueante | validar el resultado de `020` con el negocio |

**Tras la Wave 1.5 solo queda un `RC` técnico abierto (`RC-04`) y una decisión de negocio acotada (`RC-07` → `OD-02`).** Cuatro de los cinco conflictos que bloqueaban `005`, `006`, `007` y `012` se resolvieron leyendo las fuentes en el orden de la jerarquía: no hacía falta ninguna decisión. Detalle en `REQUIREMENT_CONFLICT_RESOLUTION.md`.

Dependencia nueva de Wave 1.5: **`GA-REM-023` precede a `GA-REM-005`**, y `R-28` (fechas relativas en los tests) precede a todo, porque expira el 2026-09-21.

## 6. Ajustes de orden respecto al encargo

| Ajuste | Justificación |
|---|---|
| `GA-REM-020` se ejecuta pronto pero **sin bloquear** | no es prerequisito de nadie: informa. Se ejecuta temprano porque puede revelar más huecos como R-13 y R-14, y conviene tenerlos en el backlog antes de comprometer el alcance de certificación |
| `GA-REM-014` se adelanta por delante de `GA-REM-005` | los AC de `005`, `006` y `007` exigen tests ejecutables; sin entorno aislado esas tres specs no pueden cerrarse |
| `GA-REM-012` se agrupa en la Fase B | comparte superficie con `002` y `003`; su AC depende de la política de sesión de `003` |
| `GA-REM-004`, `009` y `010` se adelantan como vía paralela | no dependen de `014`; su cierre reduce riesgo activo en producción desde el primer día |


---

# Grafo tras la Wave 2 (2026-09-04)

Las dependencias técnicas del programa están **resueltas**. Lo que queda no es un grafo de
trabajo encadenado sino una condición de entorno y dos esperas externas.

```
R-44  (permisos en produccion)  --->  despliegue del RBAC  --->  GA-REM-016 (E2E)
                                                                      ^
GA-REM-011 (8 contratos)  ----------------------------------------- |
GA-REM-021 / 022  ------------------------------------------------- |

OD-02 (RC-07)  ----->  mapeo SAP de mortalidad  ----->  GA-REM-017
Contrato tecnico SAP  -------------------------------->  GA-REM-017
```

## Dependencias que dejaron de existir

| Dependencia | Por qué desaparece |
|---|---|
| `RC-01`, `RC-02`, `RC-03`, `RC-05` → `005`, `006`, `007`, `012`, `018` | resueltas por evidencia en la Wave 1.5 |
| **`RC-04` → `008`** | resuelta por evidencia en la Wave 2 (`RR-04`) |
| **`023` → `005`** | `023` certificada; `005` pudo ejecutarse |
| **`002`/`003` → `007`, `012`** | ambas ejecutadas en la Wave 2 |
| `RC-07` → `005` | acotada por `RR-07`: solo alcanza al mapeo SAP |

## Dependencia nueva

**`R-44` precede a `GA-REM-016`.** Certificar procesos E2E contra un sistema cuyo catálogo
de permisos en producción no admite a los roles que esos procesos requieren produciría una
certificación que no se sostiene fuera del entorno de pruebas.


---

## Checkpoint `R-68` + `R-67` (2026-09-04)

```
GA-REM-025  (baseline limpio)
    │  reveló
    ├──► R-68 ──► GA-REM-026  (frontera transaccional)  P0 · CERTIFIED
    │                 │  bloqueaba
    │                 └──► GA-REM-016  (podía producir falsos negativos en E2E)
    │
    └──► R-67 ──► GA-REM-005  (enmienda, saldo de apertura)  P1 · CERTIFIED
```

El orden no fue arbitrario. `R-68` es sistémico y afecta a las 90 rutas de escritura:
mientras estuviera abierto, cualquier fallo E2E podía ser síntoma suyo y no un defecto
propio. Clasificar los 23 fallos heredados antes de cerrarlo habría medido ruido.

`R-67` no dependía de `R-68`, pero se atendió después por la misma razón de orden: su
certificación pasa por la API, y con `R-68` abierto sus lecturas inmediatas habrían sido
intermitentes.

### Dependencias nuevas

| De | A | Naturaleza |
|---|---|---|
| `GA-REM-026` | ninguna | causa raíz única, sin prerrequisitos |
| `GA-REM-005` enmienda | `RC-08` / `RR-08` | resolución de requisito previa a la implementación |
| `GA-REM-016` | `GA-REM-026` | **desbloqueada**: el baseline E2E ya puede medir defectos reales |


---

## Decisión de continuidad (2026-09-05) — `GA-REM-027` → `GA-REM-016`

El propietario autoriza reanudar `GA-REM-016` sin que `GA-REM-027` esté `CERTIFIED`.

```
GA-REM-027 → GA-REM-016
DEPENDENCY STATUS = DEFERRED_VERIFICATION
```

Se usa `DEFERRED` —vocabulario ya presente en el registro— cualificado como verificación
diferida. No se inventa un estado nuevo.

### La regla que sustituye a la anterior

Antes: `GA-REM-027` debía estar `CERTIFIED` para reanudar. Ahora `GA-REM-016` puede
reanudarse cuando:

| # | Condición | Estado |
|--:|---|---|
| 1 | La implementación de `GA-REM-027` está desplegada | **sí** — `f46cb13` |
| 2 | La validación estática de configuración pasa | **sí** — analizador oficial, status ok |
| 3 | La API pública está sana | **sí** — `L2` y `L3` en 200 |
| 4 | No se reproduce ningún defecto conocido de resolución | **sí** — 0/60 muestreos |
| 5 | Una recreación controlada de backend no deja «backend sano + proxy roto» | **sí** — ciclo del 14:34 |
| 6 | El trabajo restante de `GA-REM-027` es **solo de verificación** | **sí** — `AC08` |
| 7 | Esa verificación pendiente no invalida el entorno E2E aislado de `GA-REM-016` | **sí** — el arnés no atraviesa ese proxy |

La séptima es la que hace defendible la decisión: `scripts_e2e.sh` levanta backend y
frontend con puertos propios y **no usa el nginx del contenedor**, de modo que el hueco de
verificación de `GA-REM-027` no puede contaminar la certificación E2E.

### Clasificación del hueco

```
DEFECTO DE IMPLEMENTACIÓN CONOCIDO ABIERTO ...... NO
FALLO DE EJECUCIÓN OBSERVADO ACTUALMENTE ....... NO
API PÚBLICA .................................... SANA
VALIDACIÓN ESTÁTICA DE CONFIGURACIÓN ........... PASS
RECREACIÓN CONTROLADA DE BACKEND ............... PASS
MUESTREOS «BACKEND SANO + PROXY ROTO» .......... 0 / 60
CAMBIO DE IP DEL BACKEND VERIFICADO ............ NO
CICLOS DE RE-IP REPETIDOS EXIGIDOS ............. NO VERIFICADOS

GA-REM-027 = PARTIAL — HUECO DE VERIFICACIÓN
```

La evidencia de comportamiento es fuerte; la evidencia completa de `AC08` falta. Son cosas
distintas y se registran por separado.

### Condición de interrupción

Mientras `GA-REM-027` siga `PARTIAL`, si durante la Wave 3 vuelve a observarse:

```
salud directa del backend = PASS
+
ruta pública / proxy      = FAIL
```

se **detiene `GA-REM-016`** y `GA-REM-027` se reabre como bloqueante. No se certifica E2E
sobre un proxy defectuoso conocido. El gate
`backend/scripts/runtime_connectivity_check.py` distingue esos dos niveles precisamente
para que la condición sea comprobable en un solo comando.


---

## `GA-TD-014` · la dependencia que gobierna tres procesos

```
RC-07  (decisión del propietario, ABIERTA)
  │
  └─→ GA-TD-014 · la OC de SAP al campo tipado
        │           activa BR-11 y BR-18, hoy inertes
        ├─→ P-01  Progenitoras — Cría
        ├─→ P-03  Reproductoras — Cría
        └─→ P-06  Pollo de engorde        (su otro hueco: GA-REQ-037)
```

Es el único bloqueante conocido con fan-out mayor que uno, y su raíz **no es técnica**: la
corrección está clara y `C-15` la dejó diferida porque cambia el comportamiento para los
operadores. Mientras `RC-07` siga abierta, esos tres procesos no pueden certificarse por
mucho que se remedie alrededor.

> **Superado (2026-09-06).** La premisa de que `GA-TD-014` dependía de `RC-07` resultó falsa:
> el propietario resolvió `OD-04` —una OC admite varias entregas parciales— sin tocar `RC-07`,
> que sigue abierta y es un asunto distinto. Los tres procesos están hoy certificados. Se
> conserva el análisis porque su predicción de fan-out fue correcta y ordenó el trabajo.

`GA-REM-029` cerró `R-73`, `R-74` y `R-75` —el paso terminal de `P-06`— sin mover ninguno de
los tres de `PARTIAL`, que es exactamente lo que este mapa predecía.


---

## Corrección · `GA-TD-014` no cuelga de `RC-07`

El mapa anterior hacía descender `GA-TD-014` de `RC-07`. **Es incorrecto**, y la corrección
sale de las fuentes, no de una reinterpretación:

```
RC-07  ·  política de mortalidad frente a SAP        (OD-02, ABIERTA)
  └─→ mapeo de mortalidad dentro de GA-REM-017        ← su ÚNICO bloqueo residual
                                                        (GA-REM-017 ya BLOCKED_EXTERNAL)

OD-04  ·  ¿entregas parciales contra una misma orden?  (NUEVA, ABIERTA)
  └─→ GA-TD-014 · la OC al campo tipado
        ├─→ P-01   ├─→ P-03   └─→ P-06
```

`RR-07` lo acotó por escrito: *«solo el mapeo de mortalidad a un documento SAP queda
supeditado a la decisión del propietario»*. Y `docs/16` separa las cinco decisiones del
cliente (`G-R02`, Fase 10A) de la validación de cantidad contra la orden (`G-R05`, Fase 10B).

`GA-REM-010`, la otra dependencia que citaba `C-15`, está `CERTIFIED`.

La consecuencia práctica no cambia —`P-01`, `P-03` y `P-06` siguen `PARTIAL` a la espera de
una decisión— pero **la decisión es otra, es más pequeña y es respondible en una frase**:
`RC-07_BUSINESS_DECISION_DOSSIER.md`.


---

## `P-10` · lo que realmente lo bloquea

```
R-78  ·  el vínculo automático no se crea en el orden natural      (P1, ABIERTO)
  └─→ P-10 pasos 3, 4, 7, 8
        └─→ P-10 = PARTIAL

R-79  ·  la prueba de GA-REM-008 AC01 no puede fallar              (P2, ABIERTO)
  └─→ explica por qué R-78 sobrevivió a una certificación
        └─→ GA-REM-008 AC01 = NOT_EVIDENCED

R-60  ·  pertenencia en los vínculos manuales                      CERTIFIED (GA-REM-030)
```

El mapa anterior daba `R-60` como lo único que separaba a `P-10` de la certificación. Era
cierto según los artefactos de entonces y ha resultado falso: la certificación de
`GA-REM-008 AC01` se apoyaba en una aserción vacua, así que la distancia real nunca fue
visible en ninguna matriz.


---

## `P-10` · resuelto (2026-09-05)

```
R-60  pertenencia en los vínculos manuales     CERTIFIED (GA-REM-030)
R-78  la recepción no creaba el vínculo        CERTIFIED (GA-REM-031)
R-79  la evidencia de AC01 no podía fallar     CERTIFIED (GA-REM-016 enm. F)
  └─→ P-10 = CERTIFIED · 12 de 12 pasos
```

La cadena de causas merece quedar dicha, porque es la lección del tramo:

```
R-79 (evidencia vacua)  permitió que  R-78 (defecto de dominio)  sobreviviera a
GA-REM-008, y R-78 mantenía P-10 en PARTIAL sin que ninguna matriz lo mostrara.
```

Ninguna de las tres se veía desde fuera. Solo aparecieron al recorrer el proceso entero.


---

## `P-09` · resuelto (2026-09-06)

```
R-81  seis módulos sin registro de auditoría      CERTIFIED (GA-REM-032)
R-82  la vista aparentaba filtrar                 CERTIFIED (GA-REM-032)
R-84  el filtro de fecha devolvía 500             CERTIFIED (GA-REM-032)
  └─→ P-09 = CERTIFIED · 14 de 14 pasos

R-83  una acción sin empresa no puede auditarse   ABIERTO — no bloquea P-09
```

`R-84` no estaba en ninguna matriz: apareció al escribir la prueba del filtro de fecha. Es el
tercer tramo consecutivo en que un defecto real sale a la luz **solo** al exigirle a una
prueba que pueda fallar.


---

## `P-15` · resuelto (2026-09-06)

```
R-14  la eclosión devolvía texto                CERTIFIED (GA-REM-022 enm. A)
R-85  tres cocientes fundidos en uno            CERTIFIED
R-86  fertilidad sin productor                  CERTIFIED
  └─→ P-15 = CERTIFIED · 16 de 16 pasos

R-87 · R-88  RETIRADOS — no eran hallazgos
```

`R-88` merece quedar en el mapa aunque se retire: la exportación Excel/PDF **no depende del
backend**; vive en el cliente con SheetJS y jsPDF. Quien busque esa capacidad en el servidor
no la encontrará, y esa es exactamente la trampa en la que caí.


---

## `P-12` · resuelto (2026-09-06)

```
R-90  siete maestros sin gestión        CERTIFIED (GA-REM-033)
R-91  siete sin capacidad de edición    CERTIFIED
R-89  el total descartado               CERTIFIED
  └─→ P-12 = CERTIFIED · 8 de 8 pasos
```

Una dependencia que conviene dejar dicha: `/masters/*` tiene **43 consumidores** en el
frontend, muchos más que cualquier otro listado de la aplicación. Es la razón de que el total
viaje en cabecera y no en el cuerpo, y quien vaya a tocar ese contrato debe contarlos antes.


---

## `P-13` · resuelto (2026-09-06)

```
R-92  sin superficie de administración   CERTIFIED (GA-REM-034)
R-93  los permisos no se podían editar   CERTIFIED
R-94  sin catálogo de permisos           CERTIFIED
  └─→ P-13 = CERTIFIED · 14 de 14 pasos

OD-05  ¿quién puede conceder qué permiso?   ABIERTO — no bloquea
```

La distinción que ordenó este tramo:

```
GA-REM-002  ENFORCEMENT      que el permiso se aplique      CERTIFIED, intacto
GA-REM-034  ADMINISTRACIÓN   que pueda concederse           CERTIFIED
```

Son dos cosas. Tratarlas como una habría llevado a reabrir una spec cerrada para construir
una pantalla.


---

## `OD-04` resuelta (2026-09-06)

```
OD-04  RESOLVED — una OC admite varias entregas parciales
  └─→ GA-TD-014  CERTIFIED (GA-REM-035)
        ├─→ P-01  CERTIFIED     · era su único hueco
        ├─→ P-03  PARTIAL       · §4.5 exige la alerta de peso — GA-REQ-037
        └─→ P-06  PARTIAL       · §4.8 no exige alertas, pero R-76 bloquea el cierre
```

La lección del nodo: **un bloqueante compartido no implica un desbloqueo compartido**. Los
tres colgaban de `OD-04` y solo uno quedó libre; los otros dos tenían huecos propios que el
fan-out ocultaba.

```
R-95  la cantidad ordenada se descartaba en la importación   CERTIFIED
      └─→ sin esto, BR-18 era inaplicable aunque el campo estuviera poblado
```


---

## `P-06` · resuelto (2026-09-06)

```
GA-TD-014  CERTIFIED (GA-REM-035, tras OD-04)
R-76       CERTIFIED (GA-REM-036, docs/12 R7)
GA-REQ-037 NO APLICA — §4.8 no exige alertas; las exige §4.5, que es P-03
  └─→ P-06 = CERTIFIED · 11 de 11 pasos
```

El cierre de lote tiene ahora tres guardas y un resumen, y las cuatro piezas vienen de tramos
distintos:

```
lote activo   GA-REM-029 AC06
BR-05         GA-REM-029 (R-74: la regla vigilaba la puerta equivocada)
R7            GA-REM-036 (R-76)
resumen       GA-REM-029 (R-73) con la fecha de R-75
```


---

## `P-03` · resuelto (2026-09-06) — y con él, la última dependencia de requisito

```
GA-TD-014   CERTIFIED (GA-REM-035, tras OD-04)
GA-REQ-037  CERRADO   (GA-REM-037, tras OD-06)
  └─→ P-03 = CERTIFIED · 14 de 14 pasos
```

`GA-REQ-037` era de una clase distinta a todo lo demás de este mapa. No era un defecto ni una
regla desactivada: era un requisito que pedía comparar contra un dato que el sistema **no
tenía ni podía derivar**.

```
spec.md §4.5  «alertas por desviaciones (peso fuera de curva estándar …)»
                                              │
                          ¿de dónde sale la curva estándar?  ← no había respuesta en el repositorio
```

Ni la spec, ni los documentos de proceso, ni la implementación definían esa curva. Por eso la
única salida honesta era elevarla, y por eso `OD-06` la desbloquea sin una sola línea de código
de por medio:

```
OD-06 (decisión del propietario, RESUELTA 2026-09-06)
  │
  └─→ GA-REM-037 · curvas por línea genética, versionadas
        ├─→ genetic_weight_curves + puntos      el dato que faltaba
        ├─→ lots.weight_curve_id               la versión fijada al lote
        ├─→ weight_curve.py                    el motor, en un solo sitio
        └─→ alerta weight_deviation            el paso normativo de §4.5
              └─→ P-03 = CERTIFIED
```

### Lo que queda, y de qué clase es

Ningún bloqueante técnico pendiente alcanza fan-out 2. Los dos procesos `PARTIAL` restantes no
esperan trabajo:

```
P-08   contrato SAP real            dependencia externa   GA-REM-017 BLOCKED_EXTERNAL
P-14   canal de notificación        decisión sin plantear + desarrollo
```

Y dos decisiones siguen abiertas sin bloquear ningún proceso:

```
RC-07  ¿la mortalidad se envía a SAP?          ABIERTA
OD-05  ¿quién puede conceder qué permiso?      ABIERTA — no bloquea (P-13 ya certificado)
```


---

## `P-14` · resuelto a medias, y la mitad que falta no es técnica (2026-09-07)

```
OD-07 (canal)  RESUELTA
  │
  └─→ GA-REM-038 · bandeja interna
        ├─→ notifications + migración n4o5p6q7r8s9
        ├─→ record_rejected  ←  review/service.py       destinatario: docs/02 §3.14
        ├─→ sap_send_failed  ←  sap/service.py          destinatario: docs/10 §6.2
        └─→ campana, contador, lectura, aislamiento     UI_E2E 5/5
              └─→ P-14 = PARTIAL   (2 de 6 tipos)

OD-08 (destinatarios)  ABIERTA
  └─→ los otros cuatro tipos de docs/02 §3.14
```

La dependencia que queda es de **información**, no de trabajo: los disparadores de dos de esos
cuatro ya existen y funcionan; lo único que falta es saber a quién avisar. Los otros dos
necesitan además un planificador, que es una decisión de arquitectura que `OD-07` no tomó.

### El estado del programa

```
P-08   contrato SAP real          dependencia externa   GA-REM-017 BLOCKED_EXTERNAL
P-14   a quién avisar             decisión de negocio   OD-08
```

**Ningún proceso queda bloqueado por trabajo técnico pendiente.** Los dos que faltan esperan a
alguien de fuera: SAP en un caso, el propietario en el otro.

```
RC-07  ¿la mortalidad se envía a SAP?          ABIERTA, no bloquea ningún proceso
OD-05  ¿quién puede conceder qué permiso?      ABIERTA, no bloquea (P-13 certificado)
OD-08  ¿quién recibe los avisos operativos?    ABIERTA, bloquea 4 tipos de P-14
```


---

## `OD-08` · la mitad que se resolvió y la que no (2026-09-07)

```
OD-08 · destinatarios  RESUELTO
  │
  └─→ GA-REM-038 enmienda A · resolver_destinatarios()
        ├─→ registro rechazado         operador ∪ OD-08
        ├─→ error de envío SAP         Analista SAP ∪ OD-08
        ├─→ mortalidad > umbral        OD-08
        ├─→ peso fuera de estándar     OD-08
        └─→ pendiente de revisión >24h OD-08  ← desbloqueado al leer el nombre literal
              └─→ P-14 = PARTIAL   (5 de 6)

OD-08 · semántica temporal  ABIERTO
  └─→ «lote próximo a cierre»

MODELO
  └─→ área y rol de gerencia   →  AC-R04 bloqueado
```

### El estado del programa

```
P-08   contrato SAP real                 dependencia externa   GA-REM-017
P-14   semántica de un evento + modelo   decisión              OD-08
```

Ningún proceso queda bloqueado por trabajo técnico pendiente. Y conviene distinguir las dos
cosas que bloquean a `P-14`, porque no son iguales:

```
«lote próximo a cierre»   el propietario tiene que decidir qué significa
gerente del área          el modelo tiene que ganar un concepto que no tiene
```

La segunda no la resuelve una respuesta: exige diseñar áreas y asignar usuarios a ellas, que es
trabajo con su propia spec.
