#!/usr/bin/env python3
"""OD-HATCH-V4-02 · ajuste de datos de AC-V4-09/10 al dominio pre-carga (desde la raíz del repo)."""
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


T4 = "backend/tests/test_cutover_hatchery_v4.py"
R(T4, """        fila_incubadora("ACV4-APL-1", eggs_non_incubable_oversized=500, eggs_non_incubable_dirty=300,
                        eggs_non_incubable_broken=200, fertile_eggs_to_pit=25),""",
  """        # §9 D-21: la fosa es PRE-CARGA ⇒ 8975 + 500 + 300 + 200 + 25 = 10000 recibidos.
        fila_incubadora("ACV4-APL-1", eggs_set=8975, eggs_non_incubable_oversized=500, eggs_non_incubable_dirty=300,
                        eggs_non_incubable_broken=200, fertile_eggs_to_pit=25),""")
R(T4, """    `eggs_in_process` no los toca (9000 = `set − transferred − fosa` con fosa 0 KNOWN; SPEC 018 §7
    D-12): restarlos también ahí sería el doble conteo.""",
  """    `eggs_in_process` no los toca (9000 = `set − transferred`; SPEC 018 §9 D-23): restarlos también
    ahí sería el doble conteo.""")

if ERR:
    print("ERRORES:\n" + "\n".join(ERR))
    sys.exit(1)
print("OK: AC-V4-09/10 ajustados")
