#!/usr/bin/env python3
"""O-23 · manual de usuario y estado en la spec (desde la raíz del repo), tras la implementación."""
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


R("docs/MANUAL_USUARIO.md",
  "Una corrección tampoco puede **vaciar** el lote de la vacuna ni la causa de una mortalidad o un descarte.\n",
  "Una corrección tampoco puede **vaciar** el lote de la vacuna ni la causa de una mortalidad o un descarte.\n\n"
  "Si un dato de catálogo **quedó vacío** al registrar (por ejemplo, una recepción sin proveedor), puedes "
  "**completarlo** con una corrección: elige el campo, verás «Valor original: Sin valor», y selecciona el "
  "registro correcto de la lista. La lista solo muestra registros **activos** de tu empresa, con su código y "
  "nombre (por ejemplo «PROV-001 — Proveedor ABC»). Solo se ofrecen los campos que corresponden a esa "
  "operación (una recepción ofrece proveedor, no vacuna). El historial lo muestra como «Proveedor: Sin valor → "
  "\"Proveedor ABC\"».\n")

R("specs/020-uat-breeder-cria-s2/spec.md",
  "`O-26`, `O-27`, `O-11`, `O-12`, `O-16` y `O-19` quedan fuera de este ciclo.",
  "`O-26`, `O-27`, `O-11`, `O-12`, `O-16` y `O-19` quedan fuera de este ciclo.\n\n"
  "**Estado (26-11-2026):** `IMPLEMENTADO` en `develop` — `backend/app/corrections/service.py` "
  "(`MAESTROS_POR_TIPO_DE_EVENTO`, `_maestro_aplica`, `_exigir_maestro_activo`), `CorrectionForm.tsx`, "
  "`ReviewDetail.tsx`, `utils/correctionFields.ts` y `corrections.noValue` (es/en). Sin migración. "
  "Certificación: `audit/ga-uat-breeder-cria-s2-o23-2026-11-26/CERTIFICATION.md`.")
R("specs/020-uat-breeder-cria-s2/spec.md",
  "`O-23` (asignar por corrección un maestro a un campo que estaba vacío) sigue abierta.",
  "`O-23` (asignar por corrección un maestro a un campo que estaba vacío) sigue abierta — cerrada después por §7.")

if ERR:
    print("ERRORES:\n" + "\n".join(ERR))
    sys.exit(1)
print("OK: docs O-23 aplicados")
