# REMEDIATION READINESS REPORT

| | |
|---|---|
| **Fecha** | 2026-09-03 |
| **Commit base** | `bfccdfb` — **sin cambios desde la auditoría** (verificado con `git status`) |
| **Alcance de esta ejecución** | organización y preparación del programa. **No se ha implementado ninguna corrección funcional.** |

---

## 1. Qué se ha entregado

| # | Entregable | Ubicación |
|---|---|---|
| 1 | Programa maestro de remediación | `specs/remediation/GLOBAL_AVICOLA_REMEDIATION_PROGRAM.md` |
| 2 | Matriz maestra de remediación | `audit/remediation/MASTER_REMEDIATION_MATRIX.md` |
| 3 | Mapa de dependencias | `audit/remediation/DEPENDENCY_MAP.md` |
| 4 | Backlog priorizado | `audit/remediation/REMEDIATION_BACKLOG.md` |
| 5 | **`GA-REM-001` completa y certificada** | `specs/remediation/GA-REM-001-*.md` + `.specify/memory/constitution.md` v1.0.0 |
| 6 | Índice de las 22 GA-REM | `specs/remediation/INDEX.md` |
| 7 | 21 specs preparadas | `specs/remediation/GA-REM-002…022` |
| 8 | Este informe | `audit/remediation/REMEDIATION_READINESS_REPORT.md` |

Único artefacto de aplicación modificado: `.specify/memory/constitution.md` (documento de gobierno, entregable de `GA-REM-001`). **Cero cambios en `backend/app/`, `frontend/src/`, `alembic/versions/` y `.github/workflows/`.**

---

## 2. Revalidación de los hallazgos (§7 del encargo)

Cada bloqueador se reconfirmó **contra el código actual**, no contra el informe de auditoría.

| Hallazgo | Verificación ejecutada | Resultado |
|---|---|---|
| P0-1 mortalidad → 500 | análisis AST de `operations/service.py`: `get_current_bird_balance` en los imports | **CONFIRMADO** — no importado; firma de 2 args, invocación con 3 |
| P0-2 correcciones no aplicadas | inspección de `corrections/service.py` | **CONFIRMADO** — hay `event.status = CORRECTED`, no hay `setattr` sobre el dato |
| P0-3 sin RBAC | `grep -rn "require_permission\|has_permission\|check_permission" backend/app` | **CONFIRMADO** — 0 resultados |
| P0-4 refresh degrada identidad | `auth/service.py:72` | **CONFIRMADO** — emite `{"sub","username"}` |
| P0-5 pantallas rotas (422) | `grep -rn "limit=200\|limit: 200" frontend/src` | **CONFIRMADO** — 6 en páginas + 5 en la capa de hooks muerta |
| P0-6 evidencias efímeras | `MEDIA_DIR` + `volumes` en el servicio backend | **CONFIRMADO** — 0 declaraciones de volumen |
| P0-7 SAP simulado | `sap/service.py:34-38` + `docker-compose.yml:26` | **CONFIRMADO** — `# TODO` y `FEATURE_SAP_ENABLED` activo |
| P0-8 credenciales públicas | `GUIA_PRUEBAS_EN_VIVO.md` | **CONFIRMADO** — 31 coincidencias; sin `FEATURE_RATE_LIMIT_ENABLED` en el compose |
| P0-9 contraseña no cambia | `auth/schemas.py:42-49` | **CONFIRMADO** — `UserUpdate` no declara `password` |
| P0-10 BR-14 eludible | `grep -n validate_segregation backend/app` | **CONFIRMADO** — una sola invocación, en `review/service.py:318` |
| P0-11 trazabilidad auto-referencial | `operations/service.py:128-228` | **CONFIRMADO** — las 4 ramas filtran por `lot_id == data.lot_id` |
| P0-12 sin puerta de calidad | triggers de los 5 workflows + `git log --merges` | **CONFIRMADO** — calidad solo en `pull_request`; 0 merges |

```
Hallazgos revalidados ......... 12
CONFIRMADOS ................... 12
ALREADY_RESOLVED ..............  0
```

**Ningún hallazgo ha quedado obsoleto.** No se corregirá ningún defecto que ya no exista.

---

## 3. Hallazgos NUEVOS descubiertos en la revalidación

La auditoría registró `Imagen de Procesos Documentado/` (43 archivos del cliente) como *«fuente disponible y no explotada formalmente»*. Esta ejecución la explotó. Resultado: **3 hallazgos que la auditoría no tenía**.

| ID | Hallazgo | Evidencia | Spec asignada |
|---|---|---|---|
| **R-13** | **El consumo de agua no se captura.** El documento de requerimientos original del cliente lo exige como dato diario obligatorio en Reproductora Cría, Reproductora Producción y Engorde. `grep water backend/app` → 0 resultados. `ReportsPage.tsx:30` lee `e.water_liters`, campo inexistente, y grafica una serie permanentemente en cero. El comentario del propio código (`ReportsPage.tsx:127`) admite que el sistema legacy sí lo tenía. | `Bases Consideradas en el Desarrollo de la App Avicola.pdf`, págs. 2, 4 y 12 | `GA-REM-021` |
| **R-14** | **La Tasa de Eclosión devuelve un texto.** `get_kpi_hatchery` retorna `"hatchability_pct": "N/A (requiere datos de carga de incubación)"`, y la afirmación es falsa: `HatcheryParams.quantity_loaded` existe y ya se suma en `get_hatchery_egg_balance`. Es uno de los 5 KPI que el cliente exige para Incubadora. | `backend/app/reports/service.py:145-147` | `GA-REM-022` |
| **R-15** | **La documentación funcional del cliente nunca se ha usado para validar la implementación.** El repositorio contiene 43 documentos del negocio —incluido el documento de requerimientos original y un inventario de 30 procesos— y **ningún artefacto del proyecto los referencia**. Una lectura parcial ya produjo dos requisitos incumplidos (R-13 y R-14). | `grep -r "AVI-" specs/ docs/ backend/ frontend/src` → 0; hallazgos R-13 y R-14 | `GA-REM-020` |

### Aclaración de alcance — decisión del propietario

```
LA TAXONOMÍA DE PROCESOS DEL PROYECTO NO SE ADECÚA A LA DE PROTINAL
```

La documentación del cliente se usa **exclusivamente como fuente de validación** de procesos, procedimientos, datos, reglas y KPI. Global Avícola **conserva su propia taxonomía** (`processCatalog.ts`, 15 procesos), que sigue siendo la unidad de certificación.

Por tanto **R-15 no es bloqueante**: `GA-REM-020` informa, no condiciona. Registrado como `RA-05`.

**Validación preliminar ya realizada:** los 17 procesos del cliente dentro del alcance v1 **tienen cobertura funcional** en la implementación, con otra descomposición. No se detecta ningún proceso de negocio ausente. Los huecos encontrados son de **dato** (R-13) y de **KPI** (R-14), más un `SPEC_GAP` (`egg_storage`) y un posible hueco menor en la rotación de huevos (frecuencia y ángulo), a confirmar.

### Reclasificación derivada
| Elemento | Auditoría | Corregido | Motivo |
|---|---|---|---|
| `egg_storage` | `IMPLEMENTED_WITHOUT_SPEC` | **`SPEC_GAP`** | el cliente **sí** lo exige («Almacenamiento de Huevos: fecha, condiciones, duración»); lo que falta es la spec del proyecto |
| Condiciones de transporte | sin clasificar | requisito del cliente cubierto | exigido explícitamente e implementado |

Esto no invalida la auditoría: confirma su propia advertencia.

---

## 4. Respuestas a las diez preguntas del punto de control

### 1. ¿Cuál es el orden final?
```
 1  GA-REM-001  Gobierno                    ✅ CERTIFIED
 2  GA-REM-014  Entorno de test aislado
 3  GA-REM-020  Validación de cobertura (R-15)   ← informa, no bloquea
 4  GA-REM-004  Credenciales
 5  GA-REM-009  Evidencias
 6  GA-REM-010  Semántica SAP
 7  GA-REM-005  Mortalidad
 8  GA-REM-011  Contratos FE↔BE
 9  GA-REM-002  RBAC
10  GA-REM-003  Auth/token
11  GA-REM-007  BR-14
12  GA-REM-012  Contraseña
13  GA-REM-006  Correcciones
14  GA-REM-008  Trazabilidad
15  GA-REM-013  Quality gates
16  GA-REM-015  Tests backend
17  GA-REM-021  Agua (R-13)
18  GA-REM-022  KPI (R-14)
19  GA-REM-016  Certificación E2E y procesos
20  GA-REM-018  Trazabilidad Spec Dev
21  GA-REM-017  SAP real            BLOCKED_EXTERNAL
22  GA-REM-019  Deuda P2/P3         DEFERRED
```
Tres ajustes respecto al orden conceptual del encargo, justificados en `DEPENDENCY_MAP.md §6`: `014` se adelanta por delante de las specs de Fase C (sin él sus AC no se pueden cerrar), `020` se ejecuta temprano **sin bloquear** (riesgo nulo y puede revelar más huecos antes de comprometer el alcance), y `012` se agrupa en la Fase B.

### 2. ¿Qué dependencias existen?
Dos bloqueantes absolutas: `001` habilita todo (ya cerrada) y `014` habilita el cierre de 11 specs. `020` **informa** a `016`, `021` y `022` sin bloquearlas. El resto son funcionales, detalladas en `DEPENDENCY_MAP.md §2`.

### 3. ¿Qué se puede trabajar en paralelo?
Cuatro vías desde el primer día:
- **V1 habilitante**: `014`
- **V1b validación documental** (riesgo nulo, sin tocar código): `020`
- **V2 riesgo activo**: `004` · `009` · `010` — no dependen de `014`; reducen daño que se produce ahora
- **V3 contratos**: `011`
- **V4 proceso**: `013` (su gate de backend espera a `014`)

### 4. ¿Qué está bloqueado?
| Bloqueo | Naturaleza | Afecta |
|---|---|---|
| `GA-REM-017` SAP real | **externo**: sin contrato técnico, endpoint, autenticación ni credenciales | 1 spec |
| Confirmación del resultado de `020` con el negocio | deseable, **no bloqueante** | `020` |
| `RC-01` … `RC-05` | **decisión de negocio**, no trabajo técnico | `005` (parcial), `006`, `007`, `008`, `012` |

### 5. ¿Qué specs están listas?
**15 en `SPEC_READY`**: `002, 003, 004, 005, 009, 010, 011, 012, 013, 018, 020, 021, 022` + `014` + `007`.
De ellas, **7 pueden ejecutarse hoy sin ninguna decisión pendiente**: `014`, `020`, `004`, `009`, `010`, `011`, `021`.

### 6. ¿Qué specs necesitan investigación adicional?
| Spec | Falta |
|---|---|
| `006` Correcciones | resolver `RC-01` (¿corrección inmediata o con aprobación?) + mapa de campos corregibles |
| `008` Trazabilidad | resolver `RC-04` (ambigüedad de `spec.md §4.9`) |
| `015` Tests backend | su contenido depende del resultado de la primera ejecución |
| `016` Certificación | depende de siete specs previas; `020` le aporta la columna de cobertura validada |
| `017` SAP real | contrato técnico del cliente |

### 7. ¿Qué cambios de base de datos podrían requerirse?
| Spec | Cambio | Certeza |
|---|---|---|
| `021` Agua | columna de consumo de agua | **alta** |
| `003` Auth | tabla de tokens revocados | media — hay alternativa sin esquema |
| `005` Mortalidad | columnas de umbral de alerta por compañía | media |
| `008` Trazabilidad | campo de identificador de despacho | media — podría reutilizarse `extra_data` |
| `010` Semántica SAP | valor nuevo en el enum de estados | media — hay alternativa sin migración |
| `006` Correcciones | identificador de submovimiento destino | baja |
| `002` RBAC · `004` · `009` · `011` · `012` · `013` · `014` | **ninguno** | alta |

Todas seguirán el Art. 19: migración Alembic formal, docstring citando la `GA-REM`, y verificación de que la deriva sigue en cero.

### 8. ¿Qué integraciones externas bloquean trabajo?
Solo **SAP**. Falta: mecanismo (OData/SOAP/IDoc/RFC), URL, autenticación, estructura de payload y respuesta, credenciales, catálogo de tipos de movimiento y política de reintentos acordada. El PDF disponible describe el proceso de negocio, **no el contrato técnico**.

Telegram, Docker Hub y PostgreSQL están configurados y no bloquean. SMTP está declarado y sin usar; no bloquea nada en este ciclo.

### 9. ¿Qué procesos podrán certificarse primero?
Sobre la **taxonomía propia del proyecto**, con orden derivado del dominio (`GA-REM-016`):
1. **Recepción de aves** — alimenta el inventario de todos los demás
2. **Control de producción diario** — mayor frecuencia operativa; depende de `GA-REM-005`
3. **Revisión → Corrección → Aprobación** — diferenciador del producto; depende de `006` y `007`

El primero realista tras cerrar las specs habilitantes es el **control de producción diario**, porque su bloqueador (P0-1) tiene complejidad XS.

### 10. ¿Qué código debe mantenerse intacto?
Los 11 componentes protegidos del programa maestro §10: modelo de datos y migraciones (0 deriva sobre 47 tablas, 1 head), modelo unificado `OperationalEvent`, adapter pattern de SAP, idempotencia y bitácora SAP, validadores de reglas (salvo BR-06), i18n (865/865), cabeceras de seguridad y validación de arranque, ausencia de SQL crudo, `processCatalog.ts` (**no se modifica** — `RA-05`), estructura modular del backend y el tipado del frontend.

---

## 5. Verificación del alcance excluido

```
DEPLOYMENT AUTOMÁTICO = KNOWN_ACCEPTED_RISK = OUT_OF_SCOPE = NO MODIFICAR
```

| Verificación | Resultado |
|---|---|
| Archivos de `.github/workflows/` modificados en esta ejecución | **0** |
| `docker-compose.yml` modificado | **no** |
| Watchtower, `pull_policy`, etiqueta `:latest` | **intactos** |
| GA-REM que proponen tocar el deployment | **ninguna** |
| GA-REM con AC que verifica explícitamente que el deployment sigue intacto | **4** — `004` AC04, `009` AC06, `010` AC09, `013` AC07 |
| Registro en la constitución | `EX-01`, con sus 3 limitaciones derivadas y sin proponer corrección |

`GA-REM-013` está redactada con una restricción vinculante en su encabezado y un AC dedicado a verificar que no se ha tocado el despliegue.

---

## 6. Conflictos de requerimiento abiertos

Conforme al Art. 18 de la constitución, **no se desarrolla hasta determinar la regla vigente**.

| ID | Conflicto | Fuentes en conflicto | Bloquea | Quién decide |
|---|---|---|---|---|
| ~~`RC-01`~~ | ¿La corrección se aplica de inmediato o requiere aprobación? | **RESUELTO** (`RR-01`): cliente §17/§18/§26, `docs/12`, `spec.md:29` y el código dicen lo mismo. Era una omisión de `spec.md §4.10`, no un conflicto | — | — |
| ~~`RC-02`~~ | Semántica de `bird_transfer` en el balance de aves | **RESUELTO** (`RR-02`): `BirdMovement` declara galpón origen y destino, y el esquema **no tiene ningún campo de lote destino** — es incapaz de expresar la alternativa | — | — |
| ~~`RC-03`~~ | ¿BR-14 es absoluta o configurable? | **RESUELTO** (`RR-03`): el cliente calla; `docs/02:554` y `docs/12:139` dicen configurable, dos veces; el esquema ya tiene `require_segregation` con `default=True` | — | — |
| `RC-04` | «para el mismo lote de huevos» en `spec.md §4.9` | la redacción ambigua es la que produjo el defecto de trazabilidad | `GA-REM-008` | **corrección de spec** |
| ~~`RC-05`~~ | Política de complejidad de contraseñas | **RESUELTO** (`RR-05`): conflicto aparente — los números se aplican a operaciones distintas. Única política: `min_length=8` en el alta. La complejidad queda como `OD-01`, no bloqueante | — | — |
| **`RC-07`** | Política de mortalidad frente a SAP | el cliente §25.4 la declara **pendiente de decisión de la empresa** | solo el mapeo SAP en `GA-REM-017` | **propietario** (`OD-02`) |
| ~~`RC-06`~~ | ~~¿El «Desalojo» es un proceso certificable?~~ | **CERRADO** — desaparece con la decisión del propietario: no se adopta la granularidad del cliente. La validación preliminar confirma que el desalojo está cubierto funcionalmente por `bird_exit` y `lot_closure` | — | — |

**Actualizado tras Wave 1.5:** cuatro de los seis conflictos se resolvieron por evidencia, sin necesidad de ninguna decisión de negocio. Solo quedan `RC-04` (corrección de redacción de la spec) y `RC-07` (decisión contable del propietario, acotada al mapeo SAP). `RC-06` cerrado en Wave 1 por `RA-05`. Detalle completo en `REQUIREMENT_CONFLICT_RESOLUTION.md` y `RC_RESOLUTION_REPORT.md`.

---

## 7. Estado del programa

```
Estado tras Wave 1.5 (2026-09-03)

GA-REM creadas .................... 23   (+GA-REM-023)
CERTIFIED .........................  8   (001, 004, 009, 010, 013, 014, 015, 020)
PARTIALLY CERTIFIED ...............  1   (011)
SPEC_READY ........................ 11
SPEC_DRAFT ........................  2   (008, 016)
BLOCKED_EXTERNAL ..................  1   (017)
DEFERRED ..........................  1   (019)

Ejecutables hoy sin decisión ...... 11   (023, 005, 002, 003, 012, 006, 007, 011, 018, 021, 022)
Esperando decisión de negocio .....  0   (RC-07 acotado: solo el mapeo SAP de 017)
Esperando corrección de spec ......  1   (008 · RC-04)
Esperando al cliente ..............  1   (017 · contrato técnico SAP)

Bloqueadores P0 con spec .......... 10 / 10
Riesgos P1 con destino ............ 16 / 16
Requirement conflicts abiertos ....  2   (RC-04 técnico · RC-07 acotado)
```

---

## ESTADO

# READY

**Justificación.** Existe constitución ratificada y vinculante; los 12 bloqueadores están revalidados contra el código actual con cero falsos positivos; los 15 hallazgos bloqueantes tienen spec asignada; el orden está derivado de dependencias reales y no del número de spec; hay siete specs ejecutables de inmediato sin ninguna decisión pendiente; el alcance excluido está registrado en la constitución y verificado con AC dedicados en cuatro specs; y los cinco conflictos de requerimiento vigentes están abiertos formalmente en lugar de resueltos en silencio.

**Primera spec lista para implementación: `GA-REM-014` — Entorno de test backend aislado.**
Es el habilitante de mayor alcance: desbloquea el cierre de once specs y elimina el riesgo, hoy real, de que una sesión de pruebas escriba en la base de datos de producción.
