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

---

# AMENDMENT — OD-GP-SEXAGE-01 = RATIFIED (2026-11-22) · `GA-GRANDPARENT-V3-OD-SEXAGE`

Spec: `specs/019-cutover-grandparent-v3-preemptive/spec.md` §5. Baseline `develop = 8c9bdb3`. Implementación `f7bf1fd` (+ test de cierre en el commit siguiente), en **`develop`**; `main` sin tocar, sin PR.

## A. Decisión
```text
OD-GP-SEXAGE-01 = RATIFIED       SEXAGE_MODEL = HISTORICAL_CULL
```
Un error de sexaje que implica la **salida física del ave** del lote es un **descarte histórico** del sexo con el que estaba contabilizada. No es una reclasificación M↔H. Evidencia: anexos `Control de Producción` y `PES-02`, actividad `ABU-ENG-A06 «Error en sexo»` («registro de cantidad de aves»; regla de negocio idéntica a `ABU-ENG-A05 «Descarte»`; KPI «Descarte de aves y de huevos»).

## B. Qué cambió (y qué no)
| | |
|---|---|
| Fórmula | **sin cambio**; el sexaje no añade término |
| Campos | **ninguno** añadido ni quitado; sin `historical_sex_correction_*` ni `sexage_error_*` |
| Plantilla | `v3` / `CUTOVER_GRANDPARENT_V3`; **columnas sin cambio** (30 = 30); **instrucción sí cambió** (solo `grandparent`, `historical_culls_*`) |
| Código de aplicación | `APPLICATION_CODE_CHANGE_REQUIRED = NO` para la **lógica**: validación, preview, apply, reconciliación y UNKNOWN ya trataban los descartes por sexo. Solo cambia **un string por sexo** en `contracts.py` (la instrucción), para que la decisión llegue al usuario que rellena la plantilla |
| Reproductoras | intacta (texto idéntico carácter por carácter; con guarda) |

Definición final de `historical_culls_*` (Progenitoras): todo descarte acumulado antes del corte que redujo **físicamente** la población: cría y levante, selección, desalojo, antes de conformar producción **y aves retiradas por error de sexaje**; se registra en el sexo con el que estaba contabilizada y no como cambio de sexo ni como transferencia; un ave no es a la vez descarte y transferencia.

## C. Pruebas (SEXAGE-01..05) y protección de la decisión
| ID | Caso | Resultado |
|---|---|---|
| SEXAGE-01 | machos: placed 100, mortalidad 5, culls 10 (pueden ser error de sexaje), live 85 | PASS · CONSISTENT |
| SEXAGE-02 | hembras equivalente | PASS · CONSISTENT |
| SEXAGE-03 | `historical_culls_males` UNKNOWN | PASS · `NOT_FULLY_VERIFIABLE`, `null`/UNKNOWN en preview y reconciliación (nunca un 0 conocido) |
| SEXAGE-04 | 100 M / 1000 H, 10 aves de sexaje **sin** contar como cull | PASS · `CONSISTENCY_MISMATCH` (el sistema no corrige sexo en silencio) |
| SEXAGE-05 | culls 50 (20 cría + 10 sexaje + 20 selección/desalojo) y salida 900: `1000 − 50 − 50 − 900 = 0` | PASS · sin doble conteo, sin métrica separada |
Además: el diagnóstico previo (reclasificación M→H marca inconsistencia; descarte cuadra) pasa a documentar la decisión ratificada.

## D. Regresión
| Gate | Resultado | Evidencia |
|---|---|---|
| Cutover backend (Progenitoras, transferencias, contratos, validación, apply, red, continuidad, Incubadora V4/OD/O-15, GA-REQ-061 c1–c7, pines Alembic, QA dataset, guarda de fechas) | **315 passed, 0 failed** | `evidence/62_backend_cutover_full.log` |
| Frontend cutover | 30 passed | `evidence/63_frontend_cutover.log` |
| E2E `p16-grandparent` + `p16b` **Breeder V3** + `spec019` | **6 passed, 0 failed** | `evidence/64_e2e_grandparent_breeder.log` |
| Plantilla regenerada | 30 columnas idénticas a `HEAD`, Meta v3/`CUTOVER_GRANDPARENT_V3`, instrucción nueva | `evidence/60_sexage_template_inspection.txt` |
| Derivados | solo `03_GRANDPARENT` y `07_DATA_LINEAGE` cambian; `04_BREEDER` idéntico | `audit/cutover-initial-balances/` |
No se repitió la regresión completa (backend 1986 / frontend 753 / E2E 227 del certificado anterior): el cambio es un texto de contrato y pruebas, sin lógica; las pruebas afectadas más sus vecinas se reejecutaron.

## E. Sensibilidad
| Mutante | Resultado |
|---|---|
| M1 quitar la mención en la enumeración de descartes | **SOBREVIVIÓ** (el test solo exigía la palabra «sexaje», que seguía en otra frase) → **cerrado** con tres aserciones independientes (`aves retiradas por error de sexaje`, `es un descarte`, `NO como cambio de sexo`); M1a/M1b/M1c ahora **detectados** (3/3) |
| M2 texto de Progenitoras aplicado también a Reproductoras | detectado (guarda de Breeder) |
| M3 descartes UNKNOWN tratados como 0 en la ecuación | detectado (T09 y SEXAGE-03) |
Evidencia: `evidence/65_sexage_mutation.md`, `66_sexage_text_mutation.log`.

## F. Observación nueva
- **O-19 (preexistente, SPEC 006/014):** los descartes y la mortalidad históricos desconocidos se **almacenan** como `0` con el estado `*_status = UNKNOWN` (solo las cuatro transferencias usan columnas NULL). Las capas de lectura (preview, reconciliación, informes del cutover) respetan el estado y publican `null`; pero cualquier consumidor que lea la columna sin su estado vería `0`. No se cambia aquí (requeriría migración); riesgo latente respecto de la doctrina `UNKNOWN != 0`.
- O-17, O-18, O-16, O-11, O-12, O-13, O-14 y OPERATIONAL_MODEL_GAP: sin cambios.

## G. Decisión final
```text
OD-GP-SEXAGE-01 = CLOSED
GRANDPARENT_V3 = CERTIFIED
TRANSFERS = IMPLEMENTED
SEXAGE = CLOSED            SEXAGE_MODEL = HISTORICAL_CULL
WEIGHT_MODEL = SUFFICIENT
EGG_HISTORY_MODEL = SUFFICIENT
DEVELOP_READY_FOR_PR = YES
OWNER_UAT_READY = YES
OWNER_ACCEPTED = NO
```
