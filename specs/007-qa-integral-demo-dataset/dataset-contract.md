# Dataset Contract — `QA-DEMO-V1`

Todo lo que el seed crea lleva al menos uno de estos marcadores: código `QA-`/`QAP…`, usuario `qa.*`, email `@qa.globalavicola.com`, `source_system=QA_DEMO_V1` (lotes, cutover), `extra_data.qa_marker=QA_DEMO_V1` (eventos), `source_system=QA_SYNTHETIC` / `extra_data.source=QA_SYNTHETIC` (SAP), `tax_id=QA-DEMO-V1-*` (empresas), `payload.qa_key` (notificaciones).

## 1 · Empresas

| Clave | Nombre | tax_id | approval_levels | BU habilitadas |
|---|---|---|---|---|
| MAIN | QA Avícola Integral C.A. | `QA-DEMO-V1-INTEGRAL` | 2 | grandparent, breeder, hatchery, broiler |
| ISO | QA Avícola Aislamiento C.A. | `QA-DEMO-V1-AISLAMIENTO` | 1 | breeder, broiler (grandparent y hatchery **apagadas**) |

## 2 · Roles

Los 7 roles canónicos existentes (`company_id NULL`) se **leen**; no se crean ni modifican. «Operador» del mandato ⇒ `Operador de Granja`. `Administrador de Accesos` no recibe usuario QA (no tiene alcance productivo).

## 3 · Usuarios (contraseña: fuera del repositorio)

| Usuario | Rol | Empresa | BU concedidas | Vista | Propósito |
|---|---|---|---|---|---|
| qa.admin | Super Administrador | MAIN | 4 | web | configuración, maestros, usuarios, diagnóstico |
| qa.supervisor | Supervisor Avícola | MAIN | 4 | web | revisión, correcciones, reversos, cargas iniciales |
| qa.approver | Aprobador | MAIN | 4 | web | aprobación y rechazo |
| qa.operator.gp | Operador de Granja | MAIN | grandparent | web | registro Progenitoras |
| qa.operator.breeder | Operador de Granja | MAIN | breeder | web | registro Reproductoras |
| qa.operator.hatchery | Operador de Granja | MAIN | hatchery | web | registro Incubadora |
| qa.operator.broiler | Operador de Granja | MAIN | broiler | web | registro Engorde |
| qa.sap | Analista SAP | MAIN | 4 | web | Integración SAP (sintética) |
| qa.auditor | Auditor | MAIN | 4 | web | auditoría y reportes |
| qa.mobile | Operador de Granja | MAIN | broiler | **mobile** | registro de campo |
| qa.isolation | Supervisor Avícola | ISO | breeder, broiler | web | multiempresa y BU apagadas |
| qa.isolation.operator | Operador de Granja | ISO | breeder, broiler | web | registro en la empresa 2 |

Credencial: una misma contraseña temporal para los 12 (`GA_QA_SEED_PASSWORD` o generada en `/tmp/global_avicola_qa_credentials.txt`, 0600). Se entrega al Owner por canal separado. `--reset-passwords` la vuelve a aplicar a usuarios existentes.

## 4 · Maestros (MAIN)

- Granjas: `QA-GP-01` (progenitoras, 3 galpones), `QA-BR-01` (reproductoras, 3), `QA-EN-01` y `QA-EN-02` (engorde, 3 cada una; `QA-EN-02-G3` **inactivo** no — el inactivo es el galpón marcado `is_active=False` en `QA-EN-01`), `QA-INC-F1` (sede de incubadora, 1 galpón técnico).
- Incubadora `QA-INC-01`: incubadoras `QA Incubadora A1…A4`, nacedoras `QA Nacedora N1…N2`.
- Áreas `QA-AREA-GP/BR/INC/ENG` + `QA-AREA-ADM`. Líneas `QA-LINE-GP/BR/BRO` con raza y curva de peso (14 puntos).
- Proveedores (genética, alimento, veterinaria, transporte…), alimentos (pre-inicio, inicio, crecimiento, postura, final), vacunas, medicamentos, causas de mortalidad y descarte, transportes, plantas de beneficio, motivos de rechazo, tipos de corrección.
- ISO: `QA-ISO-F1` con 2 galpones, catálogos mínimos propios.

## 5 · Lotes

| Código | BU | Etapa | Origen |
|---|---|---|---|
| QA-GP-CRIA-001 | grandparent | cría, 6 semanas | importación `QA-OC-GP-IMPORT-005` |
| QA-GP-PROD-001 | grandparent | producción | apertura manual |
| QA-GP-CLOSE-001 | grandparent | producción, cierre previsto hace 10 días (alerta) | apertura manual |
| QA-GP-CLOSED-001 | grandparent | **cerrado** | apertura manual |
| QA-CUT-GP-001 | grandparent | producción, **cutover v2 aplicado** (alimento UNKNOWN) | SPEC 006 |
| QA-BR-CRIA-001 | breeder | cría, 8 semanas | pollitas de `QA-HAT-GPGEN-001` |
| QA-BR-PROD-001 / -002 | breeder | producción (recolección diaria) | apertura manual |
| QA-BR-CLOSED-001 | breeder | **cerrado** | apertura manual |
| QA-CUT-BR-001 | breeder | cría, cutover aplicado | SPEC 006 |
| QA-HAT-GPGEN-001 | hatchery | ciclo completo generación GP | huevo de QA-GP-PROD-001 |
| QA-HAT-REC-001 / INC-001 / OVO-001 / NAC-001 / BIRTH-001 / CHICK-001 | hatchery | recepción · incubación · ovoscopia · nacedora · nacimiento · despacho | huevo de QA-BR-PROD-001 |
| QA-CUT-HAT-001 | hatchery | incubación en curso, cutover aplicado (descartados UNKNOWN) | SPEC 006 |
| QA-BRO-001 / -002 / -003 | broiler | 1 semana · 4 semanas (con reverso) · 6 semanas (salida parcial, cierre previsto) | recepción `QA-OC-BRO-AVES-00x` |
| QA-BRO-CLOSED-001 | broiler | **cerrado** | recepción |
| QA-CUT-BRO-001 | broiler | engorde, cutover aplicado (alimento UNKNOWN) | SPEC 006 |
| QA-ISO-BR-001, QA-ISO-BRO-001 | ISO | producción / engorde | apertura manual / recepción |

## 6 · Workflow (eventos de fecha reciente, por servicios reales)

draft ×3 · registered ×4 · pending_review ×3 · in_review ×2 · returned ×3 · corrected ×7 (incluye 3 para aprobación en lote y 2 correcciones formales con CorrectionLog) · approved (flujo completo) · rejected ×1 · cancelled ×1 · reversed ×2 (par original+contrapartida) · consolidated ×5 (alimento del lote cerrado de engorde). `sent_to_sap`/`sap_confirmed`: **0**.

## 7 · SAP sintético

14 objetos HANA staged (`QA_SYNTHETIC`, jobs completados), mappings MANDT 100 → `QA01`/`QA02` → `QAP1…QAP5`,`QAP9`; referencias promovidas: plantas, almacenes, materiales, proveedores, centros de costo, lotes SAP, OC y STO. OC: `QA-OC-GP-AVES-001`=5000, `QA-OC-BR-AVES-002`=10000, `QA-OC-BRO-AVES-003`=10000, `QA-OC-BRO-AVES-004`=12500, `QA-OC-BR18-TEST`=1000 (para exceder BR-18 con 1200), `QA-OC-GP-IMPORT-005`, STO `QA-STO-…`. Ejemplos deliberados: `QAP7` en `M_PENDING_MAPPING`, material `QA-MAT-INVALIDO` en `V_INVALID`. Outbound: no habilitado; payloads: 0.

## 8 · Cargas iniciales

4 batches `applied` (uno por BU) con `source_reference=<run_id>` y un `UNKNOWN` deliberado por BU; 4 plantillas XLSX en `audit/qa-integral-dataset/fixtures/QA_cutover_<bu>.xlsx` con códigos `QA-CUT-*-NEW-*` libres para que QA ejecute su propio ciclo.

## 9 · Notificaciones

`lot_near_close` leída (supervisor) y no leída (operadores) + las generadas por el motor (umbral de mortalidad, peso fuera de curva) durante la historia.

## 10 · Invariantes de verificación (`--verify`)

Las comprobaciones del mandato §49 (`verificar()`): empresas, BU, usuarios/roles, concesiones, móvil, granjas/galpones, equipos de incubadora, lotes por BU, detalles de evento, estados de workflow, cobertura de los 28 tipos, referencias SAP sintéticas, OC coherentes, 14 objetos inbound, EggBatch/ChickBatch, datos para reportes, escenario UNKNOWN, marcadores, cutover aplicado por BU, `real SAP calls = 0`.
