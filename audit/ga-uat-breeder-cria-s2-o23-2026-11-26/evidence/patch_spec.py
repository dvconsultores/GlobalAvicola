#!/usr/bin/env python3
"""O-23 · enmienda mínima de la spec 020 (desde la raíz del repo): §7 NULL_TO_MASTER_CORRECTION."""
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


F = "specs/020-uat-breeder-cria-s2/spec.md"
ANCLA = "`O-23` (asignar por corrección un maestro a un campo que estaba vacío) sigue abierta. Certificación: `audit/ga-uat-breeder-cria-s2-owner-decisions-2026-11-25/CERTIFICATION.md`."
R(F, ANCLA, ANCLA + """

## 7. Enmienda O-23 · `NULL_TO_MASTER_CORRECTION` (26-11-2026)

Residual posterior al cierre de §6 (`SESSION2 = CERTIFIED`); no reabre la Sesión 2 ni cambia `OD-S2-01..07`. Clasificación: `P2 FUNCTIONAL GAP` · `FIX_REQUIRED`.

**Causa raíz (discovery).** `campos_corregibles_de_evento` descartaba todo campo del evento con valor `NULL` salvo `observations` (`SIEMPRE_OFRECIDOS`): la corregibilidad dependía del **valor**, no de la **metadata** del campo, y el formulario —que ya construye el selector a partir de `master`, sin mirar el valor— nunca recibía el campo. En el servidor, `POST /corrections` no bloqueaba `NULL → id`, pero tampoco acotaba el maestro al tipo de evento ni exigía maestro activo (`OD-21`).

| AC | Enunciado |
|---|---|
| **AC-O23-01** | Metadata contractual `MAESTROS_POR_TIPO_DE_EVENTO` (tipo → campos de maestro que su alta admite, extraída del formulario de alta): recepción de aves → proveedor; salida de aves → granja destino, planta destino, transporte; despacho de huevo, recepción de huevo en incubadora e inspección de transporte → transporte; nacimiento → vacuna; despacho de pollitos → granja destino, transporte; importación de progenitoras → proveedor, transporte; mortalidad → causa de mortalidad; descarte → causa de descarte; vacunación → vacuna; medicación → medicamento. |
| **AC-O23-02** | `GET /corrections/events/{id}/correctable-fields` ofrece un campo de maestro con valor `NULL` cuando el campo aplica al tipo del evento, con `master` (clave del catálogo), `current_value = null` y `current_display = null`. Un campo con valor se sigue ofreciendo como hasta ahora. Los campos vacíos que no son de maestro siguen fuera (fuera de alcance). Seguridad sin cambios: sin token 401, sin permiso 403, evento de otra empresa o inexistente 404. |
| **AC-O23-03** | Direcciones. **A** `NULL → maestro válido` = ALLOW. **B** `maestro A → maestro B` = ALLOW. **C** `maestro → NULL` según el contrato vigente del campo (`AC-S2-C02`, `RR-21`, `RR-32`: proveedor, transporte y destinos admiten vaciarse; vacuna, medicamento y causas, no). **D** `NULL → maestro` inexistente, de otra empresa o inactivo = DENY (400) y el evento queda intacto. |
| **AC-O23-04** | `NULL → maestro` en un campo que **no aplica** al tipo del evento = 400: no hay correcciones arbitrarias aunque se manipule el payload. |
| **AC-O23-05** | `OD-21` en correcciones: el maestro que una corrección **nueva** asigna debe estar activo, sea cual sea el valor original; el de otra empresa sigue siendo «no encontrado» (`BR-07`, `AC26`). La lectura histórica de un maestro hoy inactivo no cambia: el valor original se sigue mostrando por nombre. |
| **AC-O23-06** | Auditoría: `CorrectionLog.original_value = NULL`, `corrected_value = id` canónico, tipo de corrección, motivo, autor, fecha y evento; el registro de auditoría guarda lo mismo. El valor efectivo del evento es el id corregido (`RR-01`). |
| **AC-O23-07** | UI: el valor original vacío se lee «Sin valor» (nunca `null`, `undefined`, `0` ni un campo en blanco); el valor corregido de un maestro es un selector del catálogo con **solo registros activos** y etiqueta funcional (`código — nombre` cuando el maestro tiene código: `sap_code`, `code`, `plate`), nunca el id solo. El historial muestra «Proveedor: Sin valor → <nombre>». |
| **AC-O23-08** | Las reglas del campo se aplican igual que en `A→B` (`RR-21`, `RR-31`, `RR-32`, `BR-07`, vínculo efectivo): sin *bypass*. |

Pruebas: backend `O23-B01..B09` (`backend/tests/test_uat_s2_o23_null_to_master.py`), frontend `O23-F01..F06` (vitest), E2E `proceso-spec020c` (positivo con refresco y re-login, y negativo por API: otra empresa e inactivo). `O-26`, `O-27`, `O-11`, `O-12`, `O-16` y `O-19` quedan fuera de este ciclo.""")

if ERR:
    print("ERRORES:\n" + "\n".join(ERR))
    sys.exit(1)
print("OK: spec 020 §7 aplicada")
