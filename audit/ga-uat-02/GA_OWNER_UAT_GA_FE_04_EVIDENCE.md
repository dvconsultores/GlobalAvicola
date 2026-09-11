# GA-UAT-02 · EVIDENCIA DE INGENIERÍA — GA-FE-04 (precondiciones y ejecución de referencia)

Fecha: 2026-09-11 · Generación: **`index-B66tpdeW.js`** (producto `de40d36`) · Baseline canónico: `820dfc0`
Entorno: https://avicola.globaldv.net · smoke de la generación: tsc **0** · build **PASS** · Vitest **263/263** (34 archivos) · GA-FE-04 dirigida **22/22**.

## 1 · Fixtures de la sesión guiada (sintéticos, mecanismos oficiales)

| Elemento | Detalle | Verificación | Estado final |
|---|---|---|---|
| Rol 41 «GA-FE04 TEST READ-ONLY ADMIN» | reactivado (`is_active=true`) | dashboard:read · masters:read · users:read | se desactiva al cierre |
| Usuario `uat2-lector` (id 108) | rol 41, empresa 1, vista web | `/me`: 3 permisos, sin unidades | baja al cierre |
| Cuenta autorizada | Super Administrador (cuenta habitual del propietario) | empresa seleccionada en la sesión | sin cambios |

- Credenciales efímeras: `~/ga_uat_02_credentials.txt` (fuera del repositorio; se destruye al cierre).
- Unidades de empresa: **sin cambios** (4×OFF como al inicio). Sin concesiones nuevas.
- Caso «aprobar≠rechazar» excluido de la sesión visible: `GET /approvals/pending` = **total 0**
  (no hay registros pendientes en la empresa de pruebas). Cubierto por evidencia técnica.

## 2 · Ejecución de referencia de los 6 casos (mediciones duras)

| Caso | Actor | Medición | Captura |
|---|---|---|---|
| 01 · Maestros→Granjas | uat2-lector | filas **7** (lectura OK) · Nuevo **0** · Editar **0** · Eliminar **0** · aviso «Vista de solo lectura» **1** | `c01_lector_maestros_sin_acciones.png` |
| 02 · Usuarios | uat2-lector | Crear **0** · lápiz **0** · papelera **0** · aviso **1** | `c02_lector_usuarios_sin_acciones.png` |
| 03 · Menú | uat2-lector | enlaces productivos **0** · «Acceso por unidad» **0** · tarjeta en Configuración **0** · sidebar: Dashboard, Maestros, Configuración (consulta) | `c03_lector_menu_sin_areas_privilegiadas.png` |
| 04 · Control positivo | Super Administrador (empresa «Avícola Global C.A.») | filas **7** · Nuevo **1** · Editar **7** · sin aviso de solo lectura | `c04_autorizado_controles_visibles.png` |
| 05 · Móvil 390×844 | uat2-lector | Nuevo **0** · Editar **0** · aviso **1** | `c05_lector_movil_sin_acciones.png` |
| 06 · Inglés | uat2-lector | aviso EN «Read-only view…» **1** · botón New/Nuevo **0** | `c06_lector_ingles_aviso.png` |

Nota caso 04: la captura se tomó con la empresa **«Avícola Global C.A.»** seleccionada en la
barra superior (el propietario hace lo mismo con su cuenta).

## 3 · Trazabilidad técnica de la entrega (referencia)

- P13-AC20 self-grant **PASS** · P13-AC21 cross-company **PASS** · R-98 **CLOSED**
  (`audit/ga-fe-04/GA_FE_04_A_SELF_CROSS_RUNTIME_EVIDENCE.md`).
- R-98 reconciliación C1–C5 ✅ (`GA_FE_04_R98_CLOSURE_RECONCILIATION.md`).
- OBS-01 documentado y no bloqueante — **sin reclasificar**.

## 4 · Alcance de esta sesión

- Validación del resultado visible de GA-FE-04 (R-98/P-13): «quien solo lee no ve acciones de
  escritura» y «quien sí puede, las conserva» (control positivo).
- No repite GA-FE-02/GA-FE-03 (ya aceptados). No abre nuevas tranches.
- Decisión esperada: **A) ACEPTO GA-FE-04** · B) con observaciones · C) rechazo.
