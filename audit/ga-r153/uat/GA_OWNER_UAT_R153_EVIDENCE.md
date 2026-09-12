# GA-UAT-09 · EVIDENCIA DEL PROPIETARIO — R-153 / OD-25

Fecha: 2026-09-12 · Runtime `https://avicola.globaldv.net` · Bundle `index-DNXomVaS.js` · HEAD `8564364` (== remoto; árbol limpio). **Evidencia de ingeniería separada del juicio del propietario (sección G vacía).**

## A · PRECONDICIONES

- Rama `main` · HEAD `8564364` == `origin/main` · worktree limpio · **producto sin cambios desde la certificación** (ningún commit posterior; sin archivos de producto modificados).
- Runtime: health 200 · bundle certificado · backend con el comportamiento certificado de R-153.
- Smoke: Vitest **295/295** · TypeScript **PASS** · Build **PASS**.
- Fixture sintético: 2 actores (operador/aprobador de abuelas, empresa 1), unidad Progenitoras **ON**, concesiones vigentes, RBAC suficiente para el viaje normal. Credenciales efímeras en `~/ga_uat09_credentials.txt` (600; nunca en el repo/evidencia).

## B · PREFLIGHT DE GOBERNANZA

**G-01 · cronología C2b (`db8ae21`)** — *¿la spec/AC58-59 se enmendó ANTES de la implementación?* **NO.**
Evidencia git: `db8ae21` toca únicamente `backend/app/business_units/classification.py` + `backend/tests/test_r153_import_lot_auto.py` (0 archivos `.md`); la enmienda de spec/AC58-59 + clarificación C26 + checklist llegó **después**, en `8564364` (C3; el diff de la spec contiene AC58). Los tests AC58/59 viajaron en el mismo commit que la implementación.
→ **`SPEC_DEVELOPMENT_SEQUENCE_DEVIATION` declarada** (origen: descubrimiento durante el E2E runtime de certificación; corrección documental posterior). **No se cambia producto por esto**; declarada también en el historial de certificación (`GA_R153_CERTIFICATION.md` → Addendum GA-UAT-09).

**G-02 · incidente OBS-1 (roles)** — *¿qué significa «reparado»?* **DATA_RESTORATION_ONLY.**
- `GET /api/v1/roles` **no tiene el parámetro `search`** en su contrato (`backend/app/auth/router.py:178` — `list_roles` sin filtro; siempre lista todo). El guion de limpieza asumió un filtro inexistente.
- La reparación fue **solo datos**: `PUT /roles/{id} {is_active:true}` sobre los 14 roles legítimos; verificación viva: 14 legítimos activos, 0 inactivos, 0 roles sintéticos visibles.
- **Ningún archivo** de `auth`/roles/router/frontend de roles fue tocado por ningún commit del tranche (`9651550`, `47ea484`, `db8ae21`, `8564364`).
→ **Sin cambio de producto fuera de alcance; UAT habilitada por este check.**

## C · FIXTURE DEL PROPIETARIO

Nuevo contexto sintético (no se reutilizó el lote de la certificación): actores `uat09-op-*` / `uat09-ap-*` (empresa 1), unidad Progenitoras ON, OC candidata `PO-C001-GPR-0001` (OC “Progenitoras Cría – recepción de abuelas”). **Ninguna importación preexistente**: el caso 1 parte de cero. Detalle en `GA_OWNER_UAT_R153_LEDGER.md`.

## D · VERIFICACIÓN DE REFERENCIA (ejecutada por ingeniería antes del propietario)

Journal: `evidence/referencia-walkthrough.json` · capturas: `C01`, `F01`, `C08`, `C08b`.

| Paso | Resultado |
|---|---|
| Abrir alta de importación (escritorio 1440×900) | ✔ formulario con lote **no obligatorio** + nota «Si no selecciona un lote, se creará automáticamente al aprobar la importación.» (`C01`) |
| Seleccionar OC / proveedor / transporte / plan / ♂40 ♀60 | ✔ seleccionables y visibles |
| **Guardar** | ✖ **FALLA**: la petición de alta es rechazada por el servidor (422) → el manejo del error **rompe el render** (React #31) → **pantalla en blanco** (`F01`; `pageerror` en journal) |
| Traza de red | `POST /operations → 422`; detalle: `egg_storage_records[0].arrival_date` requerido (el formulario envía `[{}]` por defecto) |
| Causa 2 (encadenada) | El payload **no incluye la OC en el campo tipado** que valida la importación (solo `extra_data.sap_order_ref`) → aun sin el 422, el servidor respondería «declare la orden de compra SAP» (BR-22). Reproducido por API |
| Alcance de la causa 1 | La misma carga defectuosa afecta **cualquier alta del asistente con el registro vacío** — verificado también en la recepción (422 con `[{}]`, aceptada con `[]`) |
| Móvil 390×844 | ✔ nota y formulario visibles, sin desbordes horizontales (`C08`, `C08b`) |
| Consola fatal | 1 error de render (React #31) · 0 respuestas ≥500 |

**Veredicto de referencia: UAT-01 = FAIL (bloqueante). UAT-02…06 no alcanzables por dependencia.** `F-01` registrado como candidato nuevo (P1).

## E · CASOS DEL PROPIETARIO

| Caso | Estado |
|---|---|
| UAT-01 registrar sin lote | **FAIL** (verificado en la referencia; reproducible) |
| UAT-02 sin lote antes de aprobar | NO ALCANZABLE (depende de 01) |
| UAT-03 aprobar crea el lote | NO ALCANZABLE |
| UAT-04 datos del lote | NO ALCANZABLE |
| UAT-05 sin aves antes de recepción | NO ALCANZABLE |
| UAT-06 recepción carga aves | NO ALCANZABLE (misma causa bloquea su alta) |
| UAT-07 vía manual | PARCIAL — disponible y visible; flujo completo no ejecutable |

## F · OBSERVACIONES

Ver `GA_OWNER_UAT_R153_OBSERVATIONS.md` (F-01 P1; el resto pendiente del propietario).

## G · DECISIÓN DEL PROPIETARIO

⏳ **PENDIENTE** — se responde con A) / B) / C) sobre R-153 / OD-25 (pregunta abajo).

## H · LIMPIEZA

Pendiente **después** de la decisión (§37 del encargo). Estado actual: sondas de verificación canceladas (recepción de sonda 97 ✓; el 87 pertenece al ledger del tranche anterior y sigue retenido por R-130); fixture y concesiones **permanecen vivos** para que el propietario pueda reproducir; sin secretos en el repo.
