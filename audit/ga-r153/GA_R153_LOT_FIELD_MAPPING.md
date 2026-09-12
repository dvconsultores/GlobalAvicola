# GA-R153 · MAPEO DE CAMPOS DEL LOTE AUTOCREADO

Fecha: 2026-09-12 · Modelo: `masters/models.py:278-315` + migración `b53bbe02a476` (nullability). Regla: **no se inventa** ningún valor de negocio; lo no derivable queda `NULL` (nullable canónico).

| Campo del lote | ¿Obligatorio (NOT NULL)? | Fuente canónica | Valor en el lote autocreado | ¿Derivable? | Nota |
|---|---|---|---|---|---|
| `lot_code` | **SÍ** (único global) | generado (`R-153`) | `L-GP-{año}-{nn}` (ver análisis de secuencia) | SÍ | formato de la decisión OD-25 |
| `company_id` | no (se fija) | `event.company_id` | empresa de la importación | SÍ | misma empresa siempre (AC44/49) |
| `bird_type` | no | dominio del evento | `grandparent` | SÍ | BR-22: la importación ES de abuelas |
| `sex` | no | `bird_movements` del plan (♂>0 y ♀>0) | `mixed` si ambos; `male`/`female` si uno; `NULL` si ninguno | SÍ | sin inventar |
| `start_date` | no | `import_plan.arrival_date` | fecha de llegada (00:00) | SÍ | regla OD-25 |
| `farm_id` | no | `event.farm_id` (si el operador fijó granja) | granja de la importación o `NULL` | SÍ (si existe) | no se inventa granja |
| `house_id` | no | `event.house_id` | galpón del evento o `NULL` | SÍ (si existe) | íd. |
| `genetic_line_id` | no | — | `NULL` | NO | el plan no captura genética; no se fabrica |
| `breed_id` | no | — | `NULL` | NO | íd. |
| `weight_curve_id` | no | — | `NULL` | NO | depende de línea genética; se resolverá por flujo normal |
| `area_id` | no | — | `NULL` | NO | OD-21 no se fuerza (inactivo ≠ elegible); ausencia ≠ invento |
| `planned_close_date` | no | — | `NULL` | NO | se fija en el flujo normal |
| `hatchery_purpose` | no | — | `NULL` | N/A | dominio Progenitoras |
| `status` | **SÍ** (default) | default canónico | `active` | SÍ | igual que el alta manual |
| `activation_type` | no (default) | default canónico del alta | `normal` | SÍ | íd. |
| `end_date` | no | — | `NULL` | — | cierre normal |
| `created_at/updated_at` | server | server | server | — | — |

**Conclusión:** único campo NOT NULL no natural = `lot_code` ⇒ se genera; todo lo demás tiene fuente canónica o queda NULL legítimo. **No hay bloqueo por campo no derivable.**
