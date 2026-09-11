# RES-02 / CAP-ADM-05 · ANÁLISIS — BANDEJA DE CLASIFICACIÓN PENDIENTE

Fecha: 2026-09-11 · Fila: **FVA-10** (OUT_OF_CURRENT_PRODUCT_SCOPE) · RFC: `catalog:35`, `PHASE_9_DEPENDENCY_PREFLIGHT.md:20,34` (T-040-24, AC-H07), `BACKEND_CAPABILITY_MAP.md:31`, `CERTIFICATION_SCOPE_RECONCILIATION.md` §8.

## 1 · Hechos

- **Backend listo:** `GET /operations/pending-classification`, `POST …/classify`, `POST …/reclassify` (permisos `masters:update` / `corrections:correct`; inquilino; fase 6 ✔).
- **Frontend: 0 referencias** (grep exhaustivo; sin ruta ni página). No hay entrada de menú ni pantalla.
- **Requisito:** condicional — T-040-24 «bandeja de clasificación pendiente, **si el diseño la requiere**» (AC-H07). Nunca se autorizó el diseño.
- **OD-20** autorizó la fase 9 **solo para GA-FE-02**; «el resto del inventario permanece como estaba» ⇒ la bandeja sigue congelada por gobernanza, no por olvido.
- Clasificación histórica: `FRONTEND_MISSING` (fase 9 congelada); reconciliación final: `OUT_OF_CURRENT_PRODUCT_SCOPE`.

## 2 · Determinaciones solicitadas

| Pregunta | Respuesta |
|---|---|
| ¿Gap real de producto? | **NO** — no hay AC vigente que exija la UI (requisito condicional sin diseño ratificado) |
| ¿Falta autorización de diseño? | **SÍ** — es el bloqueo verdadero (gobernanza de diseño, T-040-24) |
| ¿Decisión del propietario? | No inmediata; es una decisión de **alcance/diseño** que puede agruparse con la cola de diseño fase-9 |
| ¿Mejora UX? | Sí — mejora funcional de administración si algún día se requiere |
| ¿Ya gobernada por RBAC? | El backend sí (`masters:update`/`corrections:correct`); la UI no existe |

## 3 · Dedup

Ya poseída por **T-040-24 / AC-H07** (preflight fase 9) + clasificación histórica. **No se crea finding nuevo.** Sin conflicto con R-122/R-150 (patrones distintos).

## 4 · Disposición

`OUT_OF_CURRENT_PRODUCT_SCOPE` (condicional al diseño). Si el programa/autoridad de diseño ratifica que se requiere: **SPEC→AC→UI mínima** (reutilizando los endpoints existentes) en una tranche propia — **no autorizada ahora**. Se propone agrupar con CAP-OPS-09 (reverso) en un **paquete de decisión de diseño fase-9 restante** cuando el programa lo abra.
