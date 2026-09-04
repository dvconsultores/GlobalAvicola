# GLOBAL AVÍCOLA — FUNCTIONAL BASELINE V1.1

| | |
|---|---|
| **Versión** | 1.1 |
| **Fecha de congelamiento** | 2026-09-03 |
| **Commit base** | `bfccdfb` |
| **Origen** | `GA-REM-020` `CERTIFIED` (Wave 1) |
| **Estado** | 🔒 **FROZEN** |
| **Supersede a** | `specs/global-avicola/spec.md` @ `cd64a17` + `docs/02-functional-spec.md` como **referencia funcional operativa** |

---

## 🔒 REGLA DE CONGELAMIENTO

A partir de este punto **no se agregan requisitos durante una remediación**, salvo evidencia nueva realmente material.

Todo descubrimiento posterior se registra como:

```
NEW_REQUIREMENT_DISCOVERY
```

en `audit/remediation/REMEDIATION_BACKLOG.md`, para evaluación separada. **Prohibido expandir silenciosamente la spec activa** (Art. 15 de la Constitución).

---

## A. Requerimientos vigentes

**60 requerimientos.** Los 56 reconstruidos por la auditoría (`GA-REQ-001` … `056`) más 4 derivados de la validación de `GA-REM-020`.

| Bloque | IDs | Origen |
|---|---|---|
| Auth y usuarios | `GA-REQ-001` … `006` | `spec.md §4.1`, `docs/02 §3.1` |
| Maestros | `GA-REQ-007` … `008` | `spec.md §4.2` |
| SAP | `GA-REQ-009` … `014` | `spec.md §4.3`, `docs/10`, `Recomendación central` |
| Progenitoras | `GA-REQ-015` … `016` | `spec.md §4.4` |
| Reproductoras | `GA-REQ-017` … `019` | `spec.md §4.5`/`§4.6` |
| Incubadora | `GA-REQ-020` | `spec.md §4.7` |
| Engorde | `GA-REQ-021` | `spec.md §4.8` |
| Lotes | `GA-REQ-022` … `023` | `spec.md §4.9` |
| Revisión y aprobación | `GA-REQ-024` … `029` | `spec.md §4.10`, `docs/12` |
| Auditoría | `GA-REQ-030` … `031` | `spec.md §4.11`, `docs/13` |
| Reportes y KPI | `GA-REQ-032` … `034` | `spec.md §4.12`, `Bases Consideradas` |
| Dashboard | `GA-REQ-035` … `036` | `docs/02 §3.13` |
| Alertas | `GA-REQ-037` … `038` | `docs/02 §3.14`, `Recomendación central §7` |
| Trazabilidad | `GA-REQ-039` … `040` | `spec.md §4.9` (2ª) |
| Evidencias | `GA-REQ-041` | `Recomendación central §2` |
| Reglas de negocio | `GA-REQ-042` … `052` | `spec.md §5` BR-01…BR-16 |
| NFR | `GA-REQ-053` … `056` | `spec.md §7`, `docs/07`/`08`/`09` |
| **Nuevos (V1.1)** | **`GA-REQ-057` … `060`** | **`GA-REM-020`** |

### Requerimientos nuevos incorporados en V1.1

| ID | Requerimiento | Fuente | Justificación |
|---|---|---|---|
| **GA-REQ-057** | Registro de consumo diario de agua en Reproductora Cría, Reproductora Producción y Engorde | `Bases Consideradas` p.2, 4, 12 | figura en «Datos Diarios a Registrar»; el sistema anterior lo tenía (`ReportsPage.tsx:127`) |
| **GA-REQ-058** | Rotación de huevos en incubación con **frecuencia y ángulo** | `Bases Consideradas` p.8 | figura en «Datos Diarios a Registrar → Incubación», no en anexo técnico |
| **GA-REQ-059** | Identificador de transacción externa hacia SAP: `external_transaction_id`, `source_system`, `sap_reference_document`, `sap_reference_item` | `Recomendación central §19` | declarado **campo obligatorio para evitar duplicados**; el modelo ya lo previó |
| **GA-REQ-060** | Bandera de riesgo manual en la inspección de granja | `Recomendación central §7` | listada entre los datos que la app debe capturar |

**No se incorporaron como requerimientos**: los manuales Ross/Cobb (referencia técnica), el contexto de negocio del PDF de compra de reproductoras, los 30 formatos vacíos (`RA-04`) ni la funcionalidad legacy no verificable.

---

## B. Requerimientos cubiertos

**Cobertura E2E verificada: 12 / 60 = 20,0 %** *(el denominador crece de 56 a 60; el numerador no cambia — ver §14 del informe de Wave 1)*

`GA-REQ-001` login y refresh · `011` consolidación · `026` devolución al operador · `027` aprobación y rechazo · `034` exportación Excel/PDF · `043` BR-02 · `044` BR-03 · `045` BR-04 · `048` BR-07 · `049` BR-08 · `053` i18n · `054` mobile-first y web.

Además, **57 elementos funcionales del cliente** verificados como `COVERED` en `FUNCTIONAL_COVERAGE_MATRIX.md`, incluidas las 6 prohibiciones arquitectónicas que la app respeta.

---

## C. Requerimientos parciales

**28 requerimientos.** Los más relevantes por bloqueo:

| Req | Bloqueado por |
|---|---|
| `GA-REQ-016, 018, 019, 021` operaciones de las 4 etapas | **P0-1** mortalidad |
| `GA-REQ-005` multi-compañía | `S-03` fuga + Super Admin ciego |
| `GA-REQ-008` UI de maestros | 405 en 8 catálogos |
| `GA-REQ-024` bandeja de revisión | filtros inertes |
| `GA-REQ-029` BR-14 | eludible |
| `GA-REQ-030, 031` auditoría | doble escritura, filtros inertes |
| `GA-REQ-032, 033, 035, 036` KPI y dashboard | **R-17**: 12 KPI parciales |
| `GA-REQ-037` alertas | generador de mortalidad roto |
| `GA-REQ-040` árbol de trazabilidad | pantalla rota |
| `GA-REQ-041` evidencias | sin persistencia |
| `GA-REQ-009, 010, 012` SAP | adaptador simulado |
| `GA-REQ-050, 051` BR-10, BR-11 | `sap_document_ref` nunca enviado |

---

## D. Requerimientos ausentes

| Req | Estado |
|---|---|
| `GA-REQ-002` RBAC granular | modelo poblado, **cero enforcement** |
| `GA-REQ-006` recuperación de contraseña, MFA, revocación | ningún endpoint |
| `GA-REQ-038` notificaciones (6 tipos) | ningún canal |
| `GA-REQ-052` BR-16 reverso post-SAP | tabla `reversals` huérfana |
| `GA-REQ-056` cobertura de tests >80/70 % | ~4 % frontend |
| **`GA-REQ-057`** consumo de agua | **ningún campo** |
| **`GA-REQ-058`** rotación con frecuencia y ángulo | solo booleano |
| **`GA-REQ-059`** identificador de transacción externa | campos declarados, **nunca poblados** |
| **`GA-REQ-060`** bandera de riesgo manual | no existe |

**Rotos (7):** `GA-REQ-003` usuarios · `013` referencia SAP en el evento · `014` comparativo SAP · `025` corrección auditada · `039` trazabilidad automática · `042` BR-01 · `047` BR-06.

---

## E. SPEC_GAPS

Requisitos del cliente **implementados correctamente** y sin spec del proyecto que los autorice. **No requieren cambio de código**; requieren spec (`GA-REM-018`).

| Elemento | Fuente del cliente | Implementación |
|---|---|---|
| `egg_storage` — almacenamiento de huevos con fecha, condiciones y duración | `Bases Consideradas` p.8 · `Recomendación central §11` | `operations/models.py:231-247`, migración `4396a2b7e7d6` — **correcta**; falta exponer la lectura |
| Condiciones de transporte en recepciones y despachos | `Bases Consideradas` p.6, 8 · `Recomendación central §6` | `extra_data.transport_*` — **correcta** |
| Inspección por galpón con ítems de equipo | `Recomendación central §7` | `inspection_details` + commit `e156a6e` — **correcta** |
| Evidencias adjuntas | `Recomendación central §2` | `evidences` — correcta, sin persistencia (`GA-REM-009`) |
| Motor de alertas / banderas operativas | `Recomendación central §2, §7` | `operational_alerts` — parcial |

---

## F. Requirement conflicts

| ID | Conflicto | Bloquea | Decide |
|---|---|---|---|
| `RC-01` | ¿Corrección inmediata o sujeta a aprobación? | `GA-REM-006` | negocio |
| `RC-02` | Semántica de `bird_transfer` en el balance de aves | `GA-REM-005` (parcial) | negocio |
| `RC-03` | ¿BR-14 absoluta o configurable? | `GA-REM-007` | negocio |
| `RC-04` | «el mismo lote de huevos» en `spec.md §4.9` | `GA-REM-008` | corrección de spec |
| `RC-05` | Política de complejidad de contraseñas (8 vs 6 vs seeds) | `GA-REM-012` | negocio |
| **`RC-07`** | **Política de mortalidad frente a SAP**: el cliente presenta 3 políticas excluyentes y exige elegir una; no hay decisión registrada | `GA-REM-017` | **negocio** |

`RC-06` cerrado por `RA-05`.

---

## G. Out of scope

| Elemento | Motivo | Registro |
|---|---|---|
| Cadena LIVIANAS / Ponedoras — 13 procesos `AVI-REP-LIV-*`, `AVI-INC-PON-03`, `AVI-GRA-PON-*` | declarado en `spec.md §9` | `RA-03` |
| Adopción de la taxonomía y códigos `AVI-*` de PROTINAL | decisión del propietario | **`RA-05`** |
| Modificación del despliegue automático, Watchtower, `:latest`, triggers | decisión del propietario | **`EX-01`** |
| 6 reglas de validación que exigen maestros e inventario de SAP (`CV-R03, 04, 06, 07, 09, 11, 12`) | dependen de integración real | `GA-REM-017` `BLOCKED_EXTERNAL` |
| Reemplazar SAP como sistema contable · app nativa · nómina · ML/IA · IoT · push | `spec.md §9` | — |

---

## H. Referencias técnicas no funcionales

**No generan requerimientos.** Se conservan como fuente de calibración.

| Referencia | Uso actual |
|---|---|
| Manuales Ross 308 / Cobb 500 / Ross GP / Cobb Breeder | `thermalCurves.ts` — curvas de temperatura y humedad por semana |
| Rangos de incubadora y nacedora | `OperationFormPage.tsx:22-25` |
| `Sap y App Proceso Avícola Software primera version.pdf` | contexto de negocio: razas, criterios de selección de proveedores, documentación sanitaria |
| `Incubadora.pdf`, `suplement macho cobb.pdf` | procedimientos operativos de referencia |
| 30 formatos `AVI-*.xlsx` | **plantillas vacías** — `RA-04`, sin contenido explotable |
| Capturas del sistema legacy | `NOT_VERIFIABLE` — imágenes sin texto |

**Excepción:** `CV-T06` (curva de peso estándar) sí es hallazgo (`R-18`) porque `spec.md §4.5` exige la alerta por peso fuera de curva.

---

## I. Procesos cubiertos

Sobre la **taxonomía propia del proyecto** (`processCatalog.ts`), validada contra la lista de comprobación del cliente:

| Proceso del proyecto | Cobertura funcional | Procesos del cliente que satisface |
|---|---|---|
| Progenitoras — Cría | `COVERED` salvo ciclo diario | `AVI-ABU-PES-01`, `03` |
| Progenitoras — Producción | `COVERED` | `AVI-ABU-PES-04`, `05`, `06` |
| Reproductoras — Cría | `COVERED` salvo ciclo diario | `AVI-REP-PES-01`, `03` |
| Reproductoras — Producción | `COVERED` | `AVI-REP-PES-04`, `05`, `06` |
| Incubación | `COVERED` salvo trazabilidad | `AVI-INC-REP-01`, `AVI-INC-ENG-02` |
| Engorde | `COVERED` salvo ciclo diario | `AVI-GRA-ENG-01`, `03` |
| Revisión → Corrección → Aprobación | 8 de 10 pasos | transversal |
| Consolidación y preparación SAP | 5 de 6 pasos | transversal |
| Gestión de maestros | 12 de 19 catálogos con UI | transversal |

**Ningún proceso de negocio del cliente está ausente.**

---

## J. Procesos con gaps internos

| Proceso | Gap | Bloqueado por |
|---|---|---|
| Control de producción diario (4 etapas) | mortalidad → 500 | **P0-1** `GA-REM-005` |
| Revisión → Corrección → Aprobación | la corrección no aplica el valor · BR-14 eludible · 2 pantallas caídas | **P0-2, P0-5, P0-10** |
| Trazabilidad generacional | emparejamiento auto-referencial | **P0-11** `GA-REM-008` |
| Consolidación → SAP | envío simulado · identificadores externos nunca poblados | **P0-7**, `R-21` |
| Gestión de usuarios y roles | pantalla caída · sin UI de roles ni permisos | **P0-5**, `GA-REQ-002` |
| Gestión de maestros | 405 en 8 catálogos · 7 sin UI · total de paginación incorrecto | `GA-REM-011` |
| Reportes y KPI | 12 de 18 KPI del cliente `PARTIAL` | **R-17** `GA-REM-022` |
| Activación manual de lotes | endpoint sin interfaz | backlog |
| Notificaciones | inexistentes | `GA-REQ-038` |

---

## Métricas del baseline

```
Requerimientos vigentes .................. 60   (56 auditados + 4 de V1.1)
  Cubiertos E2E ..........................  12   (20,0 %)
  Parciales ..............................  28
  Rotos ..................................   7
  Ausentes ...............................  13
  No verificables ........................   1  (compatibilidad de navegadores)

Elementos funcionales del cliente validados  96
  COVERED ................................  57   (59 %)
  PARTIAL ................................  25
  ABSENT .................................   5
  OUT_OF_SCOPE ...........................   6  + 13 procesos LIVIANAS
  NOT_VERIFIABLE .........................   2

Procesos del cliente en alcance ..........  17
  Con cobertura funcional ................  17   (12 completos · 5 parciales)
  Ausentes ...............................   0

Requirement conflicts abiertos ...........   6   (RC-01…05, RC-07)
SPEC_GAPS ................................   5
Riesgos aceptados ........................   5   (EX-01, RA-01…05)
```

---

## Trazabilidad del baseline

```
DOCUMENTACIÓN DEL CLIENTE  →  FUNCTIONAL_COVERAGE_MATRIX  →  BASELINE V1.1
        (96 elementos)              (GA-REM-020)              (60 GA-REQ)
                                          ↓
                                   10 hallazgos → backlog / specs
```

**Este documento es la referencia funcional para las siguientes Waves.**
