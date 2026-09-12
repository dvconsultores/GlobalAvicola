# FINAL FRONTEND AUDIT · REGISTRO DE RESIDUALES

Fecha: 2026-09-11 · Solo filas que NO terminan en estado final aceptable (o notas de infraestructura/gobernanza). **Nada se implementa en esta auditoría.**

| RES | FVA | Descripción | Estado actual | Severidad | Impacto negocio | Impacto seguridad | ¿Dueño/R existente? | ¿Duplicado? | ¿R nuevo? | ¿Decisión del propietario? | Dependencia externa | Tranche recomendada |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| RES-01 | FVA-07 (CAP-ADM-02) | Propiedad SAP vs local de Empresas/Granjas | **RESUELTO — OD-24 (A): importadas de SAP no editables; provisional local pre-P-08; sin producto hoy** | P1→cerrado | Medio (convergencia futura) | Ninguno | R-124 / AOD-06 → OD-24 | No | No | No | No | SPEC de convergencia antes de P-08 |
| RES-02 | FVA-10 (CAP-ADM-05) | Bandeja de clasificación pendiente sin UI (backend listo: GET/POST pending-classification) | OOS (diseño-condicional T-040-24) | P2 | Medio (clasificación admin) | Ninguno | T-040-24 | No | No | No (autorización de diseño) | No | Si el diseño la requiere: SPEC→AC→frontend mínimo |
| RES-03 | FVA-19 (CAP-BU-04) | Lote automático de abuelas «al completar importación» sin decisión (qué es completar/código/poblar) | **RESUELTO — OD-25 (B): `L-GP-{año}-{nn}` al aprobar, sin poblar; manual y legado intactos. Certificación técnica OK (GA-R153); UAT del propietario pendiente** | P3→cerrado (téc.) | Bajo | Ninguno | R-153 / OD-25 | No | No | No | No | Cierre al aceptar el propietario (UAT 7 casos) |
| RES-04 | FVA-28 (CAP-OPS-09) | Pantalla de reverso (solicitar/consultar) nunca construida (servicio interno certificado) | OOS (diferral fase 9) | P3 | Bajo | Ninguno | GA-REM-041/OD-19 | No | No | No (autorización) | No | Autorización fase 9 → SPEC→AC→UI |
| RES-05 | FVA-30 (CAP-OPS-11) | Volumen de evidencias no montado en producción (evidencias efímeras) | R-52 PENDING | P2 (infra/ops) | Medio (durabilidad de evidencias) | Ninguno | R-52 | No | No | No | No (acción de operaciones: `docker compose up -d backend`) | Operaciones (recrear contenedor con volumen) |
| RES-06 | FVA-32 (CAP-OPS-13) | 8 rutas SAP sin `response_model` (contrato) | R-112 abierto | P2 (técnica) | Bajo | Ninguno | R-112 · P-08 | No | No | No | **SÍ** (SAP real P-08) | Técnica Wave B/C ligada a P-08 |
| RES-07 | FVA-02/03/06/17/18/20/21/22/23/24/25/26/30/33/34/35/36/37/38 | 19 filas verificadas en runtime (L2/L3) **sin certificación formal por AC** | VNC | P3 (higiene de certificación) | Bajo | Ninguno | — | No | No | No (decisión de programa) | No | Si el programa exige L4/L5: spec→AC ligera por lote temático |
| RES-08 | FIA-05 | Inmutabilidad de `audit_logs` solo en aplicación (sin trigger BD) | R-148 P2 | P2 (técnica) | Bajo | Medio (defensa en profundidad) | R-148 | No | No | No (registrado Wave B) | No | Técnica Wave B (R-147/R-148) |
| RES-09 | (fuera de las 38) | R-177/AOD-24: tipo de huevo ≠ ovoscopía | OPEN P3 | P3 | Bajo | Ninguno | R-177/AOD-24 | No | No | **SÍ** (lista Wave B) | No | Decisión AOD-24 → SPEC |
| RES-10 | Notas de inventario | `/kpi` y `/my-pending` sin guarda de capacidad (solo sesión); `PermissionRoute` único uso; exports sin `can()` | Notas P3 | P3 | Bajo | Ninguno | — | No | No (patrón vigente documentado) | No | No | Si se desea, homogeneizar guardas en iteración futura |

**P0: 0 · P1: 1 (decisión de producto, no gap funcional) · P2: 4 · P3: 5 (2 de ellos decision-items).**
**Ningún residual es un defecto de flujo roto, superficie faltante aplicable, despliegue stale ni fila desconocida.**
Sin hallazgos R nuevos (dedup: todo mapea a R-52/R-112/R-124/R-148/R-153/R-177/T-040-24 o notas sin R; §56).
