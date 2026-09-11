# GA-R186 · MATRIZ DE ENTRADAS G-05

Contrato **preexistente preservado** (R-186 solo elimina el TypeError temporal). Nota: a diferencia de G-06, el fallback de FCR es `or 1` y el peso no filtra tipo de evento.

| Entrada | ¿Requerida? | Ausencia | Respuesta | ¿500? | ¿Cambia R-186? |
|---|---|---|---|---|---|
| `lot_id` | **Sí** (Query requerido) | sin parámetro | 422 (validación FastAPI) | No | No |
| Lote existe/alcanzable | Sí | inexistente / ajeno / fuera de alcance | **404** «Lote no encontrado» (`_exigir_lote`) | No | No |
| `Lot.start_date` | No (nulable) | NULL | `age_days = 30` (fallback legado) | No | **Sí (corrige TypeError cuando hay valor)** |
| `OpeningBalance` | No | sin fila | población 0 ⇒ mortalidad 0 ⇒ viabilidad **100.0** | No | No |
| Pesajes (`avg_weight`) | No | sin pesajes | `avg_weight_g = 0` ⇒ PI 0 | No | No |
| Alimento | No | sin alimento | `feed_conversion_ratio` 0 ⇒ **fcr = 1** (`or 1`) ⇒ PI calculado con placeholder 1 (contrato vigente) | No | No |
| Edad ≤ 0 (mismo día / futura) | — | — | guarda `(age_days × fcr) > 0` ⇒ PI **0** | No | No |
| FCR 0 explícito | — | — | nunca (0 → `or 1`); guarda adicional si ambos 0 | No | No |

## Agregación (verificación, no invención)

`lot_id: int = Query(...)` **requerido** en el router ⇒ **endpoint de un solo lote**. No existe colección multi-lote ⇒ las AC de colección (R186-AC17…AC22, E2E-06/07/08 de colección) quedan **N/A con esta prueba** (el caso «lote incompleto» sí aplica como lote único con datos ausentes → controlado).

**Regla de oro**: ningún estado vacío/ausente produce 500, NaN ni ∞; los ceros provienen de agregados vacíos (ciertos) o de guardas explícitas del contrato; **no se inventan valores nuevos**.
