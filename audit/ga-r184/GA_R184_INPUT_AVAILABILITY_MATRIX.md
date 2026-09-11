# GA-R184 · MATRIZ DE DISPONIBILIDAD DE ENTRADAS

Comportamiento canónico por entrada ausente para `GET /reports/kpi/ipe/{lot_id}`. Todo lo siguiente es **contrato preexistente preservado** (R-184 no rediseña semántica de datos ausentes; solo elimina el 500 por tipos temporales).

| Entrada | ¿Nulable? | Ausencia | Respuesta | ¿500? | ¿Zero fabricado? |
|---|---|---|---|---|---|
| Lote (identificador) | — | lote inexistente | **404** `{"detail":"Lote no encontrado"}` | No | N/A |
| Lote fuera de alcance (empresa/BU/concesión) | — | no alcanzable | **404** (anti-enumeración) | No | N/A |
| `Lot.start_date` | Sí | NULL | `age_days = 30` (**legado preservado**) → 200 con el resto de cálculos | No | No (es la rama existente; documentada, no inventada) |
| `OpeningBalance` | Sí | sin fila | población inicial 0 ⇒ mortalidad 0 ⇒ **viabilidad 100.0** (contrato existente) | No | No: agregado vacío = 0 muertes (cierto); la viabilidad 100 % es consecuencia documentada del contrato de mortalidad vigente |
| Muertes aprobadas | — | ninguna | `total_deaths = 0` | No | No (agregado vacío = 0, matemáticamente cierto) |
| Pesajes (`avg_weight`) | Sí | sin pesajes | `avg_weight_g = 0.0` ⇒ ganancia 0 ⇒ **IPE 0.0** | No | No (agregado vacío = 0) |
| Alimento (`FeedMovement`) | — | sin alimento | FCR 0 ⇒ guarda `fcr > 0` ⇒ **IPE 0.0** | No | No (contrato existente; evita división por cero) |
| Edad resultante | — | `≤ 0` (lote del mismo día) | clamp a 1 (**preservado**) | No | No |

**Regla R184-AC17/18/21**: ninguna combinación de datos ausentes/vacíos produce 500, `ZeroDivisionError`, `NaN` ni `Infinity`. Los ceros provienen de **agregados vacíos** (ciertos por definición) o de guardas explícitas del contrato existente; **no se fabrica ningún valor positivo** ni se «arregla» la ausencia con un resultado inventado.

**Fuera de alcance (registrado)**: un rediseño «null cuando no calculable» o «error de validación de negocio» para datos ausentes **no está especificado** en el repositorio; cambiarlo alteraría el contrato de respuesta de consumidores actuales (frontend espera numérico). No se toca.
