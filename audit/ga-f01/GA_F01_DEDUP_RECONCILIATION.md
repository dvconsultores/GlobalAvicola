# GA-F01 · RECONCILIACIÓN DE DUPLICADOS (dedup) — R-189

Fecha: 2026-09-12 · Tranche: remediación F-01 (GA-UAT-09 blocker) · Entrada: hallazgo F-01 del paquete UAT (`audit/ga-r153/uat/`).

## 1 · Síntomas (evidencia runtime)

| # | Síntoma | Evidencia |
|---|---|---|
| S1 | El alta de importación por interfaz envía `egg_storage_records: [{}]` por omisión → 422 `egg_storage_records[0].arrival_date` requerido | `referencia-walkthrough.json` (payload real), control backend [1] |
| S2 | La OC elegida no llega al campo tipado `sap_document_ref`; va a `extra_data.sap_order_ref` con el **id** (p.ej. `'33'`), no con el código | payload real; control backend [3] → 400 BR-22 |
| S3 | El `detail` de error (lista de objetos FastAPI) se pasa a render React → React #31 → pantalla en blanco | `F01-guardado-rechazado-422.png`, `pageerror` del journal |
| S4 | Misma carga `[{}]` afecta el alta de recepción | control backend [2] sobre recepción: 422 con `[{}]`, 201 con `[]` |

## 2 · Búsqueda de duplicados

Barrido sobre `audit/**` y `docs/**` (conceptos: egg storage / egg_storage / almacenamiento de huevos · purchase order · orden de compra · 422 · React #31 / React child · payload · serializador · import create / reception create):

| Candidato | Veredicto |
|---|---|
| `GA-REM-042` / `R-152` (plan de importación) | **No duplica**: certificó el contrato backend del plan (BR-22) por API; no cubre el serializado del formulario ni la OC tipada. |
| `GA-TD-014` / `GA-REM-035 AC13` (campo tipado `sap_document_ref`) | **Parcial**: arregló el bloque `bird_exit` (escribe ambos campos); el bloque compartido superior (import/recepción no-cría/despachos) **nunca recibió el mismo arreglo** → S2 es la misma clase de defecto en otro bloque. Se **extiende** el arreglo canónico (mismo campo, misma semántica), no se abre otro camino. |
| `R-169` (sin tolerancias en recepción) · `R-168` (muestra) | No relacionados. |
| `R180` (lot_id de `egg_storage` ajeno) | No relacionado: ownership del lote en el registro; no el envío `[{}]`. |
| `H360-…` / `WAVE_1` (egg_storage SPEC_GAP) | Brecha de especificación del **evento** de almacenamiento; no el defecto del formulario. |
| Residuales frontend (`RES-*`, FVA-17) | FVA-17 verificó el plan de importación; no detectó este defecto del serializador (el flujo de alta por UI no se ejercía en aceptación). No es una fila existente. |

**Conclusión**: no existe un hallazgo que posea F-01 en su totalidad; S1-S4 son **un solo defecto de contrato de formulario** (serializado/mapeo seguro de un mismo onSubmit) con dos observaciones adyacentes.

## 3 · Decisión

- **F-01 = UN hallazgo nuevo coherente** (opción C del encargo): defecto de contrato del formulario de operaciones en el camino de guardado (payload por omisión + mapeo de OC + presentación del error), con alcance import/recepción (mismo `onSubmit`).
- **Finding canónico: `R-189`** — siguiente libre verificado (máximo usado en `audit/`/`docs/`: `R-188`; sin reserva previa de `R-189`).
- Severidad: **P1** (bloquea el flujo normal del usuario y la aceptación del propietario; pantalla en blanco ante validación; import y recepción).
- Observaciones adyacentes **no implementadas aquí** (candidatas, registradas, fuera de alcance): 
  - **F-01b** · `egg_reception_hatchery` no captura `arrival_date` → su registro de almacenamiento no puede satisfacer el esquema (latente, otra superficie).
  - **F-01c** · `POST /operations` con `egg_storage_records` completo en un evento sin lote → **500** (modelo `egg_storage.lot_id` NOT NULL vs `data.lot_id=None` en servicio). Sonda sintética (no alcanzable por la UI hoy). Requiere hallazgo propio si el propietario lo prioriza.

## 4 · Mapeo

```
F-01 → R-189 (canónico) · P1 · afecta: alta de importación de abuelas y alta de recepción por interfaz (todas las altas del asistente con la carga por omisión) ·
         UI: OperationFormPage (serializador + bloque OC + manejo de error) · Error UX: helper compartido getErrorMessage ·
         API: POST /api/v1/operations · Procesos: P-01/P-02 (alta), P-07 indirecto (sin alta no hay aprobación), R-153/OD-25 (flujo visible).
```

## 5 · Ampliación F-01d (post-C2, subsanada en este tranche)

La re-ejecución del E2E tras C2 destapó una **tercera superficie del mismo defecto de serializado**:
`feed_movements: [{}]` y `hatchery_params: [{}]` seguían viajando (C2 solo cubrió almacenamiento y
filas de aves). La fila vacía se persiste (default sin validar) y el detalle del evento devuelve 500
al leerla (`FeedMovementSchema.quantity_kg gt=0`). Es el **mismo hallazgo R-189** (serializador
incompleto por clave + asimetría del esquema entre alta y lectura), no un hallazgo nuevo; se subsana
como extensión con anexo propio: `GA_F01D_SUBSANACION_ANNEX.md` (AC-F01D-01…10).
