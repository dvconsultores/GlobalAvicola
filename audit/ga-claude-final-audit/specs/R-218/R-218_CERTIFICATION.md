# R-218 · CERTIFICACIÓN TÉCNICA LOCAL — Serie semanal del lote (opción A)

Fecha: 2026-09-14 · Programa: GA PRE-SAP (T11) · Política: **AOD-29 Clarification 01**.

## 1 · Paquetes y commits

| Fase | SHA | Contenido |
|---|---|---|
| C1 · RED | **`0376305`** | BE 2F por causa exacta (ruta `GET /reports/lot/{id}/weekly` inexistente ⇒ 404/403) + FE 2F (tabla semanal y gráficos leían la lista sin sublistas). Finding: `EventType` de alimento = **`feed_registration`** |
| C2 · Implementación | **`d5cc5fb`** | BE: agregado de solo lectura con `_exigir_lote` + suma de estados aceptados (patrón `P-15`); agua atribuida una vez por (evento, semana); clasificado `MULTI_UNIDAD` en `route_scope`; guardián de rutas 213→214. FE: vista semanal y gráficos consumen el agregado (gate `reports:read` del paquete R-212) |

Decisión **C-01=A** del SPEC (endpoint agregado). Finding de fixture: el alcance del
lote deriva de `Lot.bird_type` (`business_units/scope.predicado`).

## 2 · Gates locales (PASS)

| Gate | Resultado | Evidencia |
|---|---|---|
| BE targeted (+guardián rutas) | **24/24** (rutas = 214) | `green/be-r218-green-targeted.log` |
| BE suite completa | **1384 passed / 0 failed / 49 skipped** (24:50) | `green/be-r218-green-full.log` |
| FE targeted | **2/2** | `green/fe-r218-green-targeted.log` |
| FE suite completa | **450/450** | `green/fe-r218-green-full.log` |
| `npm run build` | **EXIT 0** | `green/fe-r218-build.log` |

## 3 · Sensibilidad (restore `d5cc5fb`)

BE: B1 sin tenencia ⇒ `02` · B2 sin mortalidad ⇒ `01` · B3 permiso `operations:read`
⇒ `03`. FE: N1 sin agregado ⇒ AC-03 · N2 fuente plana ⇒ AC-04 · N3 sin mortalidad en
tabla ⇒ AC-03. Post-mutación: BE **3/3** · FE **2/2**.

## 4 · Estado

- **R-218 = `CLOSED_TECHNICALLY`** · UAT no requerida (verificación informativa).
- T11: R-213 ✓ · R-212 ✓ · R-218 ✓ · **siguiente: R-220** (residuales itemizados) y `GA_T11_CERTIFICATION`.
