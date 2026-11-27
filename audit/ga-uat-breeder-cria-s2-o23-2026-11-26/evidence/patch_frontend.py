#!/usr/bin/env python3
"""O-23 · frontend (desde la raíz del repo): «Sin valor», catálogo solo activo, etiqueta funcional, historial."""
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


# ── i18n ────────────────────────────────────────────────────────────────────
R("frontend/public/locales/es/translation.json",
  '    "typeRequired": "Seleccione el tipo de corrección"\n  }\n}',
  '    "typeRequired": "Seleccione el tipo de corrección",\n    "noValue": "Sin valor"\n  }\n}')
R("frontend/public/locales/en/translation.json",
  '    "typeRequired": "Select the correction type"\n  }\n}',
  '    "typeRequired": "Select the correction type",\n    "noValue": "No value"\n  }\n}')

# ── utilidades ──────────────────────────────────────────────────────────────
U = "frontend/src/utils/correctionFields.ts"
p = Path(U)
p.write_text(p.read_text(encoding="utf-8").rstrip("\n") + """

/**
 * `020` · §7 `AC-O23-07`: etiqueta funcional de un registro de catálogo en el selector de
 * corrección: `código — nombre` cuando el maestro tiene código (`sap_code` del proveedor, `code`
 * de la granja, `plate` del transporte); si no, el nombre. Nunca el id solo.
 */
export function etiquetaDeMaestro(registro: any): string {
 const codigo = registro?.sap_code || registro?.code || registro?.plate
 const nombre = String(registro?.name ?? '')
 return codigo ? `${String(codigo)} — ${nombre}` : nombre
}

/**
 * `020` · §7 `AC-O23-07`: un valor de corrección vacío (`null`, `undefined` o cadena vacía) no
 * tiene texto que mostrar: la pantalla dice «Sin valor», nunca `null`, `undefined` ni un hueco.
 */
export function esValorVacio(valor: unknown): boolean {
 return valor === null || valor === undefined || String(valor) === ''
}
""", encoding="utf-8")

# ── formulario de corrección ────────────────────────────────────────────────
C = "frontend/src/pages/review/CorrectionForm.tsx"
R(C, "import { describirCampoCorregido } from '../../utils/correctionFields'",
  "import { describirCampoCorregido, esValorVacio, etiquetaDeMaestro } from '../../utils/correctionFields'")
R(C, " const campoActual = campos.find((f: any) => String(f.field_name) === fieldName) || null\n",
  " const campoActual = campos.find((f: any) => String(f.field_name) === fieldName) || null\n"
  " // `020` · §7 `AC-O23-07`: el original vacío se lee «Sin valor» (un maestro nulo también es corregible).\n"
  " const valorOriginal = campoActual?.current_display ?? campoActual?.current_value\n"
  " const textoOriginal = esValorVacio(valorOriginal) ? String(t('corrections.noValue', 'Sin valor')) : String(valorOriginal)\n")
R(C, "<input type=\"text\" value={campoActual?.current_display ?? campoActual?.current_value ?? ''} readOnly",
  "<input type=\"text\" value={textoOriginal} readOnly")
R(C, """ {catalogo
 .filter((r: any) => String(r.id) !== String(campoActual?.current_value ?? ''))
 .map((r: any) => <option key={String(r.id)} value={String(r.id)}>{r.name}</option>)}""",
  """ {catalogo
 // `020` · §7 `AC-O23-05/07` (`OD-21`): solo registros activos, con etiqueta funcional.
 .filter((r: any) => r.is_active !== false)
 .filter((r: any) => String(r.id) !== String(campoActual?.current_value ?? ''))
 .map((r: any) => <option key={String(r.id)} value={String(r.id)}>{etiquetaDeMaestro(r)}</option>)}""")

# ── historial de correcciones ───────────────────────────────────────────────
D = "frontend/src/pages/review/ReviewDetail.tsx"
R(D, "import { describirCampoCorregido } from '../../utils/correctionFields'",
  "import { describirCampoCorregido, esValorVacio } from '../../utils/correctionFields'")
R(D, """ <p><strong>{describirCampoCorregido(t, c.field_name)}:</strong> "{c.original_display ?? c.original_value}" → "{c.corrected_display ?? c.corrected_value}"</p>""",
  """ <p><strong>{describirCampoCorregido(t, c.field_name)}:</strong> {valorDelHistorial(c.original_display, c.original_value)} → {valorDelHistorial(c.corrected_display, c.corrected_value)}</p>""")
R(D, " const { t, i18n } = useTranslation()\n",
  " const { t, i18n } = useTranslation()\n"
  " // `020` · §7 `AC-O23-07`: el historial lee «Sin valor» donde no había dato, y el nombre (no el id) donde lo hay.\n"
  " const valorDelHistorial = (display: unknown, valor: unknown) => {\n"
  "  const texto = display ?? valor\n"
  "  return esValorVacio(texto)\n"
  "   ? <em data-testid=\"correction-no-value\">{String(t('corrections.noValue', 'Sin valor'))}</em>\n"
  "   : `\"${String(texto)}\"`\n"
  " }\n")

if ERR:
    print("ERRORES:\n" + "\n".join(ERR))
    sys.exit(1)
print("OK: frontend O-23 aplicado")
