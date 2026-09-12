# GA-R153 · PLAN

Fecha: 2026-09-12 · Baseline `9ad9b26`.

| Fase | Contenido | Estado |
|---|---|---|
| P1 | Formalización OD-25 (+registro AOD) | ✅ |
| P2 | Reconciliación R-153 (dueño; R-152 CLOSED confirmado) | ✅ |
| P3 | Traza del flujo actual | ✅ |
| P4 | Traza de esquema (nullability/constraints) | ✅ |
| P5 | Mapeo de campos del lote | ✅ |
| P6 | Diseño de secuencia/concurrencia (sin migración) | ✅ |
| P7 | Diseño de atomicidad (hook en ambas rutas) | ✅ |
| P8 | Diseño de idempotencia | ✅ |
| P9 | Compatibilidad de legado | ✅ |
| P10 | Traza de impacto frontend | ✅ |
| P11 | Spec | ✅ |
| P12 | Clarificaciones C01-C25 | ✅ |
| P13 | AC (57) | ✅ |
| P14 | RED (runtime 400 + vitest estático + tests PG) | ▶ |
| P15 | Commit C1 gobernanza + push | ⏳ |
| P16 | Implementación backend (gate + hook + generador) | ⏳ |
| P17 | Implementación frontend (form opcional + enlace/pendiente + i18n) | ⏳ |
| P18 | GREEN dirigido (vitest + pytest declarado) | ⏳ |
| P19 | Pruebas de concurrencia (PG/CI) | ⏳ |
| P20-P22 | Regresión P-07 / P-01 / R-130 | ⏳ |
| P23 | Regresión frontend (Vitest 292+ · tsc · build) | ⏳ |
| P24 | Commit C2 + push | ⏳ |
| P25 | Auto-deploy (observación de generación) | ⏳ |
| P26 | Runtime autenticado E2E-01…16 | ⏳ |
| P27 | Prueba de recepción (población una sola vez) | ⏳ |
| P28 | Pruebas de seguridad (tenant/BU/RBAC/global) | ⏳ |
| P29 | Limpieza | ⏳ |
| P30 | Reconciliación de cierre | ⏳ |
| P31 | Certificación técnica (R-153 CLOSED_FUNCTIONALLY_CERTIFIED) | ⏳ |
| P32 | Preparación de UAT del propietario | ⏳ |
| P33 | STOP | ⏳ |
