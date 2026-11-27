#!/usr/bin/env python3
"""BR-03 UNKNOWN FAIL-SAFE · completa el único reemplazo de patch_backend.py que falló por ancla no única
(`from typing import Optional` en validators.py). Desde la raíz del repo."""
import sys
from pathlib import Path

p = Path("backend/app/operations/validators.py")
s = p.read_text(encoding="utf-8")
old = "from datetime import date\nfrom sqlalchemy import case, func, select\n"
if s.count(old) != 1:
    print(f"ERRORES: ancla con {s.count(old)} apariciones"); sys.exit(1)
p.write_text(s.replace(old, "from datetime import date\nfrom typing import Optional\n\nfrom sqlalchemy import case, func, select\n"), encoding="utf-8")
print("OK: import Optional añadido")
