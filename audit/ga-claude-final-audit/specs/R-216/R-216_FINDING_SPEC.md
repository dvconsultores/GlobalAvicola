# R-216 · FINDING + SPEC (COMPACTO) — PANEL: `lots_by_type` CON CLAVES `BirdTypeEnum.*` ⇒ TARJETAS EN 0

| Campo | Valor |
|---|---|
| **ID** | **R-216** · P2 · **no bloquea** · Estado `SPEC_READY` |
| **Origen** | C#9 (informe C); local `H5-dashboard-admin` · Registro G-28 · HEAD `c0b4afc` · 2026-09-13 |
| **GA-REM** | a asignar; sin migración/endpoint/permiso · UAT: no |

## 1 · Contexto y evidencia

`dashboard/service.py:171` — `lots_by_type = {str(row.bird_type): cnt}` con `bird_type` mapeado a `Enum(BirdTypeEnum)` (`masters/models.py:295`); `str()` de un `(str, Enum)` produce **`'BirdTypeEnum.BROILER'`** (verificado con Python). `DashboardPage.tsx:255,513` busca `lotsByType['broiler'|…]` ⇒ **0 en las cuatro tarjetas** mientras el subtítulo (suma de valores) es correcto. Evidencia local: `H5-dashboard-admin` (`BirdTypeEnum.BREEDER`…). Los tests `test_kpi_scope.py:286,342` comparan por substring en minúsculas y no lo detectan.

## 2 · Causa raíz

`str()` sobre un enum `(str, Enum)` sin `.value`.

## 3 · Comportamiento actual → esperado

| Aspecto | Hoy | Esperado |
|---|---|---|
| Claves | `'BirdTypeEnum.BROILER'` | `'broiler'` (valor del enum) |
| Tarjetas | 0 | recuentos correctos |
| Contrato | mismo dict | mismas claves documentadas y testeadas |

## 4 · Secciones §47 (resumen)

- **Alcance**: `dashboard/service.py:171` (`.value`); tests `test_r216_lots_by_type_contract.py` (claves exactas); ajustar el test de substring obsoleto.
- **Fuera**: resto del panel (R-212/R-218); KPIs (Wave C).
- **FE**: sin cambio (`DashboardPage` ya espera `'broiler'`). **BE**: una línea.
- **Contrato**: claves del dict normalizadas; sin cambio de forma.
- **Seguridad/tenant/BU/Transacciones/Auditoría/i18n/Migración/SAP**: sin cambio.
- **AC/cierre**: ver `R-216_AC_RED_E2E_UAT.md`.

## 5 · Dedup

C#9 sin registro previo (grep `lots_by_type` en backlog → vacío). **Nuevo** (G-28).

## 6 · Interdependencias

R-212 (panel/home) · R-204 (`active_alerts` del mismo servicio) — misma tranche de panel, paquetes separados.
