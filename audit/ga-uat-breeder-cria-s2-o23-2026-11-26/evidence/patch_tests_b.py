#!/usr/bin/env python3
"""O-23 · ajustes del test backend (desde la raíz del repo): AC correctos, S01 exacto, OD-21 y casos nuevos."""
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


F = "backend/tests/test_uat_s2_o23_null_to_master.py"
R(F, '"""`AC-O23-01`: el selector anuncia', '"""`AC-O23-01/02`: el selector anuncia')
R(F, '"""`AC-O23-01`: una mortalidad no ofrece', '"""`AC-O23-01/02`: una mortalidad no ofrece')
R(F, '"""`AC-O23-02`: el antes nulo', '"""`AC-O23-03` (A) y `AC-O23-06`: el antes nulo')
R(F, '"""`AC-O23-03`: un maestro dado de baja', '"""`AC-O23-05`: un maestro dado de baja')
R(F, '"""`AC-O23-04`: el maestro de la otra empresa', '"""`AC-O23-03` (D): el maestro de la otra empresa')
R(F, '"""`AC-O23-05`: la corrección de un maestro ya cargado', '"""`AC-O23-03` (B): la corrección de un maestro ya cargado')
R(F, '"""`AC-O23-06`: `RR-32` impide', '"""`AC-O23-03` (C) y `AC-O23-08`: `RR-32` impide')
R(F, '"""`AC-O23-07`: el proveedor es anulable', '"""`AC-O23-03` (C): el proveedor es anulable')
R(F, '"""`AC-O23-08`: historial y auditoría', '"""`AC-O23-06`: historial y auditoría')
R(F, '"""`AC-O23-09` (cierre): el campo no pertenece', '"""`AC-O23-04`: el campo no pertenece')
R(F, """    # Valor observado hoy: 404 (el evento no existe para la otra empresa).
    assert cruzado.status_code in (403, 404), cruzado.text""",
  """    # Fail closed: el evento de otra empresa no existe para el actor (404).
    assert cruzado.status_code == 404, cruzado.text""")
R(F, """    r = await _corregir(client, auth_headers, evento["id"], "supplier_id", str(proveedor_id))
    assert r.status_code == 400, r.text

    assert (await _detalle(client, auth_headers, evento["id"]))["supplier_id"] is None
    historial""",
  """    r = await _corregir(client, auth_headers, evento["id"], "supplier_id", str(proveedor_id))
    assert r.status_code == 400, r.text
    assert r.json().get("rule") == "OD-21", r.text

    assert (await _detalle(client, auth_headers, evento["id"]))["supplier_id"] is None
    historial""")

p = Path(F)
p.write_text(p.read_text(encoding="utf-8").rstrip("\n") + '''


# ── O23-B03b · tampoco se cambia a un proveedor desactivado ──────────────────

@pytest.mark.asyncio
async def test_o23_b03b_cambiar_a_un_proveedor_desactivado_es_400(auth_headers, client):
    """`AC-O23-05`: `OD-21` vale sea cual sea el original; el evento conserva su proveedor."""
    id_a, _ = await _proveedor(client, auth_headers)
    id_b, _ = await _proveedor(client, auth_headers)
    baja = await client.delete(f"/api/v1/masters/suppliers/{id_b}", headers=auth_headers)
    assert baja.status_code == 204, baja.text
    evento = await _recepcion_con_proveedor(client, auth_headers, id_a)

    r = await _corregir(client, auth_headers, evento["id"], "supplier_id", str(id_b))
    assert r.status_code == 400, r.text
    assert r.json().get("rule") == "OD-21", r.text

    assert (await _detalle(client, auth_headers, evento["id"]))["supplier_id"] == id_a


# ── O23-B09b · la recepción no anuncia maestros ajenos a su tipo ─────────────

@pytest.mark.asyncio
async def test_o23_b09b_la_recepcion_no_ofrece_vacuna_ni_causa(auth_headers, client):
    """`AC-O23-01`: el selector de una recepción no ofrece vacuna, causa ni medicamento vacíos."""
    evento = await _recepcion_sin_proveedor(client, auth_headers)

    campos = await _campos(client, auth_headers, evento["id"])
    assert not _tiene(campos, "vaccine_id"), _nombres(campos)
    assert not _tiene(campos, "cause_id"), _nombres(campos)
    assert not _tiene(campos, "medication_id"), _nombres(campos)


# ── O23-B10 · el original hoy inactivo se sigue leyendo por nombre ───────────

@pytest.mark.asyncio
async def test_o23_b10_un_original_hoy_inactivo_se_sigue_leyendo(auth_headers, client):
    """`AC-O23-05`: la baja lógica no oculta el valor histórico del evento."""
    id_a, nombre_a = await _proveedor(client, auth_headers)
    evento = await _recepcion_con_proveedor(client, auth_headers, id_a)
    baja = await client.delete(f"/api/v1/masters/suppliers/{id_a}", headers=auth_headers)
    assert baja.status_code == 204, baja.text

    entrada = _por_sufijo(await _campos(client, auth_headers, evento["id"]), "supplier_id")
    assert entrada["current_value"] == str(id_a), entrada
    assert entrada["current_display"] == nombre_a, entrada
''', encoding="utf-8")

if ERR:
    print("ERRORES:\n" + "\n".join(ERR))
    sys.exit(1)
print("OK: tests O-23 ajustados")
