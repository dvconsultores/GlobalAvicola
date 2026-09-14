# GA · T10 CERTIFICATION — Revisión y reverso (R-197 · R-207)

Fecha: 2026-09-14 · Programa: GA PRE-SAP · Política: **AOD-29 Clarification 01**
(certificación **local** con gates reproducibles; **GitHub Actions retirado**;
**push requerido** a `origin/main` con verificación de SHA remoto).

## 1 · Paquetes y commits

| Paquete | RED | IMPL (`LOCAL_CERTIFIED_SHA`) | Cierre | Push |
|---|---|---|---|---|
| R-197 · bandeja por estado + historial por evento + resultado de aprobación | `afea748` | **`10f7b53`** (+C2b `e21629a`) | cert `f128218` · ev `6baf4ae` | sincronizado |
| R-207 · superficie de reverso (solicitar/seguir/mostrar) | `3eb1193` | **`4e8d999`** | cert `00d4bea` | **`00d4bea`** |

`HEAD` remoto tras el cierre: **`00d4bea`** · `REMOTE_SHA_MATCH = PASS` (cada push verificado
con `git ls-remote`; fast-forward, sin force).

## 2 · Gates locales (PASS)

| Gate | Resultado |
|---|---|
| R-197 targeted BE / FE | 10/10 · 10/10 |
| R-197 suite BE completa | **1373 passed / 0 failed / 49 skipped** (20:56) |
| R-197 guardianes | 52 passed (recuento de rutas `/api/` = **213**, 212→213) |
| R-197 suite FE completa | **429/429** |
| R-207 targeted FE | **4/4** |
| R-207 suite FE completa | **433/433** |
| R-207 BE | **no requerida** (`BACKEND_DIFF = 0`; SPEC §10 “impacto backend ninguno”) |
| `npm run build` (`tsc -b && vite build`) | **EXIT 0** en ambos paquetes |

## 3 · Sensibilidad (mutación + restore desde SHA explícito)

- **R-197** S1-S4 (BE) y F1-F6 (FE): RED quirúrgica 1:1 por test (S1 agrupa 01/04/04b,
  control 02 intacto; S3 agrupa 06b/06c). Restore `--source=10f7b53`.
- **R-207** R1-R5: gate · validación · enlace contrapartida · mapa central · payload —
  1:1 por test. Restore `--source=4e8d999`.
- Post-mutation: R-197 BE 10/10 · FE 10/10; R-207 FE 4/4; worktree limpio.

## 4 · Hallazgos del paquete (registrados / resueltos)

1. **R-197 · fixture BE**: `EventType` de mortalidad = `mortality_recording`;
   `ApprovalAction` sin `company_id` (tenencia por evento); la cola exige
   `business_unit_id` derivable; ruta nueva obliga a clasificación en `route_scope.py`
   (boot falla con `AlcanceNoDeclarado` si falta).
2. **R-197 · defensa en profundidad**: `get_event_actions` mantiene el predicado de
   ámbito sobre `_get_event`; la sensibilidad S3 mide su retirada conjunta con la
   tenencia (documentado en la certificación del paquete).
3. **R-207 · harness**: el primer borrador del AC-01 renderizaba dos copias montadas
   (la sesión reactiva añadía el botón a la primera); corregido con `unmount` entre
   renders — el contrato (gate) no cambió.
4. **R-207 · sin backend**: el motor OD-19 ya exponía solicitud/contrapartida/aprobación;
   la UI hace alcanzable la capacidad (RES-04) sin endpoint, permiso ni migración nuevos.

## 5 · Explícitos de política

- `GITHUB_ACTIONS = NOT_APPLICABLE_BY_OWNER_DECISION` (nunca PASS).
- `PUSH = REQUIRED_AFTER_LOCAL_CERTIFICATION`; `REMOTE_SHA_VERIFICATION = PASS`.
- `PUSH != DEPLOY` (auto-deploy no disponible: dependía de Actions retirados).

## 6 · UAT

Pendiente **acumulable** (no bloquea cierre técnico): R-197 (3 casos: bandeja por
estado, devolución con motivo, enlace al lote) · R-207 (4 casos: solicitar · contrapartida
· aprobar · estado/enlace; móvil/EN). Se agrupan en el gate PRE-SAP (U6).

## 7 · Estado

- **T10 = `CLOSED_TECHNICALLY`** · KPI de procesos sin cambio (**0/17**) · SAP
  `NOT_STARTED`.
- **R-142**: condición **no cumplida** — `AOD-17` (semántica `CORRECTED` multinivel)
  permanece `SCHEDULED` como decisión del propietario (lote §25); queda diferida y
  documentada, sin bloquear el cierre de T10.
- **Siguiente**: **T11** (residuales FE: `R-213`, `R-212`, `R-218`, `R-220`) — arranque
  automático. Después **T14** (GA-REQ-061) según placement, → T12 → T13.
