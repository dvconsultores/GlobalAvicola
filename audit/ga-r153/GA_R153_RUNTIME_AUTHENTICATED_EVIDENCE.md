# GA-R153 · EVIDENCIA RUNTIME AUTENTICADO (E2E)

Fecha: 2026-09-12 · Runtime `https://avicola.globaldv.net` · evidencia cruda: `evidence/runtime-e2e.json`, `evidence/runtime-population-invariant.json`, `evidence/runtime-population.json`, `evidence/cleanup.json`, capturas `ui-*.png`.

## 1 · Actores sintéticos (empresa 1)

- `e2e-r153-op-{semilla}` (concesión `grandparent`; operations create/read/update · lots read)
- `e2e-r153-ap-{semilla}` (review read/review · approvals approve/reject · corrections read/correct · lots/operations read)
- `e2e-r153-neg-{semilla}` (**sin** concesión; operations create)

## 2 · Resultado (corrida final: `runtime-e2e.json` — 0 fallos)

| Bloque | Comprobación | Resultado |
|---|---|---|
| E2E-01/02/03 | Registrar sin lote 201 (`lot_id null`); operador **ve** el detalle; cero lotes nuevos antes de aprobar | ✅ |
| E2E-04/05 | Aprobación → `lot_id=62` = **L-GP-2026-09** (tras 01/06/07/08 existentes); grandparent · mixed · active · `start_date`=llegada · granja del evento | ✅ |
| E2E-06 | Sin población al aprobar (bracketing: x9 aprobada, x10 rechazada ⇒ saldo exacto 9 = recepción 10 − mortalidad 1; si el import aportara 100, x10 hubiera pasado) | ✅ `runtime-population-invariant.json` |
| E2E-12/13 | Recepción (única entrada de población) registrada 201 y aprobada por P-07 | ✅ |
| E2E-17/18/19 | Lote manual 201; import **con** lote (legado) aprobada conserva su lote; L-GP pasa de 3→4 totales (solo el nuevo) ⇒ sin duplicar | ✅ |
| AC45 | Actor sin concesión → 403 «sin acceso operativo a la unidad 'grandparent'» | ✅ |
| UI | Detalle pendiente («Se creará al aprobar»), detalle aprobado (enlace `#62`→`/lots/62`), formulario (nota + lote opcional) | ✅ capturas |
| Limpieza | 6 eventos cancelados; 1 rechazo por saldo (87, se conserva); 21 usuarios sintéticos dados de baja + 8 concesiones revocadas; 29 roles sintéticos desactivados; catálogo **4×OFF** | ✅ `cleanup.json` |

## 3 · Incidencia de limpieza (resuelta y verificada)

`GET /api/v1/roles` **ignora el parámetro `search`** y devolvió todos los roles; el guion desactivó 14 roles legítimos. **Reparación inmediata**: `PUT /roles/{id} {is_active: true}` ×14 → 200; verificación posterior: «legítimos aún inactivos: []», «e2e aún activos: []» (`cleanup.json → reparacion_roles_legitimos`). Registrado como observación OBS-1 para el propietario (contrato de `search` en roles).

## 4 · Señales de despliegue

- `47ea484` (+C2b): bundle `index-DtzHNDMG.js` → **`index-DNXomVaS.js`**; health 200.
- `db8ae21` (solo backend): verificado por **comportamiento** — el evento pendiente #84 pasó de 404 a 200 para el operador (derivación por tipo viva).
