#!/usr/bin/env python3
"""O-28 · sincronización de los tests del panel de unidades del usuario (desde la raíz del repo).

Solo tests y spec 013: el componente no cambia. `openPanel` dejaba de esperar al ver el TÍTULO del
Modal, que se pinta en cuanto el panel se abre, mientras el cuerpo aún muestra «cargando»; las filas
de unidades solo existen cuando la carga termina. Ahora se espera ese hecho observable.
"""
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


ESPERA = """
/**
 * O-28: el título del Modal se pinta al abrir, con el cuerpo aún en «cargando» (`role=status`); las
 * filas de unidades y las cabeceras de estado solo existen cuando la carga termina. Esperar al título
 * y consultar luego con `getBy*` dependía de que la carga ya hubiera resuelto (no determinista).
 * Se espera el mismo hecho que ve el usuario: el indicador de carga desaparece y el contenido aparece.
 */
async function esperarCargaDelPanel() {
  await waitFor(() => {
    expect(screen.queryByText('common.loading')).toBeNull()
    expect(screen.getByText('users.businessUnits.companyState')).toBeTruthy()
  })
}
"""

F1 = "frontend/src/pages/users/__tests__/gaFe02.userBuPanel.test.tsx"
R(F1, """async function openPanel(username: string) {
  render(<ToastProvider><UsersPage /></ToastProvider>)
  const openBtn = await screen.findByRole('button', { name: `users.businessUnits.open — ${username}` })
  fireEvent.click(openBtn)
  await screen.findByText('users.businessUnits.title')
}
""", ESPERA.lstrip("\n") + """
async function openPanel(username: string) {
  render(<ToastProvider><UsersPage /></ToastProvider>)
  const openBtn = await screen.findByRole('button', { name: `users.businessUnits.open — ${username}` })
  fireEvent.click(openBtn)
  await screen.findByText('users.businessUnits.title')
  await esperarCargaDelPanel()
}
""")

F2 = "frontend/src/pages/users/__tests__/uatAdminRbac.userBuPanel.test.tsx"
R(F2, """async function openPanel() {
  render(<ToastProvider><UserBusinessUnitsButton user={CARLOS} /></ToastProvider>)
  fireEvent.click(await screen.findByRole('button', { name: `users.businessUnits.open — carlos` }))
  await screen.findByText('users.businessUnits.title')
}
""", ESPERA.lstrip("\n") + """
async function openPanel() {
  render(<ToastProvider><UserBusinessUnitsButton user={CARLOS} /></ToastProvider>)
  fireEvent.click(await screen.findByRole('button', { name: `users.businessUnits.open — carlos` }))
  await screen.findByText('users.businessUnits.title')
  await esperarCargaDelPanel()
}
""")

SPEC = "specs/013-admin-rbac-uat/spec.md"
p = Path(SPEC)
s = p.read_text(encoding="utf-8")
if "## 8. Amendment O-28" in s:
    ERR.append("spec 013: el amendment O-28 ya existe")
else:
    p.write_text(s.rstrip("\n") + """

## 8. Amendment O-28 — `GA-O28-FE02-USER-BU-PANEL-FLAKINESS` (2026-11-27)

**Entrada:** vitest rojo de forma recurrente en `gaFe02.userBuPanel` y `uatAdminRbac.userBuPanel` (observación O-28, abierta desde SPEC 020 §7). Bloquea `DEVELOP_READY_FOR_PR`.

**Clasificación:** `TEST_DEFECT` (carrera asíncrona en el punto de sincronización del test). Componente sin cambios.

**Causa:** `openPanel` daba el panel por abierto al ver el **título** del `Modal`, que se pinta en el mismo render que el indicador «cargando» (`role=status`). Las filas de unidades y las cabeceras de estado solo se renderizan cuando `load()` resuelve las dos peticiones. Las consultas síncronas siguientes (`getByText('Engorde' | 'Progenitoras' | 'users.businessUnits.companyState')`) dependían de que la carga ya hubiera terminado. Los 4 fallos reproducidos muestran el indicador de carga en el DOM. En aislamiento pasa 30/30; en el archivo y la subsuite falla (2/10, 2/3); con orden aleatorio no aparece dependencia de orden. Producto correcto: indicador → contenido, verificado en navegador por la E2E P-17-B.

**Contrato del test:** abrir el panel = el indicador de carga desapareció **y** el contenido (cabeceras de estado EMPRESA/USUARIO) está presente (`waitFor` sobre esa condición concreta). Sin pausas, sin `setTimeout`, sin `skip`, sin aserciones retiradas ni relajadas.

| AC | Enunciado |
|---|---|
| **AC-O28-01** | Los 10 tests de los dos archivos esperan el fin de la carga antes de consultar el contenido del panel. |
| **AC-O28-02** | Estabilidad: archivo afectado 20/20, subsuite SPEC 013 / GA-FE-02 10/10, vitest completa 3/3 sin fallos. |
| **AC-O28-03** | Sensibilidad: con la carga diferida a una tarea posterior, el `openPanel` anterior falla y el nuevo pasa. |
| **AC-O28-04** | Falso verde: si la API devuelve `[]` unidades, los tests que esperan unidades fallan. |
""", encoding="utf-8")

if ERR:
    print("ERRORES:\n" + "\n".join(ERR))
    sys.exit(1)
print("OK: O-28 aplicado (2 tests + spec 013 §8)")
