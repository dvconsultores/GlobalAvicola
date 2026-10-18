# QA Data Coverage Matrix — `QA-DEMO-V1` × `navigationConfig.ts`

Fuente del menú: `frontend/src/data/navigationConfig.ts` (leído el 2026-10-18; 6 secciones, 26 entradas navegables). Para cada entrada: permiso, datos QA que la alimentan, usuario(s) QA que la ven y sección de la guía (`docs/MANUAL_QA_PRUEBA_INTEGRAL_GLOBAL_AVICOLA.md`).

| Sección | key | Ruta | Permiso / BU | Datos QA que la alimentan | Usuarios QA | Guía § | Cobertura |
|---|---|---|---|---|---|---|---|
| main | dashboard | `/` | dashboard:read | 25 lotes, 364 eventos, pendientes, alertas, notificaciones | todos | 3 | COVERED |
| operational | poultry › lots | `/lots` | lots:read · requiresUnits | lotes por BU y etapa, 3 cerrados, 4 de cutover, trazabilidad (7 egg_batches, 2 chick_batches) | todos salvo ISO para MAIN | 4.1–4.2 | COVERED |
| operational | poultry › operations_history | `/operations` | operations:read | eventos en 11 estados | operadores, supervisor, aprobador | 4.3 | COVERED |
| operational | poultry › my_pending | `/my-pending` | operations:read | draft ×3, returned ×3 por operador | operadores | 4.3 | COVERED |
| operational | grandparent › gp_rearing | `/poultry/grandparent/rearing` | operations:read · grandparent | QA-GP-CRIA-001 (importación, recepción, distribución, alimento, pesaje, mortalidad, vacunas, medicación, descarte) | qa.operator.gp, supervisor, approver, admin | 4.4 | COVERED |
| operational | grandparent › gp_production | `/poultry/grandparent/production` | operations:read · grandparent | QA-GP-PROD-001, QA-GP-CLOSE-001, QA-CUT-GP-001 (huevo, clasificación, despacho, cierre previsto) | ídem | 4.4 | COVERED |
| operational | breeder › br_rearing | `/poultry/breeder/rearing` | operations:read · breeder | QA-BR-CRIA-001, QA-CUT-BR-001 (agua, vacunas, medicación, descarte) | qa.operator.breeder, … | 4.4 | COVERED |
| operational | breeder › br_production | `/poultry/breeder/production` | operations:read · breeder | QA-BR-PROD-001/002 (recolección diaria, clasificación, despacho a incubadora) | ídem | 4.4 | COVERED |
| operational | hatchery | `/poultry/hatchery` | operations:read · hatchery | 8 procesos en 6 etapas + ciclo GP + cutover | qa.operator.hatchery, … | 4.4 | COVERED |
| operational | broiler | `/poultry/broiler` | operations:read · broiler | QA-BRO-001/002/003, cerrado, cutover; reverso; transferencia; salida parcial | qa.operator.broiler, qa.mobile, … | 4.4 | COVERED |
| review | review › review_pending | `/review` | review:read | pending_review ×3, in_review ×2, corrected ×7 | qa.supervisor, qa.approver, qa.auditor | 5.1 | COVERED |
| review | review › review_approved | `/review?status=approved` | review:read | approved 330+ | ídem | 5.1 | COVERED |
| review | review › review_returned | `/review?status=returned` | review:read | returned ×3 con motivo | ídem | 5.1 | COVERED |
| review | approvals | `/approvals` | approvals:approve | corrected ×7 (3 para lote), caso BR-14 (aprobador corrigió), rejected ×1 | qa.approver, qa.admin | 5.2–5.3 | COVERED |
| integration | sap › sap_pending | `/sap` | sap:read | 85 inbound QA_SYNTHETIC, QAP7 pendiente de mapeo | qa.sap, qa.admin, qa.auditor | 6 | COVERED (sintético) |
| integration | sap › sap_sent | `/sap` | sap:read | 0 envíos (outbound deshabilitado) | ídem | 6 | COVERED (vacío por diseño) |
| integration | sap › sap_errors | `/sap` | sap:read | QA-MAT-INVALIDO (V_INVALID) | ídem | 6 | COVERED |
| integration | sap › sap_log | `/sap` | sap:read | 14 sync jobs QA_SYNTHETIC | ídem | 6 | COVERED |
| reports | reports › rpt_production | `/reports` | reports:read | egg_collection aprobados (GP/BR), diaria en QA-BR-PROD-001 | qa.auditor, qa.supervisor, qa.sap, qa.admin | 7 | COVERED |
| reports | reports › rpt_mortality | `/reports` | reports:read | mortality_recording aprobados; pico semana 4 QA-BRO-003 | ídem | 7 | COVERED |
| reports | reports › rpt_sap | `/reports/sap` | reports:read | consolidated ×5, referencias sintéticas | ídem | 7 | COVERED (sintético) |
| administration | cutover | `/cutover` | cutover:read | 4 batches applied + 4 XLSX `QA-CUT-*-NEW-*` | qa.supervisor, qa.approver, qa.admin | 8 | COVERED |
| administration | audit | `/audit` | audit:read | 791 audit_logs de usuarios qa.* | qa.auditor, qa.admin | 9 | COVERED |
| administration | masters | `/masters` | masters:read | 19 catálogos QA, galpón inactivo | qa.admin (qa.supervisor lectura) | 10.1 | COVERED |
| administration | settings › settings_users | `/users` | users:read | 12 usuarios qa.* | qa.admin | 10.2 | COVERED |
| administration | settings › settings_roles | `/roles` | users:read | 7 roles canónicos | qa.admin | 10.2 | COVERED |
| administration | settings › settings_profile | `/profile` | CORE | cualquier usuario | todos | 10.4 | COVERED |
| administration | settings › settings_unit_access | `/admin/unit-access` | business_units:read | 8 CBU (2 apagadas en ISO), 29 UBU | qa.admin | 10.3 | COVERED |
| (móvil) | poultry (solo) | — | view_type=mobile | qa.mobile · QA-BRO-001 | qa.mobile | 4.4 Móvil | COVERED |

**Resumen**: 26/26 entradas del menú con datos y usuario de prueba · 4/4 BU · 12/12 usuarios con propósito · 11/11 estados internos de workflow · 28/28 tipos de evento · SAP 100 % sintético (0 llamadas reales).
