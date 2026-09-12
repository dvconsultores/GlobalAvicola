# GA-UAT-09 · REFERENCIA DEL RETRY (ATTEMPT 2) — R-153 / OD-25 tras la corrección de F-01

Fecha: 2026-09-13 · Para: propietario (referencia de ingeniería; la aceptación la realiza el propietario)
· Generación del retry: `index-DDCcWL76.js` · Evidencia cruda: `audit/ga-f01/evidence/runtime-c2f/`.

## 1 · Historial de intentos (declarado; el histórico no se reescribe)

| Intento | Fecha | Resultado |
|---|---|---|
| **ATTEMPT 1** (GA-UAT-09) | 2026-09-12 | **STARTED_AND_BLOCKED_BY_F01** — UAT-01 FAIL (guardado rechazado + pantalla en blanco); UAT-02…06 no alcanzables; UAT-07 parcial. Ver `GA_OWNER_UAT_R153_OBSERVATIONS.md` (original intacto) |
| **ATTEMPT 2** (retry de referencia) | 2026-09-13 | **7/7 en verde** + 0 errores fatales (esta nota) |

## 2 · Qué se corrigió (y quedó certificado)

- **F-01** (R-189): el guardado del asistente — payload canónico (`[]` en almacenamiento/alimento/incubadora), OC en el campo tipado, y **error 4xx renderizado seguro** (sin pantalla en blanco).
- **F-01d**: tercera superficie del serializado (alimento/incubadora) y detalle del evento sin 500 (lectura tolerante de filas históricas).
- **F-01e**: la recepción por UI ya envía el **galpón** elegido en las filas cuando el lote no lo declara (lotes autocreados `OD-25 (B)`) — antes bloqueaba con 400 BR-08.

Certificación: `audit/ga-f01/GA_F01_RUNTIME_CERTIFICATION.md` (35/35 asserts · 0 fatales · 0×5xx).

## 3 · Los 7 casos del recorrido (referencia — ATTEMPT 2)

| # | Caso | Referencia |
|---|---|---|
| 1 | Registrar importación **sin lote** | ✔ 201 (evento 121) · `C01/C01b/C02s` |
| 2 | Antes de aprobar: «Lote: Se creará al aprobar» | ✔ `C02` |
| 3 | Aprobar ⇒ aparece «Lote: #65» con enlace | ✔ `C03` (L-GP-**2026-11**) |
| 4 | Datos del lote (código, fecha = llegada, sexo, granja) | ✔ `C04` |
| 5 | Sin aves antes de recepcionar (bracket saldo 0) | ✔ `C05` |
| 6 | Recepción (♂40 ♀60) ⇒ aprobada ⇒ el lote la refleja **una vez**; saldo exacto 100 | ✔ `C06a/C06` |
| 7 | Vía manual sigue disponible («Nuevo Lote») | ✔ `C07` |

> La sesión del propietario parte de cero con `GA_OWNER_UAT_R153_GUIDE.md` (misma pareja de cuentas y
> misma unidad; la guía fue actualizada con el estado «LISTA»). El fixture de referencia (lotes
> `L-GP-2026-10/11`, eventos 120–123) queda **retenido** en el ledger hasta la decisión.

## 4 · Correcciones documentales (D-01/D-02)

- D-01: F-01 = alias de descubrimiento; **R-189 = hallazgo canónico**; F-01d/F-01e = extensiones del mismo hallazgo; no se creó ningún R adicional.
- D-02: el primer intento fue **iniciado y bloqueado** (no «7/7 ejecutados»).
