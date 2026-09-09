# MATRIZ DE AUTORIDAD DOCUMENTAL Y SUPERSESIÓN

**Auditoría 360°** · 2026-09-09 · base `7310adb` (`main`) · **AUDIT ONLY** — ningún archivo de
`backend/`, `frontend/`, `specs/`, `alembic/` ni `e2e/` fue modificado.

Responde dos preguntas: **qué documento manda sobre cada tema** y **qué documento ha dejado de
describir la realidad** sin que nadie lo haya marcado. La jerarquía aplicada es la de
`REQUIREMENT_CONFLICT_RESOLUTION.md §1` y `constitution.md` Principio V; no se altera aquí.

```
1 DECISIÓN DEL PROPIETARIO  >  2 REQUERIMIENTO DEL CLIENTE  >  3 DOCUMENTO DE PROCESO
>  4 SPEC VIGENTE  >  5 IMPLEMENTACIÓN  >  6 LEGADO  ·  REFERENCIA DE DOMINIO (fuera de la cadena)
```

---

## 1. Fuentes, nivel y estado de vigencia

| Nivel | Fuente | Contenido normativo | Vigencia | Observación |
|:--:|---|---|---|---|
| 1 | `specs/remediation/OD-09…OD-15` (7 archivos) | plano de control vs unidad, contrato de traspaso, empresa efectiva, transversalidad SAP, tenencia de roles, control global vs contexto, segregación de accesos | **VIGENTES** | `OD-04`, `OD-06`, `OD-08` se citan en código y matrices pero **no tienen archivo propio** en `specs/remediation/` (se resolvieron dentro de `MASTER_REMEDIATION_MATRIX §10/§12` y `GA-REM-038`). Registro **disperso** → `H360-D01` |
| 1 | `RA-04`, `RA-05` | plantillas AVI-* vacías no se infieren · la documentación del cliente es fuente de validación, no estructura a adoptar | VIGENTES | solo citadas en `FUNCTIONAL_COVERAGE_MATRIX`; sin registro propio |
| 2 | `Recomendación central.pdf` (29 pág.) | §1 dueño SAP por objeto · §2 funciones permitidas/prohibidas · §6–§13 datos por proceso · §15/§16 qué consume y qué envía · **§17 17 reglas** · **§18 11 estados** · §19 id externo · §24 matriz de gobierno · **§25 5 decisiones** | VIGENTE — requerimiento del cliente | Leída íntegra en esta auditoría (pág. 1–29) |
| 2 | `Bases Consideradas en el Desarrollo de la App Avicola.pdf` (13 pág.) | datos diarios y **fórmulas KPI** por etapa: cría (4), producción (6), traslado (5), incubadora (5), engorde (6) | VIGENTE — requerimiento original | Leída íntegra. Es la **única** fuente con fórmulas explícitas → gobierna `KPI_FORMULA_AND_DATA_SOURCE_MATRIX` |
| 2/6 | `Sap y App Proceso Avícola Software primera version.pdf` (34 pág.) | pág. 1–2 y 13–15: contexto de compra y pasos de OC **en SAP** · pág. 3–12: tablas Cobb (dominio) · **pág. 16–24: pantallas de la app anterior** («Segundo que registro en la App», inspección, recepción/distribución, alimento por OT, pesaje, mortalidad, vacunas) · pág. 25–34: manejo de postura, incubación, engorde | **MIXTA**: contexto (2) + **legado** (6) + dominio | `FUNCTIONAL_COVERAGE_MATRIX §0` la clasificó como «contexto, no requisitos». **Precisión de esta auditoría:** las pág. 16–24 son capturas del sistema anterior y valen como **nivel 6 (legado)**; la pág. 16 muestra el campo **«Id SAP» en el maestro de lotes**, que la app vigente no tiene → `H360-S05` |
| — | `PolloEngordeRoss/Cobb`, `ReproductoraRoss/Cobb`, `suplement macho cobb`, tablas Cobb del PDF anterior, `Incubadora.pdf` | curvas objetivo, consumos, temperaturas | **REFERENCIA DE DOMINIO** | No son fuente de requisito (regla del encargo). Sirven para poblar `genetic_weight_curves` y para sanidad de umbrales, nunca para certificar |
| — | `Sistema avicola administrativo - capture pantallas.pdf`, `App mobile … .docx` | pantallas legadas sin texto | `NOT_VERIFIABLE` | sin cambio desde `GA-REM-020` |
| 3 | `docs/02-functional-spec.md` | módulos, §4 estados, §5 R1–R16, §6 roles, §7 móvil | VIGENTE | §3.1.4 «Super Admin ve todas las compañías» precisado por `OD-14` |
| 3 | `docs/12-approval-workflow.md` | §4 13 estados con actor · §6 R1–R9 · §10 consolidación | VIGENTE | §4 fila 8: «Rechazado → Operador reenvía (corregido)» **no está implementado** → `H360-P03` |
| 3 | `docs/13-audit-strategy.md` | qué se audita, inmutabilidad, retención | VIGENTE | inmutabilidad es **de aplicación** (listeners), no de base de datos: no hay trigger ni regla en `alembic/versions` → `H360-D04` |
| 3 | `docs/10-sap-integration-strategy.md` | adaptador, §5 idempotencia, **§6.2 reintentos 1/5/15 min**, §12 AC SAP | VIGENTE | §6.2 diverge del código (`sap/service.py:373` fija 1 min) → `H360-S07` |
| 3 | `docs/16-audit-recomendacion-central.md` | auditoría de la Recomendación al 62 % (fecha original) | **PARCIALMENTE SUPERADO** | ver §3: 9 de sus 16 gaps ya no describen el código |
| 4 | `specs/global-avicola/spec.md` | §4 dominios · **§5 BR-01…BR-16** · §8 AC MVP · §9 fuera de alcance · §14 flags | VIGENTE | §14 remite tres veces a `docs/17-production-checklist.md`, **que no existe** → `H360-D02`. `BR-17`, `BR-18`, `BR-19` existen en código (`validators.py:404,419,485`) y **no** en §5 → `H360-D03` |
| 4 | `specs/global-avicola/data-model.md` | `Company.sap_config: JSON` (línea 12) | VIGENTE | la migración `b53bbe02a476` creó `sa.String()` → raíz de `R-127` |
| 4 | `.specify/memory/constitution.md` 1.0.0 | principios, artículos, `EX-01` | VIGENTE | sin cambios |
| 4 | `specs/remediation/INDEX.md` | estado de las 40 `GA-REM` | **DESACTUALIZADO** | ver §2 |
| 5 | código en `7310adb` | — | evidencia | 208 rutas, 54 tablas, `EventStatus` 13 estados, `EventType` 26 tipos |

---

## 2. Deriva del registro de estado (`INDEX.md` vs informes de certificación)

`INDEX.md` es el único índice de estado de las specs y **contradice a los informes que él mismo
enlaza**. Se comprobó el veredicto textual de los 17 informes `*-CERTIFICATION-REPORT.md`:

| Spec | `INDEX.md` dice | El informe de certificación dice | Clase |
|---|---|---|---|
| `GA-REM-004` | `SPEC_READY` | `CERTIFIED` | deriva |
| `GA-REM-009` | `SPEC_READY` (P0 «pérdida de datos activa») | `CERTIFIED` — volumen `avicola-media` en `/app/media` | deriva **con severidad falsa**: un lector del índice cree abierto un P0 cerrado |
| `GA-REM-010` | `SPEC_READY` (P0) | `CERTIFIED` — AC01…AC06 ✅ | ídem |
| `GA-REM-011` | `SPEC_READY` | `PARTIALLY CERTIFIED` | deriva |
| `GA-REM-013` | `SPEC_READY` | `CERTIFIED` | deriva |
| `GA-REM-020` | `SPEC_READY` | `CERTIFIED` | deriva |
| `GA-REM-022` | `SPEC_READY` | `MASTER_REMEDIATION_MATRIX §7`: enmienda A → `P-15` certificado | deriva |
| `GA-REM-040` | `SPEC_READY ⚠ fase 7/11` | fases 7 y 8 cerradas (`GA_REM_040_PHASE_8_EVIDENCE.md`) | deriva |
| `GA-REM-002` | `IMPLEMENTED ⚠ R-44` | `GA-REM-002-003-CERTIFICATION-REPORT.md`: `CERTIFIED`; enmienda B (AC13–AC16) certificada en `USER_TENANT_ISOLATION_P0_EVIDENCE.md` | deriva |
| `GA-REM-024` | `IMPLEMENTED ⚠ R-58` | `CERTIFIED` | deriva |
| `GA-REM-016` | `SPEC_DRAFT` | 15 informes `PROCESS-xx-CERTIFICATION.md` lo citan como marco | la spec marco de certificación sigue en borrador mientras se certifica con ella → `H360-D05` |

`MASTER_REMEDIATION_MATRIX.md` no corrige esto: desde §4 es un **diario cronológico de addenda**
(§4…§12+) y no una matriz consolidada. **No existe hoy un único documento con el estado real de
las 40 specs.** Esta auditoría lo reconstruye en `MASTER_PROGRAM_STATUS_RECONCILIATION.md §2`.

---

## 3. Supersesión de `docs/16` (gaps G-R01…G-R16) — verificada contra el código

| Gap docs/16 | Decía | Hoy (`7310adb`) | Estado del gap |
|---|---|---|---|
| G-R01 cliente OData | ❌ | `adapter.py`: `ManualSapAdapter`, `MockSapAdapter`; `SAP_ADAPTER=real` → `NO IMPLEMENTADO (GA-REM-017)` | **VIGENTE** · `BLOCKED_EXTERNAL` |
| G-R02 5 decisiones | ❌ | ninguna `OD` las resuelve; `RC-07` sigue `OWNER_DECISION_REQUIRED` | **VIGENTE** → `AOD-01…05` |
| G-R03 `external_transaction_id` | ❌ | `sap/models.py:144-146` columnas; `service.py:337` la puebla | **SUPERADO** |
| G-R04 capacidad galpón | ❌ | `validate_house_capacity` `BR-17` (`validators.py:403`) | **SUPERADO** |
| G-R05 cantidad ≤ OC | ❌ | `validate_oc_limit` `BR-18` acumulado (`validators.py:419`, `OD-04`) | **SUPERADO** |
| G-R06 evidencias | ❌ | tabla `evidences`, 4 rutas, volumen (`GA-REM-009`) | **SUPERADO** (obligatoriedad no: `H360-B04`) |
| G-R07 alertas | ❌ | `operational_alerts`; `high_mortality`, `temperature_out_of_range`, `humidity_out_of_range`, `weight_deviation` | **SUPERADO** |
| G-R08 consulta inventario SAP | ❌ | sin cambio | **VIGENTE** · `SAP_DEFERRED` |
| G-R09 reverso | ❌ | tabla `reversals` (`operations/models.py:328`) **sin servicio ni ruta** (0 usos fuera del modelo) | **VIGENTE** — modelo huérfano → `H360-P05` |
| G-R10 conciliación | ❌ | `GET /reports/sap-comparison` lista eventos con `sap_document_ref` por estado; **no compara contra SAP** | **VIGENTE** (renombrado) |
| G-R11 equipos PM/EAM | ❌ | sin modelo de equipos | **VIGENTE** · `SAP_DEFERRED` |
| G-R12 período fiscal | ❌ | `validate_period_open` `BR-19`: **90 días fijos** (`validators.py:485`) | **SUSTITUIDO POR PLACEHOLDER** → `H360-S06` |
| G-R13 `REPROCESADO` | ❌ | `EventStatus` sin ese valor; `RETRYING` existe solo en `PayloadStatus` | **VIGENTE** |
| G-R14 `sap_reference_item` | ❌ | `sap_payloads.sap_reference_item` existe; **no se puebla** desde el evento | **PARCIAL** |
| G-R15 `sample_size` | ❌ | `operational_events.sample_size` (`models.py:122`) | **SUPERADO** |
| G-R16 `method` vacunas | ❌ | `vaccination_route` existe; medicación sin método | **PARCIAL** |

`docs/16` conserva valor como **inventario de la Recomendación** (§1–§5, §7, §8 tablas de
correspondencia) y debe leerse con esta tabla al lado. No se propone tocarlo.

---

## 4. Conflictos documentales detectados (no se eligen; se registran)

| ID | Fuentes en conflicto | Conflicto | Resolución posible por evidencia | Salida |
|---|---|---|---|---|
| `H360-D06` | Recomendación §1/§15 («Centros/plantas/**granjas** → SAP», «Galpones → PM/EAM/custom», «Capacidad → SAP/custom») **vs** `docs/02 §3.2.1` («Empresas y Granjas: catálogos base locales») | dueño de granjas, galpones y capacidad | **No**: nivel 2 y nivel 3 discrepan y el nivel 1 calla | `REQUIREMENT_CONFLICT` · ya registrado como `R-124` · `AOD-06` |
| `H360-D07` | Recomendación §15 («Usuarios autorizados → SAP/IAM») **vs** `docs/02 §3.1` y `OD-13` (identidad y roles locales) | fuente de identidad | **No** para producción; para el entorno compartido (`ENV-01`) la identidad local es la única existente | `REQUIREMENT_CONFLICT` · `AOD-07` |
| `H360-D08` | Recomendación §13/§21 («Liquidación/**cierre del lote** → SAP») **vs** `spec.md BR-05`, `GA-REM-029` (`POST /lots/{id}/close` cierra el lote en la app) | semántica de «cierre» | **Parcial**: la Recomendación distingue «datos de cierre del lote» (app captura) de «liquidación» (SAP). El código no declara cuál de los dos es `status=closed` | `REQUIREMENT_CONFLICT` terminológico · `AOD-08` |
| `H360-D09` | `docs/12 §4` fila 8 («Rechazado → Operador reenvía») **vs** `corrections/service.py:34` (corregibles: `REGISTERED, PENDING_REVIEW, IN_REVIEW, RETURNED`) y `service.py:893` (`submit` desde `DRAFT, REGISTERED, RETURNED`) | ¿`REJECTED` es terminal? | **No**: el nivel 3 dice una cosa y el nivel 5 hace otra; la spec (4) calla | `REQUIREMENT_CONFLICT` · `AOD-09` |
| `H360-D10` | Bases p.5 (fertilidad = fértiles / **puestos**) **vs** Bases p.8 (fertilidad = fértiles / **recogidos**) **vs** `reports/service.py:179-183` (fértiles / recibidos en incubadora) | denominador de fertilidad | **No**: el propio cliente da dos denominadores según proceso; el código usa un tercero | `REQUIREMENT_CONFLICT` · `AOD-10` |
| `H360-D11` | `docs/10 §6.2` (1/5/15 min) **vs** `sap/service.py:373` (1 min) | política de backoff | **Sí**: nivel 3 manda; el código es defecto | `IMPLEMENTATION_DEFECT` → `H360-S07` |
| `H360-D12` | `spec.md §14` → `docs/17-production-checklist.md` | referencia rota (3 veces) | **Sí**: defecto documental | `SPEC_DEFECT` → `H360-D02` |

---

## 5. Regla de lectura que se deja escrita

1. Para **fórmulas KPI** manda `Bases Consideradas`; los manuales Ross/Cobb solo aportan valores de referencia.
2. Para **quién es dueño de un objeto** manda la Recomendación §1/§15/§21 salvo decisión del propietario en contrario; los conflictos con `docs/02` van a `AUDIT_OWNER_DECISIONS_REQUIRED.md`.
3. Para **estados y reglas** manda `docs/12` sobre `docs/02` cuando ambos hablan (es más específico y posterior); la spec §5 debe absorber `BR-17…BR-19`.
4. Para **estado del programa** no debe leerse `INDEX.md` hasta su reconciliación; se lee `MASTER_PROGRAM_STATUS_RECONCILIATION.md §2`.
