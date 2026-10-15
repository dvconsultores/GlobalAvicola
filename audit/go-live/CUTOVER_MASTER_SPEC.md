# GLOBAL AVÍCOLA — CUTOVER MASTER SPEC (Go-Live real)

Fecha: 2026-09-17 · Baseline: `fef7289` · Estado: **SPEC (diseño) — sin implementación**
Reutiliza: **GA-REQ-061 / T14** (certificada) · Frontera SAP: fuera de alcance.

---

## 1 · Proceso canónico (mandato §3)

```
1. FREEZE/CUTOFF          — instante y alcance de congelación acordados (por BU/empresa)
2. EXTRACCIÓN             — datos reales de fuentes del negocio (planillas/registros), JAMÁS inventados
3. TRANSFORMACIÓN         — a la plantilla versionada de la BU (códigos maestros, fechas ISO, unidades)
4. STAGING                — upload + parse + normalización (Excel = DATA, nunca código)
5. VALIDACIÓN             — errores estructurados por fila/campo; preview; corrección re-subiendo
6. CORRECCIÓN             — ciclo libre antes de SUBMIT
7. APROBACIÓN             — submit (creador≠aprobador) → approve | reject
8. APPLY                  — transacción única: revalidación + lotes MIGRATED + openings + auditoría
9. RECONCILIACIÓN         — Opening ↔ Post-Lifetime (golden, UNKNOWN≠0), conteos y correcciones
10. FIRMA                 — ACTA DE CUTOVER (nuevo — §6): responsables, hashes, conteos, fecha
11. APERTURA OPERACIONAL  — registro de eventos reales post-cutover sobre los lotes migrados
```

## 2 · Reutilización de GA-REQ-061 (capacidad certificada — no se reconstruye)

| Componente | Implementado (T14) | Uso en Go-Live real |
|---|---|---|
| API batches | `POST/GET /api/v1/cutover-batches` · `POST …/{id}/upload` · `…/submit` · `…/approve` · `…/reject` · `…/apply` · `GET …/{id}/validation` · `…/items` · `…/{id}/reconciliation` | Sin cambios |
| Plantillas | `GET /api/v1/cutover-templates/{bu}` — `cutover_template_{grandparent|breeder|hatchery|broiler}_v1.xlsx` (hojas `Instrucciones`/`Meta`/`Datos`; `template_version` validada) | **Rellenadas con datos reales** por el negocio |
| Correcciones | Router `opening-balances` (corrección gobernada, motivo obligatorio, original visible; AC65: `opening 10.000 → post 35 → corrección 9.900 ⇒ 9.865`) | Mismo mecanismo |
| Estados | `DRAFT → VALIDATING → VALIDATED → PENDING_APPROVAL → APPROVED → APPLIED` (+`REJECTED`; apply fallido = rollback total; re-apply ⇒ 409 determinista) | Sin cambios |
| Idempotencia | checksum sha256 del archivo + constraints (batch y opening único por lote) | Sin cambios |
| Semántica numérica | **celda vacía = UNKNOWN · `0` explícito = cero conocido · `N/A` = NOT_APPLICABLE**; sin tolerancias (§21 mandato) | Regla dura para datos reales |
| Modelo | `CutoverBatch`/`CutoverItem`/`CutoverStagingRow` + extensión `OpeningBalance` (R-67 `PARTIAL_REUSE`; `cutover_datetime`, `data_status` por métrica, provenance) | Sin cambios |
| Lote migrado | `origin = MIGRATED`, `legacy_lot_code`, `source_system/reference`; código canónico sigue siendo `lot_code` | Prefijos reales de origen del negocio |
| Seguridad | Módulo de permisos `cutover:*`; tenancy; gates BU (OD-16); `SELECT FOR UPDATE` + transición atómica | Se añaden usuarios reales con esos permisos |

**Reglas de preservación** (mandato §3, todas ya soportadas por el diseño certificado):
`NATIVE vs MIGRATED` · `real_start_date` (inicio real del lote) ≠ `cutover_datetime` (corte) · KNOWN/UNKNOWN/NOT_APPLICABLE por métrica · apply atómico · idempotencia doble · correcciones gobernadas · **estado original preservado** (nunca se borra historia; la corrección recalcula por componentes etiquetados).

## 3 · Campos por plantilla/BU (base §4 del mandato — por dominio)

| BU | Ítems | Campos de captura (mínimos de negocio) |
|---|---|---|
| `grandparent` / `breeder` | Lotes de aves en marcha | `legacy_lot_code`, `farm_code`, `house_code`, `real_start_date`, genética, sexo, **población viva al corte**, mortalidad/sacrificios **acumulados**, alimento acumulado (kg), peso actual (si existe), `cutover_datetime`, estados KNOWN/UNKNOWN por métrica |
| `hatchery` | Procesos de incubación **en curso** | Lote/equipo, fecha-hora de carga, huevos recibidos/cargados/en proceso, etapa/días, transferidos, nacimientos, descartes, fecha prevista de nacimiento, lote origen (auditoría fina de columnas al implementar G2; diseño §4 de GA-REQ-061) |
| `broiler` | Lotes de engorde en marcha | Como aves + consumo/IC, pesajes disponibles, salida parcial si existiera; `UNKNOWN` permitido donde no haya dato, nunca `0` fabricado |
| Transversal | Openings no-lote | Inventarios operacionales y saldos definidos en `REAL_DATA_MIGRATION_PLAN.md` §3 |

## 4 · Congelación (FREEZE/CUTOFF) — extensión a especificar en G2

- **Ventana**: fecha-hora de corte por empresa/BU; desde `cutover_datetime` el negocio no registra en el sistema anterior para ese alcance (o se documenta cómo se reconcilia el solape).
- **Regla del sistema**: los eventos registrados en Global Avícola con `event_date < cutover_datetime` sobre un lote migrado deben rechazarse o tratarse por reconciliación declarada — **AC nuevo `CUT-GL-02`** (a especificar en G2; hoy no existe guarda de fecha-vs-cutover).
- **Freeze de maestros**: durante el apply no se crean/modifican maestros referenciados (ventana operativa acordada).

## 5 · Nuevos ACs propuestos (semilla G2 — SPEC, a refinar con clarificación)

| AC | Requisito |
|---|---|
| `CUT-GL-01` | **Acta de cutover**: al terminar la reconciliación, el sistema genera un acta inmutable (PDF/JSON + sha256) con: empresa, BU, `cutover_datetime`, checksum del archivo fuente, conteos leídos/válidos/aplicados, métricas UNKNOWN, aperturas creadas, responsable funcional y aprobador, y firmas declaradas (funcional/técnico). |
| `CUT-GL-02` | Guarda de fecha vs `cutover_datetime` en eventos de lotes migrados (rechazo determinista o flujo de reconciliación explícito). |
| `CUT-GL-03` | Secuencia multi-BU/multi-empresa: N batches ordenados con dependencias declaradas (p. ej., incubadora referencia lote origen) y verificación de integridad cruzada previa al apply del dependiente. |
| `CUT-GL-04` | Ensayo (rehearsal) repetible contra copia aislada con dataset de ensayo versionado (semilla del `CUTOVER_REHEARSAL_PLAN.md`). |
| `CUT-GL-05` | Reapertura/corrección post-firma: política explícita (hoy: correcciones gobernadas sobre openings; reapertura de batch no existe — decidir en G2). |

## 6 · Firma (§10 del mandato ampliado)

El acta (`CUT-GL-01`) es el documento de firma del cutover. Contendrá hashes que encadenan: `source_checksum_sha256` → batch → openings → reconciliación → acta. Sin acta firmada no se declara apertura operacional. La firma es **humana** (responsable funcional + técnico); el sistema solo la registra y la evidencia.

## 7 · Lo que esta SPEC NO hace

- No implementa nada (mandato §12).
- No define SAP real (RFC/OData/IDoc/BAPI/HANA/documentos ficticios prohibidos).
- No fija tolerancias numéricas (prohibidas sin decisión de negocio → `OWNER_GATE_REAL`).
- No altera secuencias de códigos ni la autogeneración R-153.

---

## Addendum SPEC 006 (2026-10-15) — contrato de plantillas **v2** por unidad de negocio

El Owner reportó en uso real que la carga de cargas iniciales no funcionaba; la reproducción en HEAD (`57a421a`) demostró que la plantilla **v1 genérica** (8 columnas de aves por sexo para las cuatro BU) no podía representar incubadora ni engorde, perdía la distinción N/A/UNKNOWN y dejaba a la pantalla sin guía (`audit/cutover-initial-balances/01_LIVE_FAILURE_ROOT_CAUSE.md`). La remediación es **posterior a la certificación GA-REQ-061**, que se conserva íntegra; esta sección registra la evolución:

| Elemento | v1 (GA-REQ-061, histórico) | v2 (SPEC 006, vigente) |
|---|---|---|
| Plantillas | `cutover_template_{bu}_v1.xlsx`, mismas 8 columnas | `CUTOVER_{GRANDPARENT,BREEDER,HATCHERY,BROILER}_V2` (`audit/cutover-initial-balances/03…06`) con `Catalogos` e `Instrucciones` por campo; XLSX y CSV al mismo DTO |
| Versión | `v1` | `v2`; `v1 = RETIRED_WITH_CLEAR_ERROR` (nunca se reinterpreta) |
| Semántica | N/A y vacío colapsaban a `None` | `{value, status}` por métrica: vacío = UNKNOWN · 0 = KNOWN · N/A = NOT_APPLICABLE |
| Apply | fase = primera activa (CRIA), sin `LotPhase`, sin ubicación/genética | fase declarada por BU, `LotPhase`, galpón/área/línea/raza/sexo, `OpeningBalance` extendido (mixto, alojadas, salidas, estados), `hatchery_openings` |
| Motor | sin guarda de corte; saldos de huevo/pollito sin apertura | `CUT-GL-02`; saldos BR-01/BR-03/BR-04 leen la apertura |
| API | sin listado ni informe de errores | `GET /cutover-batches`, `GET …/{id}`, `GET …/preview`, `GET …/errors?format=csv|xlsx`, `GET /cutover-templates/{bu}?format=&batch_id=` |
| E2E | API-only, continuidad solo engorde | UI por BU (4 specs) con primer evento post-corte y CUT-GL-02 |

Las filas de la §2 que citan `cutover_template_{bu}_v1.xlsx` describen el estado anterior; la referencia vigente es `specs/006-cutover-initial-balances-remediation/` y `audit/cutover-initial-balances/`.
