# GA-UAT-07 · R-187 — REGISTRO DE ACEPTACIÓN DEL PROPIETARIO

Fecha: 2026-09-11 · **Decisión: A) ACEPTO R-187** (respuesta explícita del propietario; sin observaciones)

## 1 · Decisión

El propietario validó la implementación visible de OD-22 (IPE G-06 a escala estándar) y aceptó R-187.
Texto exacto de la decisión: **«ACEPTO R-187»** (opción A de las tres ofrecidas: A/Acepto · B/Acepto con observaciones · C/Rechazo). No se registraron observaciones.

## 2 · Estados resultantes

| Ítem | Estado |
|---|---|
| R-187 | **CLOSED_OWNER_ACCEPTED** · OWNER_ACCEPTANCE: **PASS** |
| OD-22 | **RATIFIED_IMPLEMENTED_OWNER_ACCEPTED** (existe como estado canónico: p. ej. OD-21) |
| R-184 | CLOSED_OWNER_ACCEPTED — sin cambios (556.6 superseded, no reabierto) |
| R-186 | CLOSED_FUNCTIONALLY_CERTIFIED — sin cambios |
| OBS-UAT-01 / BU-D10 | UX P2 sin R / PENDING_RATIFICATION — sin tocar |

## 3 · Validación realizada (6/6 casos)

UAT-01 nuevo valor (333.3 · 🟢) · UAT-02 clasificación coherente (🟢 y apoyo 🟡 282.7) · UAT-03 detalle=reporte (333.3 ambos) · UAT-04 refresh/relogin estables · UAT-05 móvil 390×844 usable (overflow 0) · UAT-06 aceptación global → **A**.
Walkthrough de referencia: `evidence/walkthrough-uat.json` + capturas C01-C07 (índice en `GA_OWNER_UAT_R187_SCREENSHOT_INDEX.md`). Notas N-1…N-3 registradas como informativas, sin acción.

## 4 · Evidencia y git

- Paquete UAT: `audit/ga-uat-07/` · **C1 `d1f9829`** (paquete) · **C2** decisión/limpieza (commit de este registro).
- Sin cambios de producto (frontend 0 · backend solo la implementación ya certificada `f755baa`).

## 5 · Limpieza ejecutada

Concesión revocada (200) · operador sintético 141 baja lógica (204) · rol 71 desactivado (200) · **BU broiler OFF restaurada (4×OFF verificado)** · credenciales `~/ga_uat07_credentials.txt` y temporales destruidos · admin verificado operativo · ningún usuario humano modificado · evidencia preservada (`audit/`).

## 6 · Alcance y no-reapertura

Ninguna decisión se reabrió: OD-22 permanece RATIFIED (implementada y aceptada); R-184/R-186 intactos; ninguna tranche nueva iniciada. Fixtures de lotes `L-R187-*` permanecen retenidos (documentados en ledger) para reproducibilidad.
