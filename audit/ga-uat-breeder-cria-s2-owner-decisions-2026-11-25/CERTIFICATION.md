# CERTIFICACIÓN LOCAL — GA-UAT-BREEDER-CRIA-S2-OWNER-DECISIONS

Continuación de `GA-UAT-BREEDER-CRIA-S2-2026-11-24` (SESSION2 = PARTIAL). Spec: `specs/020-uat-breeder-cria-s2/spec.md` §6.
Baseline `develop` = `d785c81` (último código de producción previo `8366827`), `main` = `1587073` (sin tocar).
Rama de trabajo: `develop`. Sin PR, sin cambios en `main`, sin despliegue a producción.

## 1. Decisiones Owner (ratificadas el 25-11-2026)

| Decisión | Regla | Estado | Contrato implementado |
|---|---|---|---|
| OD-S2-01 | RR-27 | CLOSED | `POST /corrections` exige `correction_type_id` existente, **activo** y de la empresa (o compartido); 400 «Seleccione el tipo de corrección». UI: selector obligatorio que solo ofrece tipos activos. Correcciones históricas sin tipo: legibles. |
| OD-S2-02 | RR-28 | CLOSED | `farm_inspection` exige al menos un dato: detalle con valor/valor numérico/estado, observación con texto, o evidencia ya adjunta. Los valores por defecto no cuentan. `lot_id NULL` permitido; «Sin lote (nivel granja)» se mantiene. |
| OD-S2-03 | RR-29 | CLOSED | `bird_distribution`: ≥1 movimiento, cada cantidad ≥ 0, Σ > 0. Saldo y capacidad intactos; no se fabrican movimientos cero. |
| OD-S2-04 | RR-30 | CLOSED | Semana derivada y de solo lectura (mortalidad, descarte, pesaje, alimento). Función única `semana_productiva = (fecha_evento − lots.start_date).days // 7 + 1` (edad productiva, no semana ISO). Se recalcula al corregir/editar la fecha o el lote. Sin fecha base o evento anterior al inicio: 400 `LOT_DATE_INCOMPLETE`; no se inventa semana. |
| OD-S2-05 | RR-31 | CLOSED | Vacunación nueva exige `vaccine_lot_number` con texto (`trim ≠ ""`). Históricos `NULL` legibles; sin migración que invente lotes. |
| OD-S2-06 | RR-32 | CLOSED | Mortalidad exige `cause_id`; descarte exige `cull_cause_id`. Valor explícito compartido «Desconocida» sembrado por migración (`NULL ≠ DESCONOCIDA`); sin *backfill*. |
| OD-S2-07 | RR-33 / RR-34 | CLOSED | `feed_type_id` obligatorio en toda fila con kg > 0; fase derivada de la fase vigente del lote (`lot_phases`), persistida en `feed_movements.phase_id`; sin fase vigente: 400 `LOT_PHASE_INCOMPLETE`; no se inventa. Cantidad > 0 (`RR-23`) se mantiene. |

Alta, edición (`PUT`) y corrección comparten las mismas funciones de validación. Las reglas no están en los esquemas de lectura: los históricos incompletos se leen, auditan y reportan tal como están.

## 2. Commits del ciclo (`d785c81..5ab8bd2` + este commit)

- Migración `i4d5e6f7a8b9` (cabeza Alembic): «Desconocida» compartida + `feed_movements.phase_id` — `7ee3327`.
- Backend: `412e234` (RR-27/31/32), `a1c2d53` (RR-28/29), `edb3d04` (RR-30/33/34). Semilla de fase para lotes de prueba `f7524b6`.
- Frontend: `7e18207` (semana/fase de solo lectura, obligatorios), `1bc438f` (selector de tipos activos). **Último commit con código de producción: `1bc438f`.**
- O-20: `90a5fb7`. Docs: `df83d44`, `1f3cb06`. Tests y fixtures: `50a3499`, `1a24120`…`ffaa28b`, `f34a49d` (E2E), `5ab8bd2` (OD01-05).

## 3. Hallazgo durante la certificación

La E2E encontró un defecto real: el formulario de corrección ofrecía tipos **inactivos** (otro proceso desactiva tipos del catálogo); el servidor los rechaza con RR-27 y el usuario veía un rechazo sin causa visible. **FIXED** en `1bc438f` (vitest `uatS2c.correctionType` c) y cubierto en backend por `OD01-05`.

## 4. O-20

- Clasificación: `TEST_DEFECT`.
- Causa raíz: el test comparaba un evento de «hoy − 2 días» con la semana ISO de **hoy**; los lunes y martes el evento cae en la semana anterior y `Δ = 0`. El panel agrega correctamente por semana ISO del evento.
- Corrección (`90a5fb7`): la semana se toma de la fecha del propio evento; casos parametrizados en fronteras de semana y de año. La aserción `Δ == 10` no se relajó.
- Determinismo (`evidence/o20/o20_resultados.txt`, plugin `reloj_controlado`): corregido solo ⇒ PASS; corregido con reloj de tests en domingo 22, lunes 23 y martes 24-11-2026 ⇒ PASS; **versión anterior** con el mismo reloj ⇒ PASS el domingo, **FAIL `Δ=0` lunes y martes** (reproduce el defecto); suite backend completa ⇒ PASS.

## 5. Pruebas

| Suite | Resultado | Evidencia |
|---|---|---|
| Backend completa (HEAD `5ab8bd2`, post-mutación) | **2125 passed, 0 failed, 60 skipped** | `evidence/backend_full_5ab8bd2.log` |
| Frontend vitest completa | **812 passed, 0 failed** (1 skipped preexistente) | `evidence/frontend_vitest_full_5ab8bd2.log` |
| `tsc -b` | RC = 0 | `evidence/frontend_tsc_5ab8bd2.log` |
| `vite build` | OK | `evidence/frontend_build_5ab8bd2.log` |
| Dirigidas OD01..OD07 + T-CAT | 65 passed | `evidence/mutation/results.json` (línea base) |
| E2E completa `--workers=1` (HEAD `f34a49d`; `5ab8bd2` solo añade tests backend) | **239 passed, 0 failed** | `evidence/e2e_full_f34a49d.log` |
| E2E del recorrido de 16 pasos (`proceso-spec020b`) | PASS (incluida en la completa) | idem |
| Mutación (tras el commit de implementación; restauración `git restore --source=<SHA>`) | **22/22 mutantes muertos** (13 backend, 9 frontend); B02 sobrevivió en la primera corrida y se cerró con `OD01-05` | `evidence/mutation/` |

Adaptación de fixtures: ~45 archivos de tests backend y 20 de E2E recibieron los datos que exige el contrato nuevo (causa, lote de vacuna, tipo de alimento, fase, tipo de corrección, contenido de inspección). No se eliminó ni relajó ninguna aserción; la matriz P18B se actualizó al contrato ratificado (casos que antes eran 201 y ahora son 400 por decisión Owner). P18D tenía una comparación por subcadena (`lot_id=2` casaba con `lot_id=29`), corregida a parámetro exacto.

## 6. Compatibilidad histórica

Eventos sin lote de vacuna, causa, tipo de alimento, semana o fase, y correcciones sin tipo, se siguen leyendo (lista, detalle, auditoría, reportes): `OD01-03`, `OD05`, `OD06` e históricos de `OD04/OD07`, E2E `E2E-S2D-08`. Ninguna migración rellena valores (`phase_id` nulable, sin *backfill*; «Desconocida» solo se siembra como catálogo).

## 7. Observaciones abiertas (no bloqueantes)

- `O-26`: la evidencia de una inspección solo se adjunta después del alta; en el alta cuentan detalle u observación.
- `O-27`: un lote sin fase productiva vigente no puede registrar alimento hasta que se registre su fase (RR-34, ratificado). **Para el retest UAT, los lotes de prueba deben tener su fase cargada.**
- `O-23`: asignar por corrección un maestro a un campo que estaba vacío sigue sin soporte (de la sesión anterior).

## 8. Seguridad de la evidencia

Logs saneados (sin DSN, tokens ni contraseñas); escaneo de secretos de `audit/ga-uat-breeder-cria-s2-owner-decisions-2026-11-25/` limpio.

## 9. Decisión local

`OD-S2-01..07 = CLOSED` · `O-20 = CLOSED` · `SESSION2 = CERTIFIED` (local; la paridad de runtime se verifica tras el push a `develop`) · `OWNER_ACCEPTED = NO`.
