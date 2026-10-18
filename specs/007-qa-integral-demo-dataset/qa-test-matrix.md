# QA Test Matrix — SPEC 007

Matriz técnica (qué dato del dataset habilita cada prueba QA y qué comprobación del seed lo garantiza). La guía de usuario está en `docs/MANUAL_QA_PRUEBA_INTEGRAL_GLOBAL_AVICOLA.md`; la cobertura por opción de menú en `audit/qa-integral-dataset/QA_DATA_COVERAGE_MATRIX.md`.

| Caso QA | Usuario | Dato del dataset | Resultado esperado | Garantía del seed |
|---|---|---|---|---|
| Login y menú por rol | los 12 | usuarios `qa.*`, concesiones BU | menú acorde a rol y BU; `qa.mobile` solo Gestión Avícola | «users and roles correct», «BU grants correct», «qa.mobile view_type mobile» |
| BU apagada (OD-16) | qa.isolation | ISO con grandparent/hatchery `is_enabled=False` | Progenitoras e Incubadora no aparecen; `/poultry/grandparent/...` ⇒ sin acceso | «isolation BU on/off» |
| Multiempresa | qa.admin vs qa.isolation | 2 empresas | cada uno ve solo lotes de su empresa | «lots have company/BU» |
| Dashboard | qa.supervisor | 364 eventos, 25 lotes, alertas, notificaciones | indicadores poblados, pendientes > 0 | «reports have source data» |
| Lotes por etapa | operadores | lotes `QA-*` por BU y etapa | listado y detalle con saldo, fase, indicadores, trazabilidad | «lots per BU» |
| Historial / Mis pendientes | operadores | draft/returned por BU | bandeja con sus borradores y devueltos | «workflow states valid» |
| Registrar operación (todas las categorías) | operadores | lotes activos por BU | el asistente ofrece los eventos de la etapa; validaciones BR-xx | cobertura de los 28 tipos |
| BR-18 exceso de OC | qa.operator.broiler | `QA-OC-BR18-TEST`=1000 | recepción de 1200 aves ⇒ rechazo BR-18 | «PO quantities coherent» |
| Revisión: pendientes/aprobados/devueltos | qa.supervisor | pending_review ×3, approved, returned ×3 | tres vistas pobladas | «workflow states valid» |
| Aprobación individual y en lote | qa.approver | corrected ×7 (3 del lote de engorde QA-BRO-003/002) | aprobar/rechazar; BR-14 impide aprobar lo propio | BR-14 en `flujo` |
| Corrección con antes/después | qa.supervisor | `wf-sup-corrected`, `wf-br14` | CorrectionLog visible; quien corrige no aprueba | `corregir` |
| Reverso | qa.supervisor + qa.approver | `bro2-recepcion-extra` (reversed) | original y contrapartida `REVERSED`; saldo neto | `reversar` |
| Cancelación | qa.operator.broiler | `wf-bro-cancelled` | estado `cancelled`, excluido de saldos | `cancel_event` |
| Cierre de lote | qa.supervisor | QA-BRO-003 (pendiente aprobaciones) vs QA-*-CLOSED-001 | cierre bloqueado por R7 hasta aprobar; cerrados con resumen | `cerrar_lote` |
| Alerta cierre previsto | operadores | planned_close_date vencida (QA-GP-CLOSE-001, QA-BRO-003) | notificación `lot_near_close` | `notificar` |
| Integración SAP (4 vistas) | qa.sap | inbound `QA_SYNTHETIC`, refs, pendiente de mapeo, inválido | listados poblados; sin envíos; outbound deshabilitado | «inbound 14 objects», «real SAP calls = 0» |
| Reportes producción/mortalidad/SAP vs App | qa.auditor | eventos aprobados 202+ | gráficas con datos; UNKNOWN como UNKNOWN | «reports have source data», «UNKNOWN scenario present» |
| Cargas iniciales | qa.supervisor + qa.approver | 4 batches applied + 4 XLSX `QA-CUT-*-NEW-*` | ver reconciliación de los aplicados; ejecutar ciclo completo con los fixtures | «cutover applied per BU», `fixtures/` |
| Auditoría | qa.auditor | 791 audit_logs QA | bitácora filtrable por usuario `qa.*` | vía servicios reales |
| Maestros | qa.admin | catálogos `QA …` incl. galpón inactivo | CRUD; inactivo no seleccionable | «farms/houses valid» |
| Usuarios/Roles/Acceso por unidad | qa.admin | 12 usuarios, concesiones | consulta y cambio de concesión; efecto inmediato en menú | «BU grants correct» |
| Móvil | qa.mobile | QA-BRO-00x | registro de campo (alimento, agua, mortalidad) | `view_type=mobile` |
| Incubadora etapa por etapa | qa.operator.hatchery | QA-HAT-REC/INC/OVO/NAC/BIRTH/CHICK | cada proceso ofrece el siguiente paso | lotes de incubadora |
| Trazabilidad generacional | cualquiera con lots:read | QA-HAT-GPGEN-001, QA-HAT-CHICK-001 | árbol GP→INC→BR y BR→INC→BRO | «EggBatch/ChickBatch coherent» |
