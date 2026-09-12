# GA-R153 · CERTIFICACIÓN TÉCNICA

Fecha: 2026-09-12 · Commits `9651550` (C1) · `47ea484` (C2) · `db8ae21` (C2b) · Deploy vivo (`index-DNXomVaS.js` + verificación de comportamiento del backend).

## 1 · Veredicto

**R-153 — CERTIFICADO TÉCNICAMENTE (`CLOSED_FUNCTIONALLY_CERTIFIED`), Aceptación del propietario PENDIENTE (UAT).**
**OD-25 — RATIFIED_IMPLEMENTED; OWNER_ACCEPTANCE PENDING.**

La promesa del propietario (opción B) se cumple extremo a extremo: registrar la importación **sin lote** → la **aprobación `P-07`** crea el lote `L-GP-{año}-{nn}` (uno exacto, sin poblar) → la **recepción** sigue siendo la única entrada de población → la **vía manual** y el **legado con lote** quedan intactos.

## 2 · Invariantes verificados

| Invariante | Verificación |
|---|---|
| UNA importación aprobada ⇒ UN lote; devuelta/rechazada ⇒ 0 | Suite AC06-08/28/29/31/32 · E2E |
| El import **no puebla** | Bracketing runtime (x9 ✅ / x10 ❌ ⇒ saldo 9 exacto) |
| La recepción puebla **una vez** | E2E-12/13 · suite AC16-21 |
| Código determinista por empresa/año, unicidad global respetada | Runtime 01/06/07/08/**09** · suite AC09/10 · lock+savepoint |
| Legado (con lote) no duplica | E2E-18/19 · suite AC27 |
| `BR-22` intacta (plan, OC, proveedor/transporte, cuadres) | E2E-01 payload real · suite |
| Falla cerrado (sin concesión, BU OFF, otra cadena) | E2E-AC45 · suites AC45/46/59 |
| Sin migración · sin endpoint nuevo · sin permiso nuevo | diff `47ea484`/`db8ae21` |

## 3 · Observaciones al propietario (no bloqueantes; ninguna exige decisión en este tranche)

- **OBS-1 · `GET /roles` ignora `search`** — devuelve todos los roles; provocó (y se corrigió) la desactivación de 14 roles legítimos durante la limpieza. Contrato de filtrado a revisar cuando toque (Wave B/plataforma); se documenta aquí y en el ledger.
- **OBS-2 · mensaje de `BR-01`** — «saldo disponible (0)» al rechazar mortalidad x10 cuando el límite efectivo era 9; mensajería a revisar.
- **OBS-3 · sesión UI del admin global sin empresa efectiva** — detalles recién creados dan 404 hasta `switch-company`; comportamiento conocido de sesión, no de R-153.
- **OBS-4 · prerequisito implementado (derivación por tipo)** — la importación sin lote no podía alcanzar su aprobación (los eventos sin clasificar viven fuera del alcance y la bandeja fase-6 no tiene superficie operativa para clasificarlos: sus habilitaciones no exponen id por API/UI). Se añadió el tercer origen de derivación **nombrado** en `classification.py` (cadena del tipo, inequívoca por `BR-22`): visible para `grandparent`, fuera de la bandeja, cerrado a otras cadenas (AC58/59; fase-6: inspecciones intactas). Sin esto, OD-25(B) era inoperable.
- **OBS-5 · cancelación de recepción (evento 87)** — rechazada por `R-130` («dejaría el saldo…»); coherente, se conserva registrada (ledger).

## 4 · Límites declarados

Ejecución local de la suite PG (PostgreSQL no disponible en esta máquina; CI la ejecuta) · concurrencia multi-proceso no provocada en runtime (primitiva compartida con `R-130`, cubierta en CI).

---

## Addendum 2026-09-12 · GA-UAT-09 (preparación de la aceptación del propietario)

1. **`SPEC_DEVELOPMENT_SEQUENCE_DEVIATION` (C2b / `db8ae21`)** — la enmienda de spec/AC58-59/C26 se formalizó **después** de la implementación (llegó en `8564364`, C3); los tests AC58/59 viajaron con la implementación. Desviación **de secuencia documental**, declarada en `uat/GA_OWNER_UAT_R153_GOVERNANCE_PREFLIGHT.md` y en `uat/GA_OWNER_UAT_R153_EVIDENCE.md §B`. No se modifica producto por esta causa.
2. **OBS-1 = `DATA_RESTORATION_ONLY`** — la reparación del incidente de roles fue únicamente de datos (`PUT /roles/{id}` `is_active`); ningún archivo de `auth`/roles fue tocado por los commits del tranche. Determinación y evidencia en la nota de preflight.
3. **Hallazgo F-01 (nuevo, P1) descubierto en la verificación de referencia del UAT** — el alta de la importación **desde la interfaz** es rechazada (registro vacío de almacenamiento de huevos en el payload por omisión) y, además, el mensaje de error del servidor **rompe el render** (pantalla en blanco); una segunda brecha impide que la orden de compra elegida llegue al campo tipado que la importación valida. La misma causa de carga por omisión afecta al alta de recepción. Origen **preexistente del asistente** (default `[{}]` desde `a43507b`, 2026-06-26; esquema estricto desde el baseline) — **no introducido por R-153** (sus commits no tocan el guardado del asistente ni los esquemas de almacenamiento de huevos).
4. **Efecto sobre el estado**: la **certificación técnica de R-153 se mantiene** (mecanismo certificado por API/E2E runtime: 0 fallos), pero la **aceptación visible del propietario queda BLOQUEADA** hasta corregir F-01 por el cauce `FINDING → SPEC → AC → IMPLEMENTACIÓN` (sin hotfix dentro de R-153). Estado: `R-153 CLOSED_FUNCTIONALLY_CERTIFIED` · `OD-25 RATIFIED_IMPLEMENTED` · `OWNER_ACCEPTANCE: BLOCKED_BY_F-01 (PENDING)`.
5. Paquete: `audit/ga-r153/uat/` (guía, observaciones, evidencia A-H, índice de capturas C/F, ledger, preflight, journal y capturas).
