# GA-BU-D10 · RECONSTRUCCIÓN DE FUENTES

Fecha: 2026-09-11 · Baseline: `8e91532` · Hogar: `audit/ga-bu-d10/` · Solo gobernanza (0 producto).

## 1 · Qué es BU-D10

La pregunta de ciclo de vida: **cuando una empresa apaga una unidad de negocio (línea) y después la vuelve a encender, ¿qué ocurre con las concesiones de usuario que ya existían?** ¿Vuelven a ser efectivas automáticamente (A) o cada usuario necesita una concesión nueva y explícita (B)?

Ámbito estricto: **misma empresa, mismo usuario, misma unidad, sin transferencia de empresa.** El ciclo de transferencia de empresa es una regla separada (OD-09.e) y no se toca.

## 2 · Cadena de origen (primera aparición → hoy)

| Fecha | Eslabón | Contenido |
|---|---|---|
| 2026-09-07 | `BUSINESS_UNIT_OWNER_DECISION_MATRIX.md` §1 | Nace `BU-D10` («La empresa deja de tener una línea», nueva en la serie de 12; «nadie preguntó qué pasa al **quitar** una línea, solo al darla»). Estado: `PENDIENTE`. |
| 2026-09-07 | `OD-09` (specs/remediation) | Fija el régimen de concesiones (OD-09.d empresa-scoped; OD-09.e: la concesión **se marca**, no se borra; «volver a la empresa A» no reactiva). BU-D10 queda fuera, deliberadamente. |
| 2026-09-09 | `AUDIT_OWNER_DECISIONS_REQUIRED.md` | Fila `BU-D10`: «**no se toca** (instrucción expresa)». Único estado: `PENDING_RATIFICATION`. |
| 2026-09-09 | `BUSINESS_UNIT_OWNER_DECISION_MATRIX.md` §7 (WAVE A0-P) | Estado exacto: *«comportamiento provisional vigente = opción A (GA-REM-040 §6.3 · AC-A06): al rehabilitar, la concesión previa vuelve a ser efectiva… opción B (concesión nueva explícita) NO elegida · NO descartada · ningún cambio de código depende de la elección»*. |
| 2026-09-09 | `GLOBAL_AVICOLA_MASTER_360_ADDENDUM_PRODUCT_SCOPE_AND_COMPANY_BU.md §6` | Misma redacción canónica + test que la prueba. |
| OD-16 (2026-09-10/11) | `OD-16.e` | La activación por empresa se formaliza **absoluta** para acceso productivo, y **deja BU-D10 separada a propósito** («Dejar BU-D10 separada…»). |
| GA-FE-02 / GA-FE-02-D/E (2026-09-11) | Observación en certificación | Contrato B06: «apagar **no borra** concesiones; re-encender las devuelve (**provisional, `BU-D10` pendiente**)». Runtime E2E-03: con lote 4×OFF, «concesión almacenada viva `is_effective=false` (BU-D10 obs.)». `PENDING_RATIFICATION` se propaga sin cambio por todas las tranches posteriores (R-184…GA-UAT-07). |

## 3 · Redacción canónica vigente (la que gobierna esta decisión)

> `BU-D10` · `PENDING_RATIFICATION`
> comportamiento provisional vigente = opción A (GA-REM-040 §6.3 · AC-A06): al rehabilitar, la concesión previa vuelve a ser efectiva
> prueba: `test_deshabilitar_no_borra_las_concesiones_y_rehabilitar_las_devuelve`
> opción B (concesión nueva explícita) NO elegida · NO descartada
> ningún cambio de código depende de la elección
> — `BUSINESS_UNIT_OWNER_DECISION_MATRIX.md §7` + addendum §6

## 4 · Comportamiento provisional actual (probado)

1. **BU ON + concesión viva** ⇒ efectiva (ALLOW productivo).
2. **BU OFF** ⇒ la concesión **sigue escrita** (apagar no revoca, `AC-A04`) y **deja de ser efectiva** (el resolutor exige `is_enabled`).
3. **BU ON de nuevo** ⇒ la concesión previa **vuelve a ser efectiva sin volver a concederla** (`AC-A06`) ⇒ **hoy = Opción A**.
4. **Conceder con BU OFF** ⇒ rechazado («la empresa no tiene habilitada la unidad; habilítela primero») — conceder no configura.

## 5 · Pruebas que lo demuestran (evidencia, no memoria)

| Prueba | Archivo | Qué acredita |
|---|---|---|
| `test_deshabilitar_no_borra_las_concesiones_y_rehabilitar_las_devuelve` | `backend/tests/test_business_unit_admin.py:318` | Ciclo completo OFF→ON sin reconceder («`AC-A06`: vuelve sin volver a concederla»); sigue escrita al apagar. |
| `test_ac_a04_apagar_una_unidad_no_borra_las_concesiones` | `backend/tests/test_business_units.py:491` | «Si apagar borrase las concesiones, el propietario ya no podría elegir». Reversibilidad = BU-D10 abierta. |
| `test_ac_a06_rehabilitar_devuelve_la_efectividad_a_la_concesion_previa` | `backend/tests/test_business_units.py:509` | Efectividad restaurada por el modelo, sin recorrer usuarios. |
| Runtime OD-16 (GA-FE-02-D/E) | `audit/ga-fe-02-d/*`, `audit/ga-fe-02-e/*` | Con sesión activa: OFF ⇒ DENY inmediato; concesión viva almacenada `is_effective=false`. |

## 6 · Por qué la ratificación seguía pendiente

- La conducta **no es un defecto**: es una **decisión de negocio previsible pero no tomada**. El código la mantiene reversible a propósito (`admin.py`: «Un borrado aquí habría contestado `BU-D10` por omisión»).
- `OD-16.e` reservó la decisión de forma expresa; toda la gobernanza posterior la preservó como `PENDING_RATIFICATION`.
- Es una decisión de **política de seguridad/negocio**: ¿la reapertura de una línea restaura accesos previos (continuidad) o exige re-autorización (mínimo privilegio)?
