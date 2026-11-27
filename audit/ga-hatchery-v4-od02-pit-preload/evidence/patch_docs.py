#!/usr/bin/env python3
"""OD-HATCH-V4-02 · manual de cargas iniciales (desde la raíz del repo): fosa PRE-CARGA."""
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


M = "docs/MANUAL_CARGAS_INICIALES.md"
R(M, "| `fertile_eggs_to_pit` | no | Huevos **fértiles a fosa**: huevos **ya cargados** en incubación y retirados del proceso en la incubación/ovoscopia, **antes de pasar a nacedora** (acumulado al corte). Es un movimiento **post-carga**: ≤ cargados, y transferidos + fosa ≤ cargados. Vacío = no se conoce; `0` = cero conocido. |",
  "| `fertile_eggs_to_pit` | no | Huevos **fértiles a fosa**: cantidad acumulada de huevos fértiles **recibidos** que se enviaron a fosa **antes de la carga** en incubadora (acumulado al corte). Esta cantidad **ya no forma parte de los huevos cargados**. Es una salida **pre-carga**: ≤ recibidos, y cargados + no incubables + fosa ≤ recibidos. Vacío = no se conoce; `0` = cero conocido. |")

R(M, "- **Balance**: `recibidos = cargados + no incubables + huevo aún por cargar` (más el huevo que quede sin clasificar). Los no incubables se restan **una sola vez**, del saldo recibido → cargado, **nunca** de lo cargado. Por eso `cargados + no incubables` **no puede superar** a los recibidos (si los supera, la fila se rechaza), y **la diferencia que queda es huevo recibido que aún no se ha cargado**: no es un error y no se fuerza a cero.",
  "- **Balance**: `recibidos = no incubables + huevos fértiles a fosa + cargados + huevo aún por cargar` (más el huevo que quede sin clasificar). No incubables y fosa se restan **una sola vez**, del saldo recibido → cargado, **nunca** de lo cargado. Por eso `cargados + no incubables + fosa` **no puede superar** a los recibidos (si los supera, la fila se rechaza; puede ser igual), y **la diferencia que queda es huevo recibido que aún no se ha cargado**: no es un error y no se fuerza a cero.")

s = Path(M).read_text(encoding="utf-8")
inicio = "### Huevos fértiles a fosa (regla ratificada · `OD-HATCH-V4-01 = RATIFIED`, 2026-11-21 · SPEC 018 §7)"
fin = "### «Generación» vs «Origen del huevo» (SPEC 009)"
if s.count(inicio) != 1 or s.count(fin) != 1:
    ERR.append("manual: no se encontró la sección de la fosa")
else:
    i, j = s.index(inicio), s.index(fin)
    s = s[:i] + """### Huevos fértiles a fosa (regla vigente · `OD-HATCH-V4-02 = RATIFIED`, 2026-11-26 · SPEC 018 §9)

> La regla anterior (`OD-HATCH-V4-01`, que situaba la fosa **después** de la carga) queda **SUPERSEDED** por nueva evidencia de la usuaria funcional: la fosa se descuenta **desde el principio** de los huevos recibidos; cuando se cargan los huevos, esa cantidad ya fue descontada.

- Los huevos fértiles a fosa son huevos **recibidos** que se envían a fosa **antes de cargarse** en incubadora. Es una salida **PRE-CARGA**, como los no incubables, pero es un concepto **distinto** de ellos: no se suma al total de no incubables ni a los huevos descartados (histórico V3).
- **Dos etapas, sin mezclar**:
  - **Pre-carga**: `recibidos → no incubables (extra grande, sucio, roto) · fosa · cargados · aún por cargar`. Regla: `cargados + extra grande + sucios + rotos + fosa ≤ recibidos` (puede ser igual; si la supera, la fila se rechaza). La fosa sola tampoco puede superar a los recibidos.
  - **Post-carga**: `cargados → transferidos · en proceso`. Regla: `transferidos ≤ cargados`. La fosa **no** interviene aquí.
- **Saldo disponible para cargar** = `recibidos − cargados − extra grande − sucios − rotos − fosa`, y **solo** cuando **todos** son conocidos; si falta alguno, el saldo queda **desconocido** (nunca se toma un vacío por `0`). Ejemplo: 10 000 recibidos, 8 500 cargados, 200 + 200 + 100 no incubables y 200 a fosa ⇒ saldo **800**.
- **Huevos en proceso** = `cargados − transferidos`, solo cuando ambos son conocidos. **No** se resta la fosa (ya se descontó antes de cargar). En el ejemplo, con 8 000 transferidos ⇒ en proceso **500** (no 300).
- En la operación diaria, la primera carga de incubación posterior al corte se valida contra el huevo recibido aún por cargar (BR-03), que descuenta no incubables y fosa **conocidos**; un dato desconocido no se descuenta.
- La vista previa muestra las dos etapas en orden: recibidos, no incubables, fosa, cargados y «Saldo disponible para cargar (derivado)»; luego transferidos y «Huevos en proceso (derivado)».

""" + s[j:]
    Path(M).write_text(s, encoding="utf-8")

if ERR:
    print("ERRORES:\n" + "\n".join(ERR))
    sys.exit(1)
print("OK: manual OD-HATCH-V4-02 aplicado")
