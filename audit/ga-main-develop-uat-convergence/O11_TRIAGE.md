# O-11 — triage (solo diagnóstico; sin cambios de producto)

Hallazgo: los filtros de granja de `/lots` y `/operations` cargan `GET /masters/farms?limit=100`; las granjas posteriores a la 100 no se pueden seleccionar.

| Pregunta del mandato (§22) | Respuesta con evidencia |
|---|---|
| ¿Límite deliberado o accidental? | **Deliberado en el backend**: `masters/router.py` declara `limit: int = Query(20, ge=1, le=100)` para todos los catálogos. **Accidental en el frontend**: la UI usa `?limit=100` como si fuera «traer todo». |
| ¿El backend soporta paginación? | Sí: `skip`, `limit`, `search` y cabecera `X-Total-Count` (GA-REM-033). |
| ¿El selector soporta búsqueda remota? | No: carga una lista fija en un `<select>`; no consulta `search` ni pagina. |
| Alcance del patrón | No es solo granjas: `limit=100` fijo en `LotListPage`, `LotFormPage` (granjas, galpones, líneas, razas, áreas), `OperationFormPage` (granjas, vacunas, medicamentos, causas, transportes, plantas, proveedores), `ApprovalPanel` y `MasterListPage`. |
| Granjas en QA | Dataset QA-DEMO-V1: 5 granjas (QA-GP-01, QA-BR-01, QA-EN-01, QA-EN-02, QA-INC-F1) — muy por debajo del tope. |
| ¿Dónde se superó el tope? | Solo en la base de **E2E**: la suite crea granjas por corrida y acumula más de 100 dentro de una misma base (rompió `spec008` en el ciclo anterior). No hay evidencia de >100 granjas por empresa en operación real. |
| Máximo operativo esperado por empresa | **No consta en el repositorio** (ni en specs ni en docs). Es un dato de negocio que solo puede dar la Owner. |

## Disposición

```text
O-11 = P2 (provisional, por mandato) · OWNER_DECISION_REQUIRED
```

- Si la Owner confirma que ninguna empresa superará ~100 granjas (u otro catálogo de los listados): `ACCEPTED_LIMIT`, dejando una alarma (aviso en UI cuando `X-Total-Count > 100`).
- Si podría superarse: `FIX_REQUIRED` en ciclo independiente. Solución natural sin tocar el backend: selector buscable (`search` + paginación por `X-Total-Count`) en los filtros de granja y, después, en los demás catálogos del patrón.
- Mientras tanto no bloquea la certificación de este ciclo: no hay pérdida de datos, solo imposibilidad de seleccionar entidades posteriores a la 100 en un filtro.
