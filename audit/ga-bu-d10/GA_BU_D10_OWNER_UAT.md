# GA-BU-D10 · GUÍA DE UAT DEL PROPIETARIO (OD-23 · B)

Estado: **READY** — la UAT **no se inicia automáticamente**; se activará por instrucción del propietario (operaciones prepara ventana y actor temporales; credenciales fuera del repositorio, destruidas al cierre).

**Cierre: EJECUTADA — decisión A) ACEPTO R-188 / BU-D10 / OD-23 (GA-UAT-08, 2026-09-11; registro `audit/ga-uat-08/GA_OWNER_ACCEPTANCE_R188_BU_D10_RECORD.md`).**

## Qué validar (solo el resultado visible)

1. **Con acceso**: con la línea encendida y una concesión vigente, el operador entra a sus lotes y ve el IPE normalmente (p. ej. `L-R187-DET` → **333.3**).
2. **Al apagar la línea**: el operador **pierde** el acceso productivo (no ve lotes ni datos; sin errores crudos) — mientras el administrador de accesos sigue administrando.
3. **Al volver a encender la línea (la decisión OD-23)**: el operador **NO recupera acceso solo** — sigue sin ver datos.
4. **Con una concesión nueva** del administrador de accesos: el acceso **se restaura**.
5. **Móvil**: el mismo comportamiento es legible y usable (390×844).

## Redacción de la pregunta (UAT)

> «¿El producto refleja ahora la política que usted aprobó: apagar una línea termina los accesos existentes y volver a encenderla NO los devuelve — hace falta una concesión nueva?»

## Qué NO debe probar el propietario

Endpoints, tipos de dato, matriz de seguridad completa (ya certificadas), ni repetir cálculos.

## Decisión a solicitar (posterior, sesión UAT)

**A)** ACEPTO R-188 · **B)** ACEPTO R-188 CON OBSERVACIONES: `<texto>` · **C)** RECHAZO R-188 — CORREGIR: `<texto>`.

## Notas operativas

- Fixtures de lotes permanecen (`L-R187-*`); la ventana de unidad y actores sintéticos se montan por operaciones con el mismo procedimiento de esta tranche (batería documentada).
- Sin auto-aprobación: el agente técnico no firma esta aceptación.
