#!/usr/bin/env python3
"""OD-HATCH-V4-02 · enmienda de la spec 018 (desde la raíz del repo): §7 SUPERSEDED y nuevo §9."""
import sys
from pathlib import Path

ERR = []


def R(path, old, new, count=1):
    p = Path(path)
    s = p.read_text(encoding="utf-8")
    n = s.count(old)
    if n != count:
        ERR.append(f"{path}: se esperaban {count} apariciones y hay {n}: {old[:90]!r}")
        return
    p.write_text(s.replace(old, new), encoding="utf-8")


F = "specs/018-cutover-hatchery-v4-non-incubables/spec.md"
R(F, "## 7. AMENDMENT — OD-HATCH-V4-01 = RATIFIED (decisión Owner, 2026-11-21)\n",
  "## 7. AMENDMENT — OD-HATCH-V4-01 = RATIFIED (decisión Owner, 2026-11-21)\n\n"
  "> **SUPERSEDED (2026-11-26) por §9 · OD-HATCH-V4-02.** Nueva evidencia del usuario funcional: la fosa es "
  "**PRE-CARGA**. El texto de §7 se conserva por trazabilidad; sus reglas D-12, D-13, D-14 y AC-V4-15..18 ya no rigen.\n")

ANCLA = "**Estado §8 (2026-11-21):** O-15 **CLOSED**."
s = Path(F).read_text(encoding="utf-8")
i = s.find(ANCLA)
if i < 0:
    ERR.append("no se encontró el estado de §8")
else:
    fin = s.find("\n", i)
    fin = len(s) if fin < 0 else fin
    s = s[:fin] + """

## 9. AMENDMENT — OD-HATCH-V4-02 = RATIFIED · fosa PRE-CARGA (2026-11-26)

Mandato `GA-HATCHERY-V4-PIT-PRELOAD-DOMAIN-CORRECTION`. `ROOT_CAUSE = DOMAIN_CLARIFICATION` (no `PROGRAMMER_REGRESSION`): la implementación de §7 seguía una decisión Owner previa que ahora se reemplaza con nueva evidencia del usuario funcional.

**Evidencia (Maira Arellano, usuaria funcional):** «La cantidad de Huevos Fértiles enviados a Fosa se descuenta desde el principio de la cantidad de Huevos recibidos. Cuando se realiza la Carga de Huevos, esa cantidad ya fue descontada.»

**Decisión:** `OD-HATCH-V4-01 = SUPERSEDED` · `OD-HATCH-V4-02 = RATIFIED`. `fertile_eggs_to_pit` es una salida **PRE-CARGA**: huevos fértiles recibidos que se envían a fosa **antes** de cargarse en incubadora. Ya no forman parte de los huevos cargados. Sigue siendo un concepto distinto de los tres no incubables y **no** se suma a `eggs_discarded` (V4: `NOT_APPLICABLE`, no se deriva).

Sin cambio de schema ni de columnas: `template_version = v4`, `schema_id = CUTOVER_HATCHERY_V4`, sin migración (`fertile_eggs_to_pit` ya existe; cabeza Alembic sin cambios). Cambian semántica, validación, balance, presentación y documentación.

### Modelo de dos etapas (reemplaza el de §7)
```
ETAPA A (recepción, PRE-CARGA):  eggs_received → { oversized | dirty | broken | fertile_eggs_to_pit | eggs_set | pendiente }
                                 eggs_set + oversized + dirty + broken + fertile_eggs_to_pit ≤ eggs_received   (sin igualdad forzada)
ETAPA B (incubación, POST-CARGA): eggs_set → { eggs_transferred | en proceso }        eggs_transferred ≤ eggs_set
```
La fosa **no** vuelve a intervenir en la etapa B.

- **D-21 invariante pre-carga** (cutover): cada salida pre-carga KNOWN (`oversized`, `dirty`, `broken`, `fertile_eggs_to_pit`) `≤ eggs_received`; y `eggs_set + Σ(salidas pre-carga KNOWN) ≤ eggs_received` (desigualdad `≤`, nunca `≥` ni `<`). Con algún componente UNKNOWN solo se valida la cota con la suma conocida (si aun así supera lo recibido ⇒ `CONSISTENCY_MISMATCH`), sin declarar consistencia completa. El error se anota en el primer componente que rompe la cota (sin doble error).
- **D-22 se eliminan** `fertile_eggs_to_pit ≤ eggs_set` y `eggs_transferred + fertile_eggs_to_pit ≤ eggs_set`. Se conserva `eggs_transferred ≤ eggs_set` y las reglas de pollitos.
- **D-23 `eggs_in_process` V4** = `eggs_set − eggs_transferred` cuando ambos son KNOWN; si no, UNKNOWN. **No** resta la fosa (ya descontada antes de `eggs_set`).
- **D-24 saldo disponible para cargar** (derivado, preview y reconciliación): `eggs_available_to_set = eggs_received − eggs_set − oversized − dirty − broken − fertile_eggs_to_pit` **solo si todos** son KNOWN; si alguno es UNKNOWN, el saldo es UNKNOWN (`null`), nunca una cifra definitiva. En la reconciliación es `current.eggs_available_hatchery` (más recepciones − cargas post-corte).
- **D-25 BR-03 operativo** (saldo con el que el operativo valida una carga posterior al corte): `apertura = received − set − Σ(no incubables KNOWN) − fosa KNOWN`. Como en D-4, un componente UNKNOWN no se resta (el saldo operativo es cota superior; un saldo UNKNOWN bloquearía toda carga posterior). V3 no cambia (sus componentes nuevos son UNKNOWN).
- **D-26 preview** en dos etapas: PRE-CARGA = recibidos, extra grande, sucio, roto, fosa, cargados, «Saldo disponible para cargar (derivado)»; POST-CARGA = transferidos, «Huevos en proceso (derivado)». El agregado del summary sigue D-18 (O-15): una fila UNKNOWN ⇒ total UNKNOWN.
- **D-27 V3 intacta**: `CUTOVER_HATCHERY_V3` y su fórmula con `eggs_discarded` no cambian.
- **KPIs y reportes**: ningún KPI ni reporte fuera de la reconciliación de cargas iniciales consume `fertile_eggs_to_pit` (discovery por búsqueda exhaustiva); la reconciliación pasa a D-23/D-24.

| AC | Enunciado |
|---|---|
| AC-V4-21 | PIT-PRELOAD-01: 10000 / 8500 / 200 / 200 / 100 / fosa 200 ⇒ válido, saldo disponible 800. |
| AC-V4-22 | PIT-PRELOAD-02: suma pre-carga = recibidos ⇒ válido, saldo 0. |
| AC-V4-23 | PIT-PRELOAD-03: suma pre-carga > recibidos ⇒ `CONSISTENCY_MISMATCH` (también cuando solo la fosa rompe la cota). |
| AC-V4-24 | PIT-PRELOAD-04: fosa > recibidos ⇒ `CONSISTENCY_MISMATCH`. |
| AC-V4-25 | PIT-PRELOAD-05: fosa UNKNOWN ⇒ saldo disponible UNKNOWN; PIT-PRELOAD-06: fosa 0 conocida ⇒ válido y saldo numérico. |
| AC-V4-26 | PIT-POST-01: set 9000, transferidos 8000, fosa 500 ⇒ en proceso 1000 (nunca 500); PIT-POST-02: transferidos > cargados ⇒ DENY; PIT-POST-03: la fosa no afecta `transferred ≤ set` (fosa grande con transferidos = cargados es válida si la pre-carga cuadra). |
| AC-V4-27 | Sin doble conteo: 10000 / 8500 / 200 / 200 / 100 / 200, transferidos 8000 ⇒ saldo 800 y en proceso 500 (nunca 300). |
| AC-V4-28 | O-15 vigente: una fila con en proceso UNKNOWN ⇒ agregado UNKNOWN (nunca 0 ni suma parcial). |
| AC-V4-29 | La plantilla v4 regenerada describe la fosa como pre-carga («antes de la carga en incubadora»); sin «durante incubación/ovoscopia». |

**Estado §9:** ver `audit/ga-hatchery-v4-od02-pit-preload/CERTIFICATION.md`.""" + s[fin:]
    Path(F).write_text(s, encoding="utf-8")

if ERR:
    print("ERRORES:\n" + "\n".join(ERR))
    sys.exit(1)
print("OK: spec 018 §9 aplicada")
