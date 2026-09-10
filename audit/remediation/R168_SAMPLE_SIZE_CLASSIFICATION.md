# `R-168` · CLASIFICACIÓN DE `sample_size` («Muestra tomada») EN LA RECEPCIÓN

**WAVE B · tranche 8 · pre-flight** · 2026-09-10 · hallazgo del tranche 7 (P3): el formulario de recepción registra
`bird_movements[i].sample_size` y `BirdMovementSchema` no lo declara.

| Dimensión | Hallazgo |
|---|---|
| **Fuente** | Rec. §6 (captura móvil de la recepción de reproductoras): «**Muestra tomada**» — un dato, junto a «Peso promedio de hembras / machos». `docs/02 §3.5.4` (pesaje): «Cantidad aves pesadas». `Bases` p.2/12: «pesaje de una muestra representativa» (dato diario, pesaje) |
| **Semántica esperada** | tamaño de la muestra pesada en la recepción: **un dato por recepción** (§6 lo lista una vez); informativo de la medida (no la altera) |
| **Frontend actual** | recepción: un campo «Muestra» **por galpón** (`OperationFormPage.tsx:730`, `bird_movements.${i}.sample_size`); distribución: ídem (`:810`); pesaje: **evento** (`:590`, `sample_size`, «Aves pesadas») |
| **API actual** | `OperationalEventBase.sample_size` (evento) existe; `BirdMovementSchema` **no** declara `sample_size` → el valor por fila **se descarta en silencio** (`extra` no prohibido) |
| **BD actual** | `operational_events.sample_size INTEGER NULL` (evento); `bird_movements` sin columna |
| **Cálculo actual** | ninguno lee `sample_size` (grep `app/`: solo modelo y esquemas); no interviene en la evaluación de peso (`GA-REM-037` evalúa `avg_weight`) |
| **¿Pérdida de datos?** | **sí**: el operador captura la muestra y no se persiste (patrón `R-47`/`P0-14`: el cliente envía, el esquema descarta, la respuesta es `2xx`) |
| **¿Impacto en clasificación?** | ninguno (`B02` no depende de la muestra) |
| **¿Impacto en auditoría/evidencia?** | el dato exigido por el cliente no queda en el registro |
| **Dependencia** | ninguna (`B01`/`B02` cerrados; el campo de evento ya existe) |
| **Severidad** | P3 → **P2** (dato de captura exigido por el cliente, perdido en silencio; misma clase que `H360-B*`) |

## Clasificación

```
R-168 ............ A · ACTIVE DEFECT (pérdida silenciosa de un dato exigido) — corrección gobernada y mínima
acción ........... el formulario de recepción captura «Muestra tomada» UNA vez, en el campo de evento `sample_size` que ya existe
                   (como el pesaje); se retiran los campos por galpón que el esquema descarta (recepción y distribución: sin fuente
                   por galpón). Backend: sin cambio de modelo (control: `sample_size` de la recepción se persiste y se lee).
                   Spec: GA-REM-021 enmienda C §R-168. Sin migración.
no se hace ....... columna por fila en `bird_movements` (ninguna fuente pide la muestra por galpón); validación de tamaño mínimo
                   (ninguna fuente fija un mínimo)
```
