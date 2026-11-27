#!/usr/bin/env python3
"""BR-03 UNKNOWN FAIL-SAFE (desde la raíz del repo): saldo canónico, BR-03 deniega con UNKNOWN,
corrección gobernada de los componentes pre-carga y spec 018 §10."""
import shutil
import sys
from pathlib import Path

ERR = []
EV = "audit/ga-hatchery-v4-br03-unknown-failsafe/evidence"


def R(path, old, new, count=1):
    p = Path(path)
    s = p.read_text(encoding="utf-8")
    n = s.count(old)
    if n != count:
        ERR.append(f"{path}: se esperaban {count} apariciones y hay {n}: {old[:90]!r}")
        return
    p.write_text(s.replace(old, new), encoding="utf-8")


def entre(path, inicio, fin, nuevo):
    p = Path(path)
    s = p.read_text(encoding="utf-8")
    if s.count(inicio) != 1 or s.count(fin) != 1:
        ERR.append(f"{path}: marcadores no únicos ({s.count(inicio)}, {s.count(fin)}): {inicio[:60]!r}")
        return
    i, j = s.index(inicio), s.index(fin)
    p.write_text(s[:i] + nuevo + s[j:], encoding="utf-8")


# ── módulo canónico ─────────────────────────────────────────────────────────
shutil.copyfile(f"{EV}/saldo_incubadora.py", "backend/app/cutover/saldo_incubadora.py")

# ── BR-03 operativo ─────────────────────────────────────────────────────────
O = "backend/app/operations/validators.py"
R(O, "from datetime import date\nfrom sqlalchemy import case, func, select\n",
  "from datetime import date\nfrom typing import Optional\n\nfrom sqlalchemy import case, func, select\n")
R(O, """async def get_hatchery_egg_balance(db: AsyncSession, lot_id: int) -> int:""",
  """async def get_hatchery_egg_balance(db: AsyncSession, lot_id: int) -> Optional[int]:""")
R(O, """    Apertura migrada (SPEC 018 · D-4): `recibidos − cargados − Σ(no incubables KNOWN)`.
""", """    Apertura migrada (SPEC 018 §10): saldo **exacto** de `saldo_apertura_por_cargar` (V4: recibidos −
    cargados − no incubables − fosa con los seis KNOWN). Si la apertura tiene un componente UNKNOWN el
    saldo del lote es UNKNOWN (`None`): BR-03 no autoriza cargas hasta corregir la carga inicial.
""")
entre(O, "    # SPEC 006: un proceso de incubación migrado abre con huevo recibido y aún no cargado\n",
      "\n\nasync def get_viable_chick_balance", """    # SPEC 006: un proceso de incubación migrado abre con huevo recibido y aún no cargado; sin esa
    # apertura el lote nacía con saldo 0 y `BR-03` rechazaba la primera carga posterior al corte.
    # SPEC 018 §10 (BR-03 UNKNOWN FAIL-SAFE): la apertura sale de la función canónica compartida con
    # el preview y la reconciliación. Un componente pre-carga UNKNOWN NO se omite: la suma conocida es
    # una cota superior, no un saldo demostrado ⇒ el saldo es UNKNOWN y no autoriza consumo.
    from ..cutover.saldo_incubadora import saldo_apertura_del_lote

    _, apertura = await saldo_apertura_del_lote(db, lot_id)
    if apertura is None:
        return None
    return int(apertura) + (res_in.scalar() or 0) - (res_out.scalar() or 0)
""")
R(O, """    await bloquear_saldo_del_lote(db, lot_id)
    balance = await get_hatchery_egg_balance(db, lot_id)
    if quantity > balance:""", """    await bloquear_saldo_del_lote(db, lot_id)
    balance = await get_hatchery_egg_balance(db, lot_id)
    if balance is None:
        # SPEC 018 §10: sin saldo exacto (apertura con componentes UNKNOWN) no se autoriza ninguna carga.
        from ..cutover.saldo_incubadora import MENSAJE_SALDO_INCOMPLETO, REGLA_SALDO_INCOMPLETO

        raise BusinessRuleViolation(MENSAJE_SALDO_INCOMPLETO, REGLA_SALDO_INCOMPLETO)
    if quantity > balance:""")
R(O, """        saldo = await saldo_de(db, lot_id)
        if saldo - n < 0:""", """        saldo = await saldo_de(db, lot_id)
        if saldo is None:
            # SPEC 018 §10: con el saldo inicial UNKNOWN no se puede demostrar que el lote quede `≥ 0`.
            from ..cutover.saldo_incubadora import MENSAJE_SALDO_INCOMPLETO, REGLA_SALDO_INCOMPLETO

            raise BusinessRuleViolation(MENSAJE_SALDO_INCOMPLETO, REGLA_SALDO_INCOMPLETO)
        if saldo - n < 0:""")

# ── preview (derivado) ──────────────────────────────────────────────────────
V = "backend/app/cutover/validation.py"
R(V, """            # D-24: saldo disponible para cargar = recibidos − cargados − no incubables − fosa, solo si
            # TODOS son KNOWN; con un UNKNOWN el saldo es UNKNOWN (no se da una cifra definitiva).
            if _known(fila, "eggs_received", "eggs_set", *_SALIDAS_PRE_CARGA):
                derivados["eggs_available_to_set"] = (_val(fila, "eggs_received") - _val(fila, "eggs_set")
                                                     - sum(_val(fila, c) for c in _SALIDAS_PRE_CARGA))
            else:
                derivados["eggs_available_to_set"] = None
            return
""", """            # D-24 + §10: saldo disponible para cargar con la función canónica (la misma de la
            # reconciliación y de BR-03): exacto solo si los seis son KNOWN; con un UNKNOWN, UNKNOWN.
            from .saldo_incubadora import saldo_apertura_por_cargar

            valores = {c: (_val(fila, c) if _known(fila, c) else None)
                       for c in ("eggs_received", "eggs_set", *_SALIDAS_PRE_CARGA)}
            derivados["eggs_available_to_set"] = saldo_apertura_por_cargar(valores, es_v4=True)
            return
""")

# ── reconciliación ──────────────────────────────────────────────────────────
S = "backend/app/cutover/service.py"
R(S, "from .parser import CutoverParseError, parse_cutover_file\n",
  "from .parser import CutoverParseError, parse_cutover_file\nfrom .saldo_incubadora import saldo_apertura_por_cargar, valores_de_apertura\n")
R(S, """                    # D-4 + §9 D-24: no incubables y fosa (PRE-CARGA) restan UNA sola vez, en el saldo
                    # recibido→cargado, y solo si todos son KNOWN (con un UNKNOWN el saldo es UNKNOWN).
                    if None in (recibidos, cargados):
                        disponible = None
                    elif es_v4:
                        disponible = ((recibidos - cargados - total_no_incubable - fosa)
                                      if None not in (total_no_incubable, fosa) else None)
                    else:
                        disponible = recibidos - cargados
""", """                    # D-4 + §9 D-24 + §10: no incubables y fosa (PRE-CARGA) restan UNA sola vez, con la
                    # función canónica compartida con el preview y BR-03 (V4: exacto solo con todo KNOWN).
                    disponible = saldo_apertura_por_cargar(valores_de_apertura(ho), es_v4)
""")
R(S, """                "origin": lote.origin if lote else None, "business_unit": batch.business_unit,
""", """                "origin": lote.origin if lote else None, "business_unit": batch.business_unit,
                # SPEC 018 §10: id de la apertura, para corregirla por la vía gobernada.
                "opening_id": opening.id,
""")
SC = "backend/app/cutover/schemas.py"
R(SC, """    origin: Optional[str] = None
    business_unit: Optional[str] = None
    opening: CutoverOpeningRead""", """    origin: Optional[str] = None
    business_unit: Optional[str] = None
    #: SPEC 018 §10: id del opening (`POST /opening-balances/{id}/corrections`).
    opening_id: Optional[int] = None
    opening: CutoverOpeningRead""")

# ── corrección gobernada de los componentes pre-carga ───────────────────────
C = "backend/app/cutover/opening_corrections.py"
R(C, "from .models import OpeningBalanceCorrection\n",
  "from .contracts import KNOWN\nfrom .models import OpeningBalanceCorrection\n"
  "from .saldo_incubadora import COMPONENTES_PRE_CARGA, es_version_v4, valores_de_apertura, version_de_apertura\n")
R(C, """    "accumulated_culls_mixed",
)
""", """    "accumulated_culls_mixed",
)

#: SPEC 018 §10 · BR-03 UNKNOWN FAIL-SAFE: componentes PRE-CARGA de una apertura de incubadora **V4**
#: (`hatchery_openings`) que la corrección gobernada completa (UNKNOWN → valor) o corrige. Es la vía para
#: que BR-03 vuelva a tener un saldo exacto; el operador nunca escribe un saldo a mano.
CAMPOS_CORREGIBLES_INCUBADORA = COMPONENTES_PRE_CARGA
""")
R(C, """        opening = await self._opening_propio(opening_id)
        if data.field not in CAMPOS_CORREGIBLES:""", """        opening = await self._opening_propio(opening_id)
        if data.field in CAMPOS_CORREGIBLES_INCUBADORA:
            return await self._corregir_incubadora(opening, data)
        if data.field not in CAMPOS_CORREGIBLES:""")
R(C, """    async def listar(self, opening_id: int) -> list[OpeningBalanceCorrection]:""", '''    async def _corregir_incubadora(self, opening: OpeningBalance, data) -> OpeningBalanceCorrection:
        """Completa o corrige un componente pre-carga de una apertura de incubadora V4 (SPEC 018 §10).

        Conserva el original (`old_value` vacío = era UNKNOWN), exige razón, audita y no deja una apertura
        imposible: el componente y la suma conocida `cargados + no incubables + fosa` no superan lo recibido.
        """
        from .models import HatcheryOpening

        apertura = (await self.db.execute(
            select(HatcheryOpening).where(HatcheryOpening.opening_id == opening.id))).scalar_one_or_none()
        if apertura is None or not es_version_v4(await version_de_apertura(self.db, opening.lot_id)):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"CORRECTION_FIELD_INVALID: '{data.field}' no es un campo corregible")
        if data.new_value < 0:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="CORRECTION_VALUE_INVALID: el valor no puede ser negativo")

        valores = valores_de_apertura(apertura)
        viejo = valores[data.field]            # None = UNKNOWN (se conserva como tal)
        nuevo = int(data.new_value)
        valores[data.field] = nuevo
        recibidos = valores["eggs_received"]
        conocidos = (valores["eggs_set"] or 0) + sum(valores[c] for c in COMPONENTES_PRE_CARGA if valores[c] is not None)
        if recibidos is not None and (nuevo > recibidos or conocidos > recibidos):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="CORRECTION_VALUE_INVALID: cargados + no incubables + fosa superarían los huevos recibidos")

        setattr(apertura, data.field, nuevo)
        setattr(apertura, f"{data.field}_status", KNOWN)
        correccion = OpeningBalanceCorrection(
            opening_id=opening.id,
            field=data.field,
            old_value=None if viejo is None else str(viejo),
            new_value=str(nuevo),
            delta=None if viejo is None else str(nuevo - viejo),
            reason=data.reason,
            requested_by_id=int(self.current_user["id"]),
            applied_at=datetime.now(timezone.utc),
        )
        self.db.add(correccion)
        await self.db.flush()

        await audit_accion(
            self.db, usuario=self.current_user, accion=AuditAction.CORRECT,
            modulo=AuditModule.CUTOVER, entity_type="opening_balance",
            entity_id=str(opening.id), company_id=self._empresa(), lot_id=opening.lot_id,
            previous_values={data.field: viejo, f"{data.field}_status": "UNKNOWN" if viejo is None else KNOWN},
            new_values={data.field: nuevo, f"{data.field}_status": KNOWN},
            change_reason=data.reason,
        )
        await self.db.commit()
        await self.db.refresh(correccion)
        return correccion

    async def listar(self, opening_id: int) -> list[OpeningBalanceCorrection]:''')

# ── spec 018 §10 ────────────────────────────────────────────────────────────
F = "specs/018-cutover-hatchery-v4-non-incubables/spec.md"
R(F, "**Estado §9:** ver `audit/ga-hatchery-v4-od02-pit-preload/CERTIFICATION.md`.",
  """**Estado §9:** ver `audit/ga-hatchery-v4-od02-pit-preload/CERTIFICATION.md`. La regla D-25 (BR-03 «un UNKNOWN no se resta») queda **reemplazada por §10**.

## 10. BR-03 UNKNOWN FAIL-SAFE — integridad del saldo disponible posterior al corte (2026-11-26)

Mandato `GA-HATCHERY-V4-BR03-UNKNOWN-FAILSAFE`. No reabre la semántica PRE-CARGA (§9) ni el balance post-carga (`eggs_in_process = set − transferred`).

**Defecto (revisión de la Owner sobre el cierre de §9).** D-25 permitía que BR-03 omitiera un componente pre-carga UNKNOWN y autorizara cargas con la suma conocida. Esa cifra es una **cota superior**, no un saldo demostrado: con `received 10000, set 8500, oversized 200, dirty UNKNOWN, broken 100, pit 200` BR-03 daba 1000; si `dirty` era 700, el saldo real era 300 y se podían cargar 800 (**sobreconsumo de 500**).

**Doctrina:** `UNKNOWN ≠ 0` y `UNKNOWN ≠ SAFE_TO_IGNORE`.

- **D-28 saldo canónico.** Una sola función (`backend/app/cutover/saldo_incubadora.py · saldo_apertura_por_cargar`) da el saldo de apertura por cargar a preview (`derived.eggs_available_to_set`), reconciliación (`current.eggs_available_hatchery`) y BR-03 (`get_hatchery_egg_balance`). V4: `received − set − oversized − dirty − broken − pit` solo si los seis son KNOWN; si cualquiera es UNKNOWN ⇒ **UNKNOWN**. `0` conocido es un cero real. V3 histórica: `received − set` (su contrato no tenía esos componentes; sin cambios).
- **D-29 dos usos distintos de la suma parcial conocida.** *Consistencia* (D-21): `set + Σ(pre-carga KNOWN) ≤ received` sí se evalúa con UNKNOWN y, si la supera, la fila se rechaza de inmediato. *Autorización* de una carga nueva: **no** puede usar la cota; exige saldo exacto (`KNOWN`).
- **D-30 BR-03.** `quantity > 0` y saldo UNKNOWN ⇒ **400** `rule = CUTOVER_BALANCE_INCOMPLETE`, mensaje funcional: «No se puede determinar el saldo disponible para cargar porque la carga inicial de Incubadora contiene valores desconocidos. Corrija o complete la carga inicial antes de registrar una nueva carga de huevos.» La misma regla protege la anulación/reasignación de una recepción en incubadora (no se puede demostrar que el lote quede `≥ 0`). Un lote sin apertura migrada no cambia.
- **D-31 corrección gobernada.** El operador nunca escribe un saldo. `POST /opening-balances/{id}/corrections` (permiso `corrections:correct`, razón obligatoria, auditado, conserva el original: `old_value` vacío = era UNKNOWN) admite ahora los cuatro componentes pre-carga de una apertura **V4** y rechaza (422) un valor que deje `cargados + no incubables + fosa > recibidos`. Con los seis componentes KNOWN, BR-03 vuelve a operar. La reconciliación expone `opening_id` para esa corrección.

| AC | Enunciado |
|---|---|
| AC-V4-30 | BR03-U01: `dirty` UNKNOWN ⇒ saldo UNKNOWN en preview, reconciliación y BR-03; carga de 1 ⇒ 400 `CUTOVER_BALANCE_INCOMPLETE`. |
| AC-V4-31 | BR03-U02: corregir `dirty = 700` ⇒ saldo 300; cargar 300 ⇒ 201; 1 más ⇒ 400 BR-03. |
| AC-V4-32 | BR03-U03: `dirty = 0` conocido ⇒ saldo 1000; cargar 1000 ⇒ 201. |
| AC-V4-33 | BR03-U04: con un UNKNOWN, la suma conocida > recibidos ⇒ fila rechazada; una corrección que la provocaría ⇒ 422. |
| AC-V4-34 | BR03-U05/U06: UNKNOWN en la fosa o en cualquiera de los tres no incubables ⇒ misma denegación (sin trato especial para la fosa). |
| AC-V4-35 | BR03-U07: todo KNOWN (10000/8500/200/200/100/200) ⇒ saldo 800; 800 ⇒ 201; 801 ⇒ 400 BR-03. |
| AC-V4-36 | V3 histórica sin cambios; anular una recepción de incubadora con saldo inicial UNKNOWN ⇒ 400 `CUTOVER_BALANCE_INCOMPLETE`. |

**Estado §10:** ver `audit/ga-hatchery-v4-br03-unknown-failsafe/CERTIFICATION.md`.""")

if ERR:
    print("ERRORES:\n" + "\n".join(ERR))
    sys.exit(1)
print("OK: BR-03 UNKNOWN FAIL-SAFE aplicado")
