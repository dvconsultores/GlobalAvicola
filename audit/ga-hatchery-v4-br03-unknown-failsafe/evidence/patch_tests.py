#!/usr/bin/env python3
"""BR-03 UNKNOWN FAIL-SAFE · tests (desde la raíz del repo): suite nueva y los dos tests que fijaban la cota."""
import shutil
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


shutil.copyfile("audit/ga-hatchery-v4-br03-unknown-failsafe/evidence/test_cutover_hatchery_v4_br03_unknown.py",
                "backend/tests/test_cutover_hatchery_v4_br03_unknown.py")

OD2 = "backend/tests/test_cutover_hatchery_v4_od02.py"
R(OD2, """    \"\"\"AC-V4-25: fosa vacía ⇒ saldo disponible UNKNOWN (nunca 1000); `dirty` UNKNOWN igual.

    En proceso no depende de la fosa: 8500 − 0. BR-03 operativo no resta lo desconocido (D-25).
    \"\"\"""", """    \"\"\"AC-V4-25: fosa vacía ⇒ saldo disponible UNKNOWN (nunca 1000); `dirty` UNKNOWN igual.

    En proceso no depende de la fosa: 8500 − 0. BR-03 operativo comparte el UNKNOWN (§10 · D-28/D-30:
    la suma conocida es una cota, no un saldo; reemplaza a D-25).
    \"\"\"""")
R(OD2, """    assert saldos["PIT-PRE-05"] == 10000 - 8500 - 500           # fosa UNKNOWN no se resta
    assert saldos["PIT-PRE-05B"] == 10000 - 8500 - 300 - 200     # dirty UNKNOWN no se resta; la fosa sí""",
  """    assert saldos["PIT-PRE-05"] is None                          # fosa UNKNOWN ⇒ saldo UNKNOWN (§10)
    assert saldos["PIT-PRE-05B"] is None                         # dirty UNKNOWN ⇒ saldo UNKNOWN (§10)""")

T4 = "backend/tests/test_cutover_hatchery_v4.py"
R(T4, """    ahí sería el doble conteo. Con un componente UNKNOWN el saldo BR-03 es
    cota superior.""", """    ahí sería el doble conteo. Con un componente UNKNOWN el saldo BR-03 es UNKNOWN (SPEC 018 §10):
    la suma conocida es una cota superior y no autoriza cargas.""")
R(T4, """        # (c) `dirty` UNKNOWN no se resta ni se inventa: 10000 − 9000 − 500 = 500 (cota superior)""",
  """        # (c) `dirty` UNKNOWN: el saldo es UNKNOWN (la cota 10000 − 9000 − 500 = 500 no es un saldo)""")
R(T4, """        assert await get_hatchery_egg_balance(s, lotes["ACV4-BC-C"]) == 500""",
  """        assert await get_hatchery_egg_balance(s, lotes["ACV4-BC-C"]) is None""")
R(T4, """    assert rec["ACV4-BC-C"]["current"]["eggs_available_hatchery"] is None  # cota superior, sin número inventado""",
  """    assert rec["ACV4-BC-C"]["current"]["eggs_available_hatchery"] is None  # UNKNOWN, sin número inventado""")

if ERR:
    print("ERRORES:\n" + "\n".join(ERR))
    sys.exit(1)
print("OK: tests BR-03 UNKNOWN aplicados")
