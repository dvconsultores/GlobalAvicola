# CERTIFICACIÓN LOCAL — GA-CUTOVER-HATCHERY-V4-NON-INCUBABLES-PIT

Spec `specs/018-cutover-hatchery-v4-non-incubables/spec.md` (Discovery/Domain report + D-1..D-11 + AC-V4-01..14).
Baseline `main == develop == bb91338`. Implementación `2f772eb` (backend) + `0d7b0cc` (frontend, docs/plantillas, E2E). Cabeza Alembic: `g2b3c4d5e6f7` → `h3c4d5e6f7a8`.
El código certificado es el árbol de `0d7b0cc`; el commit de certificación solo añade documentación y evidencia.

## 1. Contrato V4
- `template_version=v4`, `schema_id=CUTOVER_HATCHERY_V4`, `cutover_template_hatchery_v4.xlsx`, 23 columnas (orden D-7), sin `eggs_discarded` como entrada.
- Nuevos: `eggs_non_incubable_oversized|dirty|broken`, `fertile_eggs_to_pit` (enteros ≥ 0, métricas opcionales: vacío = UNKNOWN, 0 = cero conocido, sin N/A).
- V3 nueva → `TEMPLATE_VERSION_UNSUPPORTED` indicando v4 (regla «versión ≠ vigente»); columna `eggs_discarded` en un archivo V4 → `HEADER_UNKNOWN`; faltante de un campo nuevo → `HEADER_MISSING`.

## 2. Hallazgo de dominio (clave)
En el código V3, `eggs_discarded` era el descarte **posterior a la carga** (resta de `eggs_set`: `eggs_in_process = set − transferred − discarded`), pero los 4 procesos entregados lo usaban como `received − set` (pre-carga). Los no incubables V4 son una **clasificación del huevo recibido que nunca entró en `eggs_set`**, y `received − set` incluye además huevo aún por cargar (saldo de BR-03). Por eso:
- `eggs_discarded` **no se deriva** del total (habría doble conteo en `eggs_in_process`); en V4 queda NULL + `NOT_APPLICABLE`; la columna se conserva para la V3 histórica.
- No se impone igualdad `received = set + no incubables`; solo `set + Σ(KNOWN) ≤ received` (aunque falte un componente).
- BR-03 resta los no incubables KNOWN **una sola vez** (`received − set − Σ`); un UNKNOWN no se resta ni se inventa.
- `fertile_eggs_to_pit`: solo `≤ received`; su posición en el balance es **OD-HATCH-V4-01 (OWNER_DOMAIN_DECISION_REQUIRED)**: `eggs_in_process` V4 se calcula solo con fosa KNOWN = 0; con fosa > 0 o UNKNOWN queda sin calcular.

## 3. Pipeline y persistencia
Mismo recorrido (parse → staging → validación → preview → aprobación → apply → reconciliación), XLSX y CSV. Migración aditiva y reversible: 4 columnas + 4 `*_status` (`NOT NULL`, `server_default 'UNKNOWN'`), sin backfill: los registros históricos quedan con el desglose UNKNOWN.
UI: reconciliación con «Total no incubables (derivado)», desglose, fosa y, solo si hay descartados KNOWN, «Huevos descartados (histórico V3)».

## 4. Regresión (código = `0d7b0cc`)
| Gate | Resultado | Evidencia |
|---|---|---|
| Backend completo | **1947 passed, 0 failed, 59 skipped** | `evidence/40_backend_full.log` |
| Backend dirigido V4 (dedicado) | 41 passed | `evidence/11_v4_dedicated_tests.log` |
| Frontend completo | **740 passed, 1 skipped** (124 archivos) | `evidence/41_frontend_full.log` |
| TSC / Build | PASS / PASS | `evidence/42_tsc.log`, `43_build.log` |
| E2E hatchery (P16 + E2E-V4-01..06) | 7 passed | `evidence/30_e2e_hatchery_v4.log`, `e2e_spec018/` |
| E2E completa `--workers=1` | corrida 1: 212 passed / 1 failed (P17e, Usuarios/Roles); corrida 2: **213 passed / 0 failed** | `evidence/44a_...`, `44_e2e_full.log`, `45_e2e_p17e_alone.log` (P17e aislado: pasa) |
| Sensibilidad | **20/20 detectados**, 0 supervivientes | `evidence/50_mutation_campaign.md` |
| Post-mutación | backend 299 passed · frontend 38 passed + 1 skipped | `evidence/51_`, `52_` |

## 5. Observaciones (no bloqueantes)
- **O-13** Ambigüedad V3 de `eggs_discarded` (contrato vs datos entregados): histórico intacto; no se reinterpreta ni se redistribuye.
- **OD-HATCH-V4-01** posición de la fosa en el balance: pendiente de decisión de la Owner (ver §2).
- **OPERATIONAL_MODEL_GAP**: la operación normal ya tiene `egg_type` `dirty`/`broken`, pero no `oversized` ni evento de fosa; no se amplió.
- **O-14** P17e (Usuarios/Roles S2-01) falló una vez en la E2E completa (selector de rol sin la opción); pasa aislado y en la repetición. Ajeno a esta spec; vigilar.
- `egg_origin` se persiste pero no se expone en la proyección de reconciliación (preexistente).
- Las aperturas ya aplicadas con V3 (p. ej. dataset QA-DEMO-V1) no se mutan.
- O-11 y O-12 (ciclo anterior) siguen abiertas.
