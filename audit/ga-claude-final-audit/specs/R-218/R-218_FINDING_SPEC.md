# R-218 · FINDING + SPEC (COMPACTO) — VISTA SEMANAL Y GRÁFICOS PLANOS (LISTA SIN SUBLISTAS)

| Campo | Valor |
|---|---|
| **ID** | **R-218** · P2 · **no bloquea** · Estado `SPEC_READY` |
| **Origen** | C#4 (informe C); F G-08/G-20 · Registro G-30 · HEAD `c0b4afc` · 2026-09-13 |
| **GA-REM** | a asignar; sin migración/permiso · UAT: no |

## 1 · Contexto y evidencia

`/operations` lista devuelve `OperationalEventRead` **sin sublistas** (`operations/schemas.py:256-266`); `LotDetailPage.tsx:249-268` (tabla «semanal») y `ReportsPage.tsx:25-31` (gráficos de mortalidad/alimento/peso) leen `bird_movements/feed_movements` de esa lista ⇒ la «Vista semanal» nunca aparece y las series quedan planas (solo `water_liters`, que es columna, funciona).

## 2 · Causa raíz

La lista se aligeró (contrato) sin una fuente de agregación para la vista semanal/gráficos.

## 3 · Comportamiento actual → esperado

| Aspecto | Hoy | Esperado |
|---|---|---|
| Vista semanal del lote | vacía | tabla por semana (mortalidad, alimento, peso, agua) |
| Gráficos de reportes | planos | series reales de las sublistas o de un agregado |

## 4 · Secciones §47 (resumen)

- **Alcance (decisión C-01)**: (A) endpoint agregado `GET /reports/lot/{id}/weekly` (backend) **o** (B) el FE pide los detalles necesarios (N+1 caro, descartable) **o** (C) la lista expone un modo `include=movements` acotado. Propuesto: **A**.
- **Fuera**: KPIs (Wave C); paginación general (GA-REM-011).
- **Contrato**: A añade una ruta de solo lectura (documentada); B/C no la requieren.
- **Seguridad/BU**: el agregado pasa por `_exigir_lote` (patrón KPI) — obligatorio en A.
- **Migración/SAP**: ninguna / indirecto.
- **AC/cierre**: ver `R-218_AC_RED_E2E_UAT.md`.

## 5 · Dedup

C#4 sin paquete previo (el contrato ligero es intencional; falta la contraparte de lectura). **Nuevo** (G-30).

## 6 · Interdependencias

R-204/R-214 (KPI/agregados; misma familia de lectura) · R-212 (consola 403) · GA-REM-011 (paginación).
