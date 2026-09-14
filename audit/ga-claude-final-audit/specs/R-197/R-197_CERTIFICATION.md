# R-197 · CERTIFICACIÓN TÉCNICA LOCAL — Bandeja de revisión por estado y detalle veraz

Fecha: 2026-09-14 · Programa: GA PRE-SAP (T10) · Política: **AOD-29 Clarification 01**
(certificación local con gates reproducibles; **GitHub Actions retirado**; **push requerido**
a `origin/main` con verificación de SHA remoto).

## 1 · Paquetes y commits

| Fase | SHA | Contenido |
|---|---|---|
| C1 · RED | **`afea748`** | FE 10F (5 bandeja + 5 detalle) · BE 5F + 1 control; findings de fixture (EventType=`mortality_recording`, `ApprovalAction` sin `company_id`, cola exige `business_unit_id`) |
| C2 · Implementación | **`10f7b53`** | BE: `/review/pending` acepta `status` (múltiple, 422 si inválido) y `registered_by_id`; nueva `GET /review/events/{id}/actions` (tenencia por evento + ámbito de cadena; 403 sin `review:read`); `route_scope` clasificada; guardián de rutas 212→213. FE: 7 pestañas reales; filtro operador solo con `users:read` (`registered_by_id`, nunca `operator_id`); 403 ≠ «sin resultados»; modal de devolución (sin diálogos nativos, ≥10 caracteres); detalle permanece y recarga; guard de vuelo (1 POST); badge `status.*`; enlace al lote creado |
| C2b · Cobertura | **`e21629a`** | Tests de tenencia: evento ajeno ⇒ 404 (empresa B + control 200), fuera de ámbito de cadena ⇒ 404, `operations:read` sin `review:read` ⇒ 403 (hooks S3/S4) |

## 2 · Gates locales (PASS)

| Gate | Resultado | Evidencia |
|---|---|---|
| BE targeted R-197 | **10/10** | `evidence/green/be-r197-green-targeted.log` |
| BE suite completa | **1373 passed / 0 failed / 49 skipped** (20:56) | `evidence/green/be-r197-green-full.log` |
| Guardianes (population + BU guard + R-197) | **52 passed** (incluye recuento de rutas = 213) | `evidence/green/be-r197-guardians.log` |
| FE targeted R-197 | **10/10** | `evidence/green/fe-r197-green-targeted.log` |
| FE suite completa | **429/429** (baseline 419 + 10) | `evidence/green/fe-r197-green-full.log` |
| `npm run build` (`tsc -b && vite build`) | **EXIT 0** | `evidence/green/fe-r197-build.log` |

## 3 · Sensibilidad (mutación → RED quirúrgica → restore desde `10f7b53`)

| ID | Mutación | Rojo observado | Log |
|---|---|---|---|
| S1 | servicio ignora `status` (siempre defecto) | `01`, `04`, `04b` (control `02` intacto) | `sensibilidad/be-s1-…` |
| S2 | router sin validación de catálogo | `03` únicamente | `sensibilidad/be-s2-…` |
| S3 | historial sin tenencia (empresa/ámbito) | `06b`, `06c` únicamente | `sensibilidad/be-s3-…` |
| S4 | permiso de la ruta → `operations:read` | `07` únicamente | `sensibilidad/be-s4-…` |
| F1 | pestaña `in_review` mapea a `pending_review` | AC05 únicamente | `sensibilidad/fe-f1-…` |
| F2 | filtro vuelve a `operator_id` | AC04 únicamente | `sensibilidad/fe-f2-…` |
| F3 | 403 cae al branch genérico | AC19 únicamente | `sensibilidad/fe-f3-…` |
| F4 | sin guard de vuelo | AC14/16/17 únicamente | `sensibilidad/fe-f4-…` |
| F5 | historial desde `/review/batches` | AC13 únicamente | `sensibilidad/fe-f5-…` |
| F6 | badge crudo (sin i18n) | AC21 únicamente | `sensibilidad/fe-f6-…` |

**Post-mutación** (restauración verificada, worktree limpio, `HEAD = e21629a`):
BE targeted **10/10** · FE targeted **10/10** (`evidence/post-mutation/`).

## 4 · Hallazgos del paquete (registrados en C1; resueltos en C2)

1. `EventType` de mortalidad = `mortality_recording` (fixtures).
2. `ApprovalAction` **no** declara `company_id`: la tenencia se resuelve por el evento —
   `get_event_actions` exige además el ámbito de cadena (`GA-REM-040` fase 6).
3. La cola exige `business_unit_id` del evento (derivación `predicado_de_evento`); sin
   cadena, el evento no aparece — su superficie es la bandeja.
4. Ruta nueva obliga a clasificación en `business_units/route_scope.py` (el boot falla
   con `AlcanceNoDeclarado` si falta) — clasificada como `MULTI_UNIDAD`.
5. Guard redundante de ámbito dentro de `get_event_actions` (defensa en profundidad
   sobre `_get_event`): se conserva; su retirada conjunta con la tenencia es lo que S3
   mide.

## 5 · Explícitos de política

- `GITHUB_ACTIONS = NOT_APPLICABLE_BY_OWNER_DECISION` (nunca PASS).
- `PUSH = REQUIRED_AFTER_LOCAL_CERTIFICATION`; este cierre se publica con
  `REMOTE_SHA_VERIFICATION` inmediata.
- `PUSH != DEPLOY` (auto-deploy no disponible: dependía de Actions retirados).

## 6 · UAT

Pendiente **acumulable** (no bloquea cierre técnico): casos de R-197 (bandeja por
estado, devolución con motivo, enlace al lote) se agrupan en el gate PRE-SAP junto a
los de T3–T9.

## 7 · Estado

- **R-197 = `CLOSED_TECHNICALLY`** (local) · KPI de procesos sin cambio (**0/17**).
- **Siguiente**: **R-207** (reverso — superficie autorizada) en T10, arranque automático.
