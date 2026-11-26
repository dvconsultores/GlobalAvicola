#!/usr/bin/env python3
"""Cierre del mutante superviviente B02 (RR-27 · tipo de corrección inactivo aceptado).

1. Test nuevo `OD01-05`: un tipo desactivado no tipifica correcciones nuevas (400 RR-27) y,
   reactivado, vuelve a servir (201) — la causa del 400 es la inactividad, no otra.
2. Los helpers de tests toman un tipo ACTIVO (antes, la primera fila aunque estuviera inactiva:
   la misma fragilidad que hizo fallar la E2E cuando otro test desactivó el único tipo).
Desde la raíz del repo."""
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


F = "backend/tests/owner_decisions_support.py"
R(F, '''    """Id de un tipo de corrección de la empresa (se crea uno si no hay)."""
    filas = await _lista(client, headers, "correction-types")
    if filas:
        return filas[0]["id"]''', '''    """Id de un tipo de corrección ACTIVO de la empresa (se crea uno si no hay)."""
    filas = [f for f in await _lista(client, headers, "correction-types") if f.get("is_active", True)]
    if filas:
        return filas[0]["id"]''')
R(F, '''    """Id de un tipo de alimento de la empresa (se crea uno si no hay)."""
    filas = await _lista(client, headers, "feed-types")
    if filas:
        return filas[0]["id"]''', '''    """Id de un tipo de alimento ACTIVO de la empresa (se crea uno si no hay)."""
    filas = [f for f in await _lista(client, headers, "feed-types") if f.get("is_active", True)]
    if filas:
        return filas[0]["id"]''')

F = "backend/tests/test_uat_s2_owner_decisions_a.py"
R(F, '''    items = await _lista(client, headers, "correction-types")
    if items:
        return items[0]["id"]''', '''    items = [i for i in await _lista(client, headers, "correction-types") if i.get("is_active", True)]
    if items:
        return items[0]["id"]''')
R(F, '''    assert de_otra_empresa.status_code == 400, de_otra_empresa.text
    assert de_otra_empresa.json()["detail"] == MENSAJE_TIPO, de_otra_empresa.json()
''', '''    assert de_otra_empresa.status_code == 400, de_otra_empresa.text
    assert de_otra_empresa.json()["detail"] == MENSAJE_TIPO, de_otra_empresa.json()


@pytest.mark.asyncio
async def test_od01_05_tipo_inactivo_es_400_y_reactivado_vuelve_a_servir(auth_headers, client):
    """`OD01-05` · `RR-27` (`OD-21`): un tipo desactivado no tipifica correcciones nuevas.

    El catálogo conserva el tipo (las correcciones históricas lo siguen nombrando), pero una
    corrección nueva con él es 400 con el mismo mensaje que «sin tipo». Reactivado, el mismo
    tipo vuelve a servir: el rechazo se debe a la inactividad y a nada más.
    """
    alta = await client.post("/api/v1/masters/correction-types", headers=auth_headers,
                             json={"name": f"Tipo retirado {uuid.uuid4().hex[:6].upper()}"})
    assert alta.status_code == 201, alta.text
    tipo = alta.json()["id"]
    evento = await _alta_vacunacion(client, auth_headers, vaccine_lot_number="OD-VAC-05")
    assert evento.status_code == 201, evento.text
    event_id = evento.json()["id"]

    baja = await client.put(f"/api/v1/masters/correction-types/{tipo}", headers=auth_headers,
                            json={"is_active": False})
    assert baja.status_code == 200, baja.text
    assert baja.json()["is_active"] is False, baja.json()

    inactivo = await _corregir(client, auth_headers, event_id, "observations", "x", tipo=tipo)
    assert inactivo.status_code == 400, inactivo.text
    assert inactivo.json()["detail"] == MENSAJE_TIPO, inactivo.json()
    assert inactivo.json()["rule"] == "RR-27", inactivo.json()

    reactivado = await client.put(f"/api/v1/masters/correction-types/{tipo}", headers=auth_headers,
                                  json={"is_active": True})
    assert reactivado.status_code == 200, reactivado.text
    ok = await _corregir(client, auth_headers, event_id, "observations", "x", tipo=tipo)
    assert ok.status_code == 201, ok.text
    assert ok.json()["correction_type_id"] == tipo, ok.json()
''')

F = "backend/tests/test_uat_s2_corrections_masters.py"
R(F, '''    items = datos["items"] if isinstance(datos, dict) else datos
    if items:
        return items[0]["id"]
    r = await client.post("/api/v1/masters/correction-types", headers=headers,
                          json={"name": f"Tipo UATS2 {uuid.uuid4().hex[:6].upper()}"})''',
  '''    items = [i for i in (datos["items"] if isinstance(datos, dict) else datos) if i.get("is_active", True)]
    if items:
        return items[0]["id"]
    r = await client.post("/api/v1/masters/correction-types", headers=headers,
                          json={"name": f"Tipo UATS2 {uuid.uuid4().hex[:6].upper()}"})''')

if ERR:
    print("ERRORES:\n" + "\n".join(ERR))
    sys.exit(1)
print("OK: parches aplicados")
