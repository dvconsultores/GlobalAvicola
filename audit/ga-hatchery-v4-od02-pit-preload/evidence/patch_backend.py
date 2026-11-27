#!/usr/bin/env python3
"""OD-HATCH-V4-02 · backend (desde la raíz del repo): la fosa pasa a PRE-CARGA.

validación (D-21/D-22), derivados (D-23/D-24), reconciliación, BR-03 operativo (D-25), contrato y
generador de docs; más el ajuste de datos/comentarios de tests existentes al dominio nuevo.
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


def entre(path, inicio, fin, nuevo):
    """Sustituye el bloque [inicio, fin) por `nuevo` (ambos marcadores deben ser únicos)."""
    p = Path(path)
    s = p.read_text(encoding="utf-8")
    if s.count(inicio) != 1 or s.count(fin) != 1:
        ERR.append(f"{path}: marcadores no únicos ({s.count(inicio)}, {s.count(fin)}): {inicio[:60]!r}")
        return
    i, j = s.index(inicio), s.index(fin)
    p.write_text(s[:i] + nuevo + s[j:], encoding="utf-8")


# ── validation.py ───────────────────────────────────────────────────────────
V = "backend/app/cutover/validation.py"
R(V, '_NO_INCUBABLES = ("eggs_non_incubable_oversized", "eggs_non_incubable_dirty", "eggs_non_incubable_broken")\n',
  '_NO_INCUBABLES = ("eggs_non_incubable_oversized", "eggs_non_incubable_dirty", "eggs_non_incubable_broken")\n'
  '#: SPEC 018 §9 · OD-HATCH-V4-02: salidas PRE-CARGA del huevo recibido (no incubables + fosa), en el orden\n'
  '#: en que se acumulan contra lo recibido. La fosa es un concepto distinto de los no incubables.\n'
  '_SALIDAS_PRE_CARGA = _NO_INCUBABLES + ("fertile_eggs_to_pit",)\n')

entre(V, "    def _consistencia_incubadora(self, fila: dict) -> None:\n", "    def _derivados(self, fila: dict) -> None:\n", '''    def _consistencia_incubadora(self, fila: dict) -> None:
        """Invariantes del contrato V4 (SPEC 018 §2 D-4 y §9 D-21/D-22, OD-HATCH-V4-02 RATIFIED
        2026-11-26): sin `eggs_discarded`, sin igualdades forzadas y con el modelo de dos etapas
        (`received → {no incubables | fosa | set | por cargar}`; `set → {transferred | en proceso}`).
        La fosa es PRE-CARGA; OD-HATCH-V4-01 (fosa post-carga) queda SUPERSEDED."""
        recibidos_known = _known(fila, "eggs_received")
        recibidos = _val(fila, "eggs_received") if recibidos_known else None
        cargados_excedidos = recibidos_known and _known(fila, "eggs_set") and _val(fila, "eggs_set") > recibidos
        if cargados_excedidos:
            self._error(fila, "eggs_set", "CONSISTENCY_MISMATCH", detalle="huevos cargados > huevos recibidos")
        # Etapa B (POST-CARGA): solo cargados → transferidos/en proceso. La fosa ya no participa (D-22).
        if _known(fila, "eggs_set"):
            cargados = _val(fila, "eggs_set")
            if _known(fila, "eggs_transferred") and _val(fila, "eggs_transferred") > cargados:
                self._error(fila, "eggs_transferred", "CONSISTENCY_MISMATCH", detalle="eggs_transferred > huevos cargados")
            if _known(fila, "chicks_hatched"):
                tope_campo = "eggs_transferred" if _known(fila, "eggs_transferred") else "eggs_set"
                if _val(fila, "chicks_hatched") > _val(fila, tope_campo):
                    self._error(fila, "chicks_hatched", "CONSISTENCY_MISMATCH", detalle=f"pollitos nacidos > {tope_campo}")
        if _known(fila, "chicks_hatched", "chicks_available") and _val(fila, "chicks_available") > _val(fila, "chicks_hatched"):
            self._error(fila, "chicks_available", "CONSISTENCY_MISMATCH", detalle="pollitos disponibles > nacidos")
        if not recibidos_known:
            return  # sin `eggs_received` no hay cota: un UNKNOWN nunca se trata como 0 ni dispara ni oculta errores
        # Etapa A (PRE-CARGA) · D-4 + D-21: no incubables y fosa son salidas del huevo RECIBIDO previas a
        # la carga; cada componente KNOWN no puede superar lo recibido.
        componente_excedido = False
        for campo in _SALIDAS_PRE_CARGA:
            if _known(fila, campo) and _val(fila, campo) > recibidos:
                detalle = ("huevos fértiles a fosa > huevos recibidos" if campo == "fertile_eggs_to_pit"
                           else f"{campo} > huevos recibidos")
                self._error(fila, campo, "CONSISTENCY_MISMATCH", detalle=detalle)
                componente_excedido = True
        # D-21: `eggs_set + Σ(salidas pre-carga KNOWN) ≤ eggs_received`. Con un UNKNOWN la suma conocida
        # es solo una cota (si aun así supera lo recibido, se rechaza) y **no se impone igualdad**:
        # `received − set − salidas` es huevo recibido aún por cargar (saldo de BR-03).
        # El error se anota en el primer componente conocido que rompe la cota (sin doble error).
        if not componente_excedido and not cargados_excedidos:
            cargados = _val(fila, "eggs_set") if _known(fila, "eggs_set") else 0
            acumulado = cargados
            for campo in _SALIDAS_PRE_CARGA:
                if not _known(fila, campo):
                    continue
                acumulado += _val(fila, campo)
                if acumulado > recibidos:
                    self._error(fila, campo, "CONSISTENCY_MISMATCH",
                                detalle=f"cargados + no incubables + fosa > recibidos: {cargados} + {acumulado - cargados} "
                                        f"> {recibidos}")
                    break

''')

R(V, """            # SPEC 018 §7 · D-12 (OD-HATCH-V4-01 RATIFIED 2026-11-21): la fosa es POST-CARGA, así que
            # `set − transferred − fosa` solo si los tres son KNOWN (un UNKNOWN nunca se toma por 0:
            # jamás 1000 con `fertile_eggs_to_pit` UNKNOWN). `pit = 0` conocido ⇒ `set − transferred`.
            if _known(fila, "eggs_set", "eggs_transferred", "fertile_eggs_to_pit"):
                derivados["eggs_in_process"] = (_val(fila, "eggs_set") - _val(fila, "eggs_transferred")
                                               - _val(fila, "fertile_eggs_to_pit"))
            else:
                derivados["eggs_in_process"] = None
            return
""", """            # SPEC 018 §9 · D-23 (OD-HATCH-V4-02): la fosa es PRE-CARGA y ya se descontó antes de
            # `eggs_set`; en proceso = `set − transferred` solo si ambos son KNOWN (nunca un 0 inventado).
            if _known(fila, "eggs_set", "eggs_transferred"):
                derivados["eggs_in_process"] = _val(fila, "eggs_set") - _val(fila, "eggs_transferred")
            else:
                derivados["eggs_in_process"] = None
            # D-24: saldo disponible para cargar = recibidos − cargados − no incubables − fosa, solo si
            # TODOS son KNOWN; con un UNKNOWN el saldo es UNKNOWN (no se da una cifra definitiva).
            if _known(fila, "eggs_received", "eggs_set", *_SALIDAS_PRE_CARGA):
                derivados["eggs_available_to_set"] = (_val(fila, "eggs_received") - _val(fila, "eggs_set")
                                                     - sum(_val(fila, c) for c in _SALIDAS_PRE_CARGA))
            else:
                derivados["eggs_available_to_set"] = None
            return
""")

# ── service.py (reconciliación) ─────────────────────────────────────────────
S = "backend/app/cutover/service.py"
R(S, """                    if es_v4:
                        # SPEC 018 §7 · D-12: fosa POST-CARGA; `set − transferred − fosa` solo si los
                        # tres son KNOWN (un UNKNOWN nunca se toma por 0: jamás 1000 con fosa UNKNOWN).
                        en_proceso = ((cargados - transferidos - fosa)
                                      if None not in (cargados, transferidos, fosa) else None)
""", """                    if es_v4:
                        # SPEC 018 §9 · D-23 (OD-HATCH-V4-02): la fosa es PRE-CARGA; en proceso =
                        # `set − transferred` solo si ambos son KNOWN (la fosa ya no resta aquí).
                        en_proceso = (cargados - transferidos) if None not in (cargados, transferidos) else None
""")
R(S, """                    # D-4: los no incubables restan UNA sola vez, en el saldo recibido→cargado.
                    if None in (recibidos, cargados):
                        disponible = None
                    elif es_v4:
                        disponible = (recibidos - cargados - total_no_incubable) if total_no_incubable is not None else None
""", """                    # D-4 + §9 D-24: no incubables y fosa (PRE-CARGA) restan UNA sola vez, en el saldo
                    # recibido→cargado, y solo si todos son KNOWN (con un UNKNOWN el saldo es UNKNOWN).
                    if None in (recibidos, cargados):
                        disponible = None
                    elif es_v4:
                        disponible = ((recibidos - cargados - total_no_incubable - fosa)
                                      if None not in (total_no_incubable, fosa) else None)
""")

# ── operations/validators.py (BR-03 operativo) ──────────────────────────────
O = "backend/app/operations/validators.py"
R(O, """    no_incubables = sum(componentes[1:], componentes[0])
    apertura = (await db.execute(
        select(func.coalesce(HatcheryOpening.eggs_received, 0) - func.coalesce(HatcheryOpening.eggs_set, 0) - no_incubables)
""", """    no_incubables = sum(componentes[1:], componentes[0])
    # SPEC 018 §9 · D-25 (OD-HATCH-V4-02): la fosa es PRE-CARGA y también sale del huevo recibido;
    # como los no incubables, solo se resta si es KNOWN (un UNKNOWN no se inventa: cota superior).
    fosa = case((HatcheryOpening.fertile_eggs_to_pit_status == "KNOWN",
                 func.coalesce(HatcheryOpening.fertile_eggs_to_pit, 0)), else_=0)
    apertura = (await db.execute(
        select(func.coalesce(HatcheryOpening.eggs_received, 0) - func.coalesce(HatcheryOpening.eggs_set, 0)
               - no_incubables - fosa)
""")

# ── contracts.py (instrucciones de la plantilla) ────────────────────────────
C = "backend/app/cutover/contracts.py"
R(C, 'promotion="saldo por cargar = recibidos − cargados − no incubables conocidos", consumer="BR-03 carga de incubación"),',
  'promotion="saldo por cargar = recibidos − cargados − no incubables − fosa (conocidos)", consumer="BR-03 carga de incubación"),')
R(C, 'promotion="≤ eggs_received; cargados ≥ transferidos + fosa", consumer="huevos en proceso"),',
  'promotion="≤ eggs_received; cargados + no incubables + fosa ≤ recibidos; cargados ≥ transferidos", consumer="huevos en proceso"),')
R(C, 'promotion="set + suma de no incubables conocidos ≤ eggs_received", consumer="saldo por cargar (BR-03), total no incubable (derivado)"),',
  'promotion="set + no incubables + fosa conocidos ≤ eggs_received", consumer="saldo por cargar (BR-03), total no incubable (derivado)"),',
  count=3)
R(C, 'promotion="≤ eggs_set; transferidos + fosa ≤ eggs_set", consumer="nacimientos"),',
  'promotion="≤ eggs_set", consumer="nacimientos"),')
R(C, '"Cantidad acumulada de huevos YA CARGADOS en incubación que fueron retirados a fosa (huevos fértiles) durante la incubación/ovoscopia, antes de continuar a nacedora, hasta la fecha de corte. Concepto POST-CARGA, separado de los no incubables y de eggs_discarded. ≤ huevos cargados; transferidos + fosa ≤ cargados. Vacío = desconocido; 0 = cero conocido.",',
  '"Cantidad acumulada de huevos fértiles recibidos que fueron enviados a fosa antes de la carga en incubadora, hasta la fecha de corte. Esta cantidad ya no forma parte de los huevos cargados. Concepto PRE-CARGA, separado de los no incubables y de eggs_discarded. ≤ huevos recibidos; cargados + no incubables + fosa ≤ recibidos. Vacío = desconocido; 0 = cero conocido.",')
R(C, '''              promotion="fosa ≤ eggs_set; transferidos + fosa ≤ eggs_set; en proceso = cargados − transferidos − fosa",
              consumer="huevos en proceso (junto con transferidos), reconciliación"),''',
  '''              promotion="fosa ≤ eggs_received; set + no incubables + fosa ≤ eggs_received; saldo por cargar = recibidos − cargados − no incubables − fosa",
              consumer="saldo por cargar (BR-03), reconciliación"),''')

# ── generador de docs de contrato ───────────────────────────────────────────
D = "backend/scripts/cutover_v2_docs.py"
R(D, "- No incubables (SPEC 018, V4): cada componente KNOWN (`eggs_non_incubable_oversized`, `eggs_non_incubable_dirty`, `eggs_non_incubable_broken`) `≤ eggs_received`, y `eggs_set + Σ(no incubables KNOWN) ≤ eggs_received`. **Sin igualdad**: la suma conocida es cota inferior porque `eggs_received` puede incluir huevo aún no cargado.\n"
     "- `fertile_eggs_to_pit ≤ eggs_set` si `eggs_set` es KNOWN, y `eggs_transferred + fertile_eggs_to_pit ≤ eggs_set` si los tres son KNOWN (sin doble error si una cota ya falló); sin `eggs_set` KNOWN solo queda `fertile_eggs_to_pit ≤ eggs_received`. `fertile_eggs_to_pit` son huevos YA CARGADOS retirados a fosa durante la incubación/ovoscopia (concepto POST-CARGA, separado de los no incubables y de `eggs_discarded`): decisión de dominio `RATIFIED` 2026-11-21 · `OD-HATCH-V4-01` (SPEC 018 §7).\n",
  "- Salidas PRE-CARGA (SPEC 018, V4): cada componente KNOWN (`eggs_non_incubable_oversized`, `eggs_non_incubable_dirty`, `eggs_non_incubable_broken`, `fertile_eggs_to_pit`) `≤ eggs_received`, y `eggs_set + Σ(no incubables KNOWN) + fertile_eggs_to_pit (KNOWN) ≤ eggs_received`. **Sin igualdad forzada** (`≤`, nunca `≥`): la suma conocida es cota porque `eggs_received` puede incluir huevo aún no cargado; con un UNKNOWN solo se valida la suma conocida.\n"
     "- `fertile_eggs_to_pit` son huevos fértiles **recibidos** enviados a fosa **antes de la carga** en incubadora (concepto PRE-CARGA, separado de los no incubables y de `eggs_discarded`): ya no forman parte de `eggs_set` y no intervienen en `eggs_set → eggs_transferred`. Decisión de dominio `OD-HATCH-V4-02 = RATIFIED` 2026-11-26 (SPEC 018 §9), que deja `SUPERSEDED` a `OD-HATCH-V4-01` (fosa post-carga).\n")
R(D, "`eggs_in_process = eggs_set − eggs_transferred − fertile_eggs_to_pit` solo si los tres son KNOWN (si alguno es UNKNOWN, desconocido: `fertile_eggs_to_pit = 0` conocido da `eggs_set − eggs_transferred`, nunca se inventa un cero)",
  "`eggs_in_process = eggs_set − eggs_transferred` solo si ambos son KNOWN (la fosa no resta: ya se descontó antes de la carga); `eggs_available_to_set = eggs_received − eggs_set − oversized − dirty − broken − fertile_eggs_to_pit` solo si todos son KNOWN (si alguno es UNKNOWN, desconocido; nunca se inventa un cero)")
R(D, "huevo por cargar = `eggs_received − eggs_set − Σ(no incubables KNOWN)` (un UNKNOWN no se resta: el saldo es entonces cota superior)",
  "huevo por cargar (BR-03 operativo) = `eggs_received − eggs_set − Σ(no incubables KNOWN) − fertile_eggs_to_pit (KNOWN)` (un UNKNOWN no se resta: el saldo es entonces cota superior)")

# ── tests existentes: datos y comentarios al dominio nuevo (sin relajar aserciones) ──
T4 = "backend/tests/test_cutover_hatchery_v4.py"
R(T4, """igualdad forzada `received = set + no incubables` (D-4), fosa POST-CARGA acotada por los
cargados y `eggs_in_process = set − transferred − fosa` (SPEC 018 §7 · D-12/D-13,
OD-HATCH-V4-01 RATIFIED) y V3 histórica intacta (D-2/D-8).""",
  """igualdad forzada `received = set + no incubables` (D-4), fosa PRE-CARGA acotada por lo
recibido junto con los no incubables y `eggs_in_process = set − transferred` (SPEC 018 §9 ·
D-21/D-23, OD-HATCH-V4-02 RATIFIED) y V3 histórica intacta (D-2/D-8).""")
entre(T4, "# ── AC-V4-08 · huevos fértiles a fosa ───────────────────────────────────────\n",
      "    lotes = await items_por_referencia(http_client, auth_headers, batch_id)\n    apertura = await _apertura(lotes[\"ACV4-PIT-1\"])\n",
      '''# ── AC-V4-08 · huevos fértiles a fosa ───────────────────────────────────────

@pytest.mark.asyncio
async def test_ac_v4_08_fosa_acotada_por_lo_recibido(auth_headers, http_client, seeded_ids):
    """AC-V4-23/24 · D-21: la fosa es PRE-CARGA y se acota contra lo recibido, con los no incubables.

    Fixture: recibidos 10000 = cargados 9000 + no incubables 500/300/200 (saldo 0). OD-HATCH-V4-02:
    una fosa > 0 sin bajar los cargados rompe la cota pre-carga; la fosa ya no se compara con `eggs_set`.
    """
    await preparar(seeded_ids)
    filas = [
        fila_incubadora("ACV4-PIT-X", fertile_eggs_to_pit=10001),                     # > recibidos ⇒ error
        fila_incubadora("ACV4-PIT-Y", fertile_eggs_to_pit=50),                        # 9000 + 1000 + 50 > 10000 ⇒ error
        fila_incubadora("ACV4-PIT-Z", eggs_set=8950, fertile_eggs_to_pit=50),         # = 10000 ⇒ válida
        fila_incubadora("ACV4-PIT-W", eggs_set=0, eggs_non_incubable_oversized=0, eggs_non_incubable_dirty=0,
                        eggs_non_incubable_broken=0, fertile_eggs_to_pit=9500),       # fosa > cargados: válida (D-22)
        fila_incubadora("ACV4-PIT-V", eggs_set=8000, eggs_transferred=8000, fertile_eggs_to_pit=1000),  # = 10000 ⇒ válida
    ]
    cuerpo, errores = await _errores(http_client, auth_headers, filas, 82)
    assert errores == [(2, "fertile_eggs_to_pit", "CONSISTENCY_MISMATCH"),
                       (3, "fertile_eggs_to_pit", "CONSISTENCY_MISMATCH")]
    assert (cuerpo["valid_rows"], cuerpo["invalid_rows"]) == (3, 2)


@pytest.mark.asyncio
async def test_ac_v4_08_pipeline_completo_con_fosa(auth_headers, http_client, seeded_ids):
    """Fosa > 0 viaja por todo el pipeline: staging, preview, apertura y reconciliación."""
    await preparar(seeded_ids)
    batch_id = await _aplicar_batch(http_client, auth_headers, headers_aprobador(seeded_ids), [
        fila_incubadora("ACV4-PIT-1", eggs_set=8975, fertile_eggs_to_pit=25),     # 8975 + 1000 + 25 = 10000
        fila_incubadora("ACV4-PIT-2", fertile_eggs_to_pit=0),
    ], 83)

    preview = await _preview(http_client, auth_headers, batch_id)
    assert preview["ACV4-PIT-1"]["values"]["fertile_eggs_to_pit"] == {"value": 25, "status": "KNOWN"}
    # §9 D-23: la fosa es PRE-CARGA y no resta de lo cargado: en proceso = 8975 − 0.
    assert preview["ACV4-PIT-1"]["derived"]["eggs_in_process"] == 8975
    assert preview["ACV4-PIT-1"]["derived"]["eggs_available_to_set"] == 0
    assert preview["ACV4-PIT-2"]["derived"]["eggs_in_process"] == 9000  # fosa 0 KNOWN

''')

T15 = "backend/tests/test_cutover_hatchery_v4_o15.py"
R(T15, """    # A: set 9000 − transferred 8000 − fosa 100 = 900 · B: fosa vacía ⇒ en proceso UNKNOWN.
    preview = await _preview_de(http_client, auth_headers, "hatchery", [
        fila_incubadora("O15-A", eggs_set=9000, eggs_transferred=8000, fertile_eggs_to_pit=100),
        fila_incubadora("O15-B", eggs_set=9000, eggs_transferred=8000, fertile_eggs_to_pit=None),
    ], 91)""", """    # SPEC 018 §9 · D-23: en proceso = set − transferred (la fosa es PRE-CARGA y no resta).
    # A: 8900 − 8000 = 900 (8900 + 1000 + fosa 100 = 10000 recibidos) · B: transferidos vacío ⇒ UNKNOWN.
    preview = await _preview_de(http_client, auth_headers, "hatchery", [
        fila_incubadora("O15-A", eggs_set=8900, eggs_transferred=8000, fertile_eggs_to_pit=100),
        fila_incubadora("O15-B", eggs_set=9000, eggs_transferred=None, fertile_eggs_to_pit=0),
    ], 91)""")
R(T15, """    # Con B' de fosa 0 conocida (en proceso 1000) el total pasa a ser numérico.
    preview2 = await _preview_de(http_client, auth_headers, "hatchery", [
        fila_incubadora("O15-A2", eggs_set=9000, eggs_transferred=8000, fertile_eggs_to_pit=100),
        fila_incubadora("O15-B2", eggs_set=9000, eggs_transferred=8000, fertile_eggs_to_pit=0),
    ], 90)""", """    # Con B' de transferidos 8000 conocidos (en proceso 1000) el total pasa a ser numérico.
    preview2 = await _preview_de(http_client, auth_headers, "hatchery", [
        fila_incubadora("O15-A2", eggs_set=8900, eggs_transferred=8000, fertile_eggs_to_pit=100),
        fila_incubadora("O15-B2", eggs_set=9000, eggs_transferred=8000, fertile_eggs_to_pit=0),
    ], 90)""")

TV = "backend/tests/test_cutover_v2_validation.py"
R(TV, """             # SPEC 018 · D-4 + §7 D-13 (OD-HATCH-V4-01 RATIFIED): cada no incubable se acota
             # contra lo recibido y la fosa POST-CARGA contra lo cargado (aquí 10001 > set 9000 ⇒ un
             # solo error en `fertile_eggs_to_pit`, sin doble reporte).""",
  """             # SPEC 018 · D-4 + §9 D-21 (OD-HATCH-V4-02 RATIFIED): cada salida PRE-CARGA (no
             # incubables y fosa) se acota contra lo recibido (aquí fosa 10001 > 10000 ⇒ un solo
             # error en `fertile_eggs_to_pit`, sin doble reporte).""")
R(TV, """             fila_incubadora("V-C16", eggs_non_incubable_oversized=900, eggs_non_incubable_dirty=None,
                             eggs_non_incubable_broken=None, fertile_eggs_to_pit=1000)]           # 9000 + 900 ≤ 10000""",
  """             fila_incubadora("V-C16", eggs_non_incubable_oversized=900, eggs_non_incubable_dirty=None,
                             eggs_non_incubable_broken=None, fertile_eggs_to_pit=100)]            # 9000 + 900 + 100 ≤ 10000""")

TC = "backend/tests/test_cutover_v2_continuity.py"
R(TC, """    # SPEC 018 · D-4 + §7 D-12 (OD-HATCH-V4-01 RATIFIED): los no incubables no restan de
    # `eggs_in_process` (nunca entraron en el set) y la fosa POST-CARGA (0 KNOWN aquí) tampoco añade
    # nada: en proceso = `set − transferred − fosa` + cargas post-corte. Saldo recibido→cargado = 0.""",
  """    # SPEC 018 · D-4 + §9 D-23 (OD-HATCH-V4-02 RATIFIED): los no incubables y la fosa son PRE-CARGA y
    # no restan de `eggs_in_process` (nunca entraron en el set): en proceso = `set − transferred` +
    # cargas post-corte. Saldo recibido→cargado = 0.""")

TR = "backend/tests/test_cutover_v2_red.py"
R(TR, """        # SPEC 018 · D-4/AC-V4-10 + §7 D-12: los no incubables restan UNA sola vez, en el saldo
        # recibido→cargado (10000 − 9000 − 1000), no en `eggs_in_process` (= `set − transferred − fosa`;
        # aquí con fosa 0 KNOWN sigue siendo `set − transferred`).""",
  """        # SPEC 018 · D-4/AC-V4-10 + §9 D-24/D-25: no incubables y fosa (PRE-CARGA) restan UNA sola vez,
        # en el saldo recibido→cargado (10000 − 9000 − 1000 − fosa 0), no en `eggs_in_process`
        # (= `set − transferred`).""")

TF = "backend/tests/cutover_v2_fixtures.py"
R(TF, """    # SPEC 018 · D-4 + §7 D-12: fila V4 coherente — recibidos = cargados + no incubables conocidos
    # (500+300+200), sin huevo pendiente de cargar; la fosa es un cero conocido
    # (`eggs_in_process = set − transferred − fosa`).""",
  """    # SPEC 018 · D-4 + §9 D-21: fila V4 coherente — recibidos = cargados + no incubables conocidos
    # (500+300+200) + fosa (0 conocido), sin huevo pendiente de cargar. Una fosa > 0 exige bajar los
    # cargados o los no incubables (la fosa es PRE-CARGA).""")

if ERR:
    print("ERRORES:\n" + "\n".join(ERR))
    sys.exit(1)
print("OK: backend OD-HATCH-V4-02 aplicado")
