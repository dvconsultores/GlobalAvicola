# CERTIFICACIÓN LOCAL — GA-CUTOVER-GRANDPARENT-V3-PREEMPTIVE

Spec `specs/019-cutover-grandparent-v3-preemptive/spec.md` (Discovery Report completo en §1). Baseline `main == develop == 8531d95`.
Implementación `e161d16` en **`develop`** (no se toca `main`, no hay PR ni merge). Código certificado = árbol de `e161d16`; el commit de certificación solo añade documentación y evidencia.

## 1. Hallazgo central
La premisa «Grandparent V2 → V3» está **superada**: Progenitoras ya es `v3` con las cuatro transferencias históricas, la ecuación por sexo, el versionado y el rechazo de V2 desde SPEC 014 (2026-11-07), por contrato compartido con Reproductoras y «a confirmar con el usuario clave».
Los anexos de Abuelas (Desalojo, Traslado a producción, Recepción/Alojamiento) **son esa confirmación**: no hacía falta crear campos ni versión nueva.
```text
TRANSFERS = IMPLEMENTED   (preexistente, ahora verificado y probado para Progenitoras)
```

## 2. Brechas reales cerradas
| ID | Brecha | Resolución |
|---|---|---|
| G1 | Sin pruebas de Progenitoras para apply, fase≠transferencia, conformación, descarte de desalojo, post-corte ni E2E | 20 tests `test_gp_v3_*` + 4 E2E-GP + regresión de Breeder |
| G2 | Transferencias invisibles en el preview y sin etiqueta i18n; reconciliación solo con totales | resaltado del preview de Progenitoras con las 4 transferencias; etiquetas es/en; claves M/H aditivas en la reconciliación (`null` = UNKNOWN) |
| G3 | Textos ambiguos para Abuelas | `birds_placed` = lo **efectivamente** recibido/alojado (no lo planificado); descartes = todo descarte incl. selección y desalojo; fase CRÍA→PROD del mismo lote **no** es transferencia (solo `grandparent`; Reproductoras idéntica carácter por carácter, con guarda) |
| G4 | Sexaje sin criterio | ver §3 |

## 3. Decisiones de dominio
| Tema | Resultado |
|---|---|
| **Sexaje** | `UNRESOLVED` (inclinación a H2 = descarte). El modelo actual no tiene ningún concepto de sexaje. `ABU-ENG-A06 «Error en sexo»`: «registro de cantidad de aves»; su regla de negocio es el texto idéntico al de Descarte (`A05`). Sin campos nuevos. Si es H2, ya cabe en `historical_culls_*` por sexo (prueba: cuadra). Si es H1 (reclasificación M↔H), el contrato **no puede** representarlo: la ecuación marca `CONSISTENCY_MISMATCH` en ambos sexos (prueba diagnóstica; el fallo es **visible**, no silencioso). `OD-GP-SEXAGE-01 = OWNER_DECISION_REQUIRED`, no bloqueante: los saldos de los fixtures cuadran sin sexaje. |
| Peso | `WEIGHT_MODEL = SUFFICIENT`: un promedio al corte; único consumidor = peso inicial de FCR. Peso por sexo = backlog. |
| Huevo histórico | `EGG_HISTORY_MODEL = SUFFICIENT` (producción y envío a incubadora acumulados, `to_hatchery ≤ producción`). Detalle de clasificación = `GP-EGG-HISTORICAL-DETAIL`, backlog / decisión Owner. |
| Capitalización | hito de paso a producción (≥ 24 semanas); sin campo de cutover. Importación: no se reconstruye. |
| Σ salidas vs Σ entradas entre lotes | evaluada y **no** implementada (cargas parciales, origen cerrado, destino no migrado): `GP-XLOT-RECON = BACKLOG`. Solo aserción de prueba. |
| Mortalidad histórica | sigue **opcional** en Progenitoras (obligatoria solo en Reproductoras): vacía ⇒ la ecuación de ese sexo es `NOT_FULLY_VERIFIABLE`, nunca 0 inventado. |

## 4. Fórmula (sin cambio de contrato)
```text
live = birds_placed + transfers_in − mortality − culls − transfers_out     (por sexo; solo con los seis KNOWN)
```
Veredictos `CONSISTENT` / `INCONSISTENT` (error `CONSISTENCY_MISMATCH`) / `NOT_FULLY_VERIFIABLE` (algún UNKNOWN).

## 5. Casos del mandato
GP-V3-T01..T11 ✔ · PHASE-01 ✔ · CONFORMATION-01 ✔ · desalojo (1000 − 50 − 50 − 900 = 0; el validador acepta `live = 0`) ✔ · persistencia por sexo ✔ · post-corte (`current = apertura − post`; lo histórico no se resta de nuevo) ✔ · diagnóstico de sexaje ✔ · UNKNOWN/negativo/decimal ✔ · V2 rechazada ✔.
E2E-GP-01..04 (tres lotes: Cría sin transferencias, origen con salida 40/600, producción con entrada 40/600; suma de vivas 2085 = Σ(placed+in−mort−culls−out)).

## 6. Regresión (código = `e161d16`)
| Gate | Resultado | Evidencia |
|---|---|---|
| Backend completo | **1986 passed, 0 failed, 59 skipped** (40 min) | `evidence/40_backend_full.log` |
| Frontend completo | **753 passed, 1 skipped** (125 archivos) | `evidence/41_frontend_full.log` |
| TSC / Build | PASS / PASS | `42_tsc.log`, `43_build.log` |
| E2E completa `--workers=1` | **227 passed, 0 failed** (17,9 min; incluye `p16-grandparent`, `p16b` Breeder V3, Spec 018/O-15/H4-FOSA y E2E-GP-01..04) | `evidence/44_e2e_full.log`, `e2e_spec019/` |
| Breeder V3 | verde (tests de transferencias de Breeder, `p16b`, y la guarda de textos de Breeder intactos) | idem |
| Sensibilidad | **10/10 detectados**, 0 supervivientes (textos de Progenitoras, guarda de Breeder, nota de fase, resaltado, UNKNOWN→0, claves M/H cruzadas, ecuación sin salidas, ecuación con UNKNOWN→0, etiquetas es/en) | `evidence/50_mutation_campaign.md` |
| Post-mutación | backend 229 passed · frontend 30 passed | `51_`, `52_` |
Escaneo de secretos antes del commit como **puerta** (falla si encuentra JWT/DSN): PASS.

## 7. Observaciones
- **O-17**: el preview de Reproductoras no resalta las transferencias (se ven con «todas las columnas»); fuera de alcance de este mandato, una línea en `PREVIEW_DESTACADAS['breeder']`.
- **O-18**: la tabla de reconciliación de la UI sigue mostrando solo totales de transferencias (las claves M/H están en la API); backlog de UX.
- O-16 (feed parcial en otras BU), O-11, O-12, O-13, O-14 y OPERATIONAL_MODEL_GAP: sin cambios.
- `Imagen de Procesos Documentado/…/.~lock.Formato…Borrador.xlsx#`: bloqueo de LibreOffice de alguien con un anexo abierto; no versionado ni tocado.
- El push a `develop` redespliega UAT de forma automática (Watchtower); **no** hay despliegue de producción, no se cambiaron workflows y `main` no se modifica.
