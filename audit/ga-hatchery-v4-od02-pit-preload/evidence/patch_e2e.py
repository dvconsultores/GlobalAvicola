#!/usr/bin/env python3
"""OD-HATCH-V4-02 · E2E (desde la raíz del repo): datos y aserciones al dominio pre-carga.

La E2E de OD-01 (`proceso-spec018b-…-od01`) se retira con `git rm` aparte; aquí se instala la de OD-02.
"""
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


# ── soporte compartido: fila canónica coherente con la invariante pre-carga ──
TS = "test-support/cutover.ts"
R(TS, """    // sustituye por el desglose de no incubables + los huevos fértiles enviados a fosa. Los tres
    // componentes son KNOWN (500 + 300 + 200 = 1000 derivados) y la fosa es 25 ≠ 0: por SPEC 018
    // §7 · D-12 (OD-HATCH-V4-01 RATIFIED) el `eggs_in_process` derivado es 9 000 − 0 − 25 = 8 975.""",
  """    // sustituye por el desglose de no incubables + los huevos fértiles enviados a fosa. Los tres
    // componentes son KNOWN (500 + 300 + 200 = 1000 derivados) y la fosa es un cero conocido: por SPEC
    // 018 §9 · D-21 (OD-HATCH-V4-02, fosa PRE-CARGA) recibidos 10 000 = cargados 9 000 + 1 000 + fosa 0.
    // Un escenario con fosa > 0 debe bajar los cargados o los no incubables.""")
R(TS, "eggs_non_incubable_broken: 200, eggs_transferred: 0, fertile_eggs_to_pit: 25, chicks_hatched: 0, chicks_available: 0,",
  "eggs_non_incubable_broken: 200, eggs_transferred: 0, fertile_eggs_to_pit: 0, chicks_hatched: 0, chicks_available: 0,")

# ── E2E V4 principal ────────────────────────────────────────────────────────
V4 = "e2e/proceso-spec018-cutover-hatchery-v4.spec.ts"
R(V4, """ * - D-12 (SPEC 018 §7 · OD-HATCH-V4-01 RATIFIED): `eggs_in_process = set − transferred − fosa`
 *   **solo** si los tres son KNOWN; la fosa es POST-CARGA (no es un no incubable ni un descarte).""",
  """ * - D-21/D-23 (SPEC 018 §9 · OD-HATCH-V4-02 RATIFIED): la fosa es PRE-CARGA (`set + no incubables +
 *   fosa ≤ received`) y `eggs_in_process = set − transferred` (no es un no incubable ni un descarte).""")
R(V4, "  // ── 3 · rellenar (10 000 recibidos / 9 000 cargados, 500+300+200 no incubables, fosa 25) y subir ──",
  "  // ── 3 · rellenar (10 000 recibidos / 8 975 cargados, 500+300+200 no incubables, fosa 25 = 10 000) y subir ──")
R(V4, """  const filas = [filaV4(ref, {
    eggs_non_incubable_oversized: 500, eggs_non_incubable_dirty: 300, eggs_non_incubable_broken: 200,
    fertile_eggs_to_pit: 25,
  })]""", """  const filas = [filaV4(ref, {
    eggs_set: 8975,
    eggs_non_incubable_oversized: 500, eggs_non_incubable_dirty: 300, eggs_non_incubable_broken: 200,
    fertile_eggs_to_pit: 25,
  })]""")
R(V4, """  // SPEC 018 §7 · D-12: 9 000 − 0 − 25 = 8 975 (la fosa es post-carga y sí resta).
  expect(filaPrev.derived.eggs_in_process, 'D-12: set − transferred − fosa').toBe(8975)""",
  """  // SPEC 018 §9 · D-23: 8 975 − 0 = 8 975 (la fosa es pre-carga: ya salió de lo recibido, no de lo cargado).
  expect(filaPrev.derived.eggs_in_process, 'D-23: set − transferred').toBe(8975)
  expect(filaPrev.derived.eggs_available_to_set, 'D-24: 10 000 − 8 975 − 1 000 − 25').toBe(0)""")
R(V4, """  // Columnas 3 y 4 de la fila = «en proceso» y «disponible»: 8 975 (9 000 − 0 − 25) y 0 (nunca −1 000).
  await expect(filaUI.locator('td').nth(3), 'D-12: set − transferred − fosa ⇒ 8 975').toContainText(/8[.,]975/)
  await expect(filaUI.locator('td').nth(4), 'D-4: una sola resta ⇒ 0, no −1 000').toHaveText('0')""",
  """  // «En proceso» y «disponible»: 8 975 (8 975 − 0) y 0 (una sola resta: nunca −1 000 ni −25).
  await expect(page.getByTestId(`cutover-eggs-in-process-${lotId}`), 'D-23: set − transferred ⇒ 8 975').toContainText(/8[.,]975/)
  await expect(page.getByTestId(`cutover-eggs-available-${lotId}`), 'D-24: una sola resta ⇒ 0').toHaveText('0')""")
R(V4, "  expect(h.eggs_set).toBe(9000)\n", "  expect(h.eggs_set).toBe(8975)\n")
R(V4, "  // SPEC 018 §7 · D-12: `set − transferred − fosa` = 9 000 − 0 − 25 = 8 975 (ni 9 000 ni 8 000).",
  "  // SPEC 018 §9 · D-23: `set − transferred` = 8 975 − 0 = 8 975 (la fosa no vuelve a restar).")
R(V4, "  // D-12 con fosa = 0 conocido: en proceso = set − transferred − 0 (9 000) y, tras el post-corte, más lo",
  "  // D-23: en proceso = set − transferred (9 000) y, tras el post-corte, más lo")

# ── E2E O-15: el UNKNOWN de «en proceso» ahora lo da transferidos vacío ──────
O15 = "e2e/proceso-spec018c-hatchery-v4-o15-preview-unknown.spec.ts"
R(O15, """ * - **E2E-O15-01** dos procesos en el mismo batch: A (10 000 / 9 000 / transferidos 8 000 / fosa 100
 *   ⇒ en proceso 900) y B (idéntico pero `fertile_eggs_to_pit` **vacío** ⇒ UNKNOWN). La fila A muestra""",
  """ * - **E2E-O15-01** dos procesos en el mismo batch: A (10 000 / 9 000 / transferidos 8 100 ⇒ en proceso
 *   900) y B (idéntico pero `eggs_transferred` **vacío** ⇒ UNKNOWN; desde SPEC 018 §9 · OD-HATCH-V4-02
 *   la fosa es PRE-CARGA y ya no interviene en «en proceso»). La fila A muestra""")
R(O15, """/** Fila con fosa KNOWN (`valor`), transferidos 8 000 y no incubables conocidos en 0 ⇒ en proceso = set − 8 000 − fosa. */
const filaConFosa = (ref: string, valor: number | null): Record<string, unknown> => filaV4(ref, {
  eggs_non_incubable_oversized: 0, eggs_non_incubable_dirty: 0, eggs_non_incubable_broken: 0,
  eggs_transferred: 8000, fertile_eggs_to_pit: valor,
})""", """/**
 * Fila con no incubables y fosa en 0 conocido y transferidos `8 000 + valor` (o vacío si `valor` es
 * `null`) ⇒ en proceso = 9 000 − transferidos (SPEC 018 §9 · D-23: `set − transferred`). `valor` 100 ⇒
 * 900; `0` ⇒ 1 000; `null` ⇒ UNKNOWN. La fosa (PRE-CARGA) ya no vuelve UNKNOWN el en proceso.
 */
const filaConFosa = (ref: string, valor: number | null): Record<string, unknown> => filaV4(ref, {
  eggs_non_incubable_oversized: 0, eggs_non_incubable_dirty: 0, eggs_non_incubable_broken: 0,
  eggs_transferred: valor === null ? null : 8000 + valor, fertile_eggs_to_pit: 0,
})""")
R(O15, "test('E2E-O15-01 dos procesos (A conocido, B con fosa vacía) ⇒ fila A 900, fila B UNKNOWN y chip UNKNOWN'",
  "test('E2E-O15-01 dos procesos (A conocido, B con transferidos vacío) ⇒ fila A 900, fila B UNKNOWN y chip UNKNOWN'")
R(O15, "'fosa UNKNOWN ⇒ en proceso UNKNOWN'", "'transferidos UNKNOWN ⇒ en proceso UNKNOWN'")
R(O15, "'fosa 0 conocido ⇒ set − transferidos'", "'transferidos 8 000 conocidos ⇒ set − transferidos'")

# ── p16 ─────────────────────────────────────────────────────────────────────
P16 = "e2e/proceso-p16-cutover-hatchery.spec.ts"
R(P16, """ * 500/300/200 con fosa 25 —y el `eggs_in_process` V4 (fosa POST-CARGA, SPEC 018 §7 · D-12) que
 * arrastra— se certifica aparte en `proceso-spec018-cutover-hatchery-v4.spec.ts` y en
 * `proceso-spec018b-hatchery-v4-fosa-od01.spec.ts`.""",
  """ * 500/300/200 con fosa 25 —y el `eggs_in_process` V4 (fosa PRE-CARGA, SPEC 018 §9 · D-23) que
 * arrastra— se certifica aparte en `proceso-spec018-cutover-hatchery-v4.spec.ts` y en
 * `proceso-spec018d-hatchery-v4-fosa-od02.spec.ts`.""")
R(P16, "        // Fosa en cero conocido ⇒ `eggs_in_process` derivable (con fosa > 0 sería UNKNOWN).",
  "        // Fosa en cero conocido: la fosa es PRE-CARGA y saldría del saldo por cargar (SPEC 018 §9).")

# ── E2E nueva de OD-02 ──────────────────────────────────────────────────────
shutil.copyfile("audit/ga-hatchery-v4-od02-pit-preload/evidence/proceso-spec018d-hatchery-v4-fosa-od02.spec.ts",
                "e2e/proceso-spec018d-hatchery-v4-fosa-od02.spec.ts")

if ERR:
    print("ERRORES:\n" + "\n".join(ERR))
    sys.exit(1)
print("OK: E2E OD-HATCH-V4-02 aplicadas")
