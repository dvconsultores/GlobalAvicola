# GA-UAT-08 · ACEPTACIÓN DEL PROPIETARIO — R-188 / BU-D10 / OD-23

Clasificación: **ACEPTACIÓN DEL PROPIETARIO (no auto-aprobada)**. Registrada únicamente tras la respuesta explícita del propietario.

## 1 · Decisión registrada

**A) ACEPTO R-188 / BU-D10 / OD-23** — «La validación visible es correcta: con concesión válida hay acceso; apagar la unidad lo quita; re-encender NO lo devuelve; una concesión nueva lo restaura.»

- Fecha: 2026-09-11 · Decisor: **Propietario**
- Sin observaciones adicionales (opción sin texto libre).

## 2 · Casos del propietario

| UAT ID | Resultado |
|---|---|
| UAT-01 (acceso válido) | **PASS** |
| UAT-02 (apagar quita acceso) | **PASS** |
| UAT-03 (re-encender no devuelve) | **PASS** |
| UAT-04 (concesión nueva restaura) | **PASS** |
| UAT-05 (móvil/navegación) | **PASS** |

## 3 · Estados actualizados

| Ítem | Antes | Ahora |
|---|---|---|
| R-188 | CLOSED_FUNCTIONALLY_CERTIFIED (Owner UAT pendiente) | **CLOSED_OWNER_ACCEPTED** |
| BU-D10 | RESOLVED | **RESOLVED_OWNER_ACCEPTED** |
| OD-23 | RATIFIED_IMPLEMENTED | **RATIFIED_IMPLEMENTED_OWNER_ACCEPTED** |
| OWNER ACCEPTANCE | PENDING | **PASS** |

## 4 · Evidencia de la aceptación

- Walkthrough de referencia: `GA_OWNER_UAT_R188_EVIDENCE.md` (C01-C08; TODOS PASS).
- Capturas: `evidence/C01..C08` · Raw: `evidence/walkthrough-uat.json`, `evidence/setup-uat.json`, `evidence/cleanup-uat.json`.
- Guía entregada al propietario: `GA_OWNER_UAT_R188_GUIDE.md` (5 casos, sin tecnicismos).
- Observaciones: `GA_OWNER_UAT_R188_OBSERVATIONS.md` — **sin observaciones** (decisión A).

## 5 · Protecciones verificadas en el walkthrough

- Concesión válida ⇒ acceso visible (UAT-01).
- Apagar la unidad ⇒ acceso retirado de inmediato (UAT-02, incluido móvil C08).
- **Re-encender NO restaura el acceso histórico** — línea válida solo con **concesión nueva** (UAT-03/UAT-04, caso central de OD-23).
- Regrant probado por la **UI real** del Access Administrator («Conceder»).
- Sin regresión visible de seguridad · sin datos ajenos · consola sin errores.
- Certificaciones previas (R-184/R-186/R-187, OD-16) preservadas.

## 6 · Limpieza ejecutada

Limpieza post-decisión completada: concesión revocada (200) · usuarios 146/147 baja lógica (204/204) · roles 92/93 desactivados (200/200) · **BU Engorde OFF restaurada — catálogo 4×OFF** · credenciales y temporales destruidos · ningún humano modificado · admin operativo (200). Detalle: `evidence/cleanup-uat.json` y sección G de la evidencia.
