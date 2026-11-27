#!/usr/bin/env python3
"""BR-03 UNKNOWN FAIL-SAFE · manual, docs de contrato y E2E (desde la raíz del repo)."""
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


M = "docs/MANUAL_CARGAS_INICIALES.md"
R(M, "- En la operación diaria, la primera carga de incubación posterior al corte se valida contra el huevo recibido aún por cargar (BR-03), que descuenta no incubables y fosa **conocidos**; un dato desconocido no se descuenta.",
  "- En la operación diaria, una carga de incubación posterior al corte se valida contra el **saldo disponible para cargar** (BR-03), el mismo de la vista previa y la reconciliación. Si a la carga inicial le falta **algún** dato (extra grande, sucios, rotos o fosa vacíos), el saldo es **desconocido** y el sistema **no permite registrar cargas** en ese lote: aparece «No se puede determinar el saldo disponible para cargar porque la carga inicial de Incubadora contiene valores desconocidos…». La suma de lo que sí se conoce solo sirve para rechazar una fila imposible; no demuestra cuánto huevo queda.\n"
  "- **Cómo se desbloquea**: un usuario con permiso de correcciones completa el dato faltante con una **corrección de la carga inicial** (indicando el motivo; queda auditada y conserva el valor original «desconocido»). En cuanto los seis datos son conocidos, el saldo vuelve a ser exacto y las cargas se validan normalmente. Un `0` conocido es un cero real y no bloquea nada.")

D = "backend/scripts/cutover_v2_docs.py"
R(D, "huevo por cargar (BR-03 operativo) = `eggs_received − eggs_set − Σ(no incubables KNOWN) − fertile_eggs_to_pit (KNOWN)` (un UNKNOWN no se resta: el saldo es entonces cota superior)",
  "huevo por cargar (BR-03 operativo, SPEC 018 §10) = `eggs_received − eggs_set − oversized − dirty − broken − fertile_eggs_to_pit` solo si los seis son KNOWN; con un UNKNOWN el saldo es UNKNOWN y BR-03 deniega toda carga positiva (`CUTOVER_BALANCE_INCOMPLETE`) hasta la corrección gobernada de la apertura (`POST /opening-balances/{id}/corrections`)")

shutil.copyfile("audit/ga-hatchery-v4-br03-unknown-failsafe/evidence/proceso-spec018e-hatchery-v4-br03-unknown.spec.ts",
                "e2e/proceso-spec018e-hatchery-v4-br03-unknown.spec.ts")

if ERR:
    print("ERRORES:\n" + "\n".join(ERR))
    sys.exit(1)
print("OK: docs y E2E BR-03 aplicados")
