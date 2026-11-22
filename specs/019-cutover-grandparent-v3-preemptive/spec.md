# SPEC 019 — Cargas Iniciales · Progenitoras V3: auditoría preventiva (Abuelas)

Mandato `GA-CUTOVER-GRANDPARENT-V3-PREEMPTIVE` (2026-11-22). Amendment de SPEC 014 (transferencias históricas) y SPEC 006/009. Baseline `main == develop == 8531d95`.
Alcance: anticiparse a la UAT de Yolinel sobre Progenitoras con la evidencia funcional de los ocho anexos de Abuelas. **No** promueve a `main`, no crea PR, no despliega.

## 1. PROGENITORAS V3 — DISCOVERY REPORT

### 1.1 Current Grandparent (contrato real)
- **Ya es V3.** `contracts.py`: `AVES_TEMPLATE_VERSION = "v3"`; `grandparent → CUTOVER_GRANDPARENT_V3`; archivo `cutover_template_grandparent_v3.xlsx`. SPEC 014 (2026-11-07) lo subió de v2 a v3 **por contrato compartido con Reproductoras**
  y dejó escrito «a confirmar con el usuario clave». La premisa «V2 → V3» del mandato está **superada**: no hay que crear versión ni campos.
- Campos (resumen; comparten `_metricas_reproductoras(bu)` con `breeder`): `live_males|females` (obligatorios), `birds_placed_males|females`, `historical_mortality_males|females` (**opcionales en grandparent**, obligatorios solo en breeder, SPEC 009),
  `historical_culls_males|females`, **`historical_transfers_in_males|females`, `historical_transfers_out_males|females`**, `accumulated_feed_kg`, `current_avg_weight_g`, `accumulated_egg_production`, `accumulated_eggs_to_hatchery`.
- Ecuación (por sexo, solo con los seis componentes KNOWN): `vivas = alojadas + entradas − mortalidad − descartes − salidas` → `CONSISTENT` / `INCONSISTENT` (`CONSISTENCY_MISMATCH`) / `NOT_FULLY_VERIFIABLE` (algún UNKNOWN). Persistencia: `opening_balances.accumulated_transfers_in|out_male|female` (NULL = UNKNOWN) + estados. Sin migración pendiente.
- Parser: una carga V2 de grandparent se rechaza (`TEMPLATE_VERSION_UNSUPPORTED`; ya probado por SPEC 014 `BR-T12`).

### 1.2 Evidencia funcional de los ocho anexos (`Imagen de Procesos Documentado/PESADAS/Abuelas/`)
Mapeo: `Recepción de Abuelas` ≈ `PES-01` (importación, recepción, alojamiento) · `Control de Producción` ≈ `PES-02` (cría/levante) · `Desalojo` ≈ `PES-03` · `Recepción producción abuelas` (traslado + alojamiento en producción) · `control de producion HF` (producción de huevo fértil).
| Proceso | Hallazgo (hoja/actividad) | Qué exige a nuestro modelo |
|---|---|---|
| Importación (`ABU-GDP-A01`) | Planificación anual de importación; razas, lote, trazabilidad. | **No** es población. No se reconstruye; `birds_placed` ≠ cantidad planificada. |
| Recepción (`ABU-GDP-A02`) | Cantidad **realmente recibida**; lote nuevo con trazabilidad del lote de origen; línea materna/paterna sexada previamente. | `birds_placed_*` = lo realmente recibido/alojado. |
| Alojamiento (`ABU-GDP-A03`) | Conteo y sexaje de pollitos por línea hembra/macho; pollitos por galpón; «lote aperturado». | Población original por sexo (`birds_placed_*`). |
| Cría/levante (control de producción y `PES-02`: `ABU-ENG-A01..A07`) | Alimento, **mortalidad** (tolerancia 0,3 %), **peso semanal** (muestra 10–15 %, gramos), **descarte**, **error en sexo**, **capitalización** (≥ 24 semanas). | Mortalidad y descarte acumulados; peso promedio; capitalización = hito. |
| **Desalojo** (`ABU-ENG-A01..A05`) | Lote origen → lote destino; cantidad hembras, machos y **descarte**; granja/galpón origen; fecha; selección de aves; peso final; **conformación del lote**. | Movimiento de población **entre lotes** + descarte en la selección. |
| **Traslado a producción** (`Recepción producción abuelas`, `ABU-GDP-A01`) | Lote origen/destino, granja y galpón origen/destino, cantidad de aves, raza, edad; luego alojamiento en producción. | Transferencia entre lotes (salida del origen, entrada al destino). |
| Producción HF (`control de producion HF`: `ABU-ENG-A01..A06`; **no** incluye «error en sexo») | Inventario diario, clasificación de huevo por incubabilidad, solo se envía huevo incubable, todos los descartes de huevo. | Detalle de huevo = analítica; ver §1.7. |

**Conclusión de dominio:** Progenitoras tiene movimientos reales de población entre lotes (selección, descarte, traslado, conformación). El modelo `placed − mortalidad − descartes = vivas` sería incompleto; **el contrato actual ya lo cubre** con las cuatro transferencias.

### 1.3 Reutilización de Reproductoras V3
| Componente | Breeder V3 | Grandparent actual | Reutilizable |
|---|---|---|---|
| campos de plantilla | 4 transferencias + placed + culls | **idénticos** (`_metricas_reproductoras`) | sí, ya reutilizado |
| parser / validador / ecuación | `_consistencia_reproductoras` | mismo | sí |
| columnas DB | `opening_balances.accumulated_transfers_*` | mismas | sí (sin migración) |
| preview / reconciliación | totales en/out | mismos | sí |
| tests específicos | 27 en `historical_transfers_red`, apply, E2E `p16b` | solo plantilla + rechazo V2; **0 de apply, 0 de E2E** | **brecha de cobertura** |
Diferencia que se conserva: mortalidad histórica **opcional** en Progenitoras (obligatoria solo en Reproductoras).

### 1.4 Transfers
Required: **YES** (demostrado por Desalojo/Traslado) · **ya implementado** por SPEC 014 → `TRANSFERS = IMPLEMENTED`. Sin campos nuevos, sin versión nueva.

### 1.5 Fase ≠ Transferencia
`productive_phase_code` + `phase_start_date` describen la fase **del mismo lote**. CRÍA→PROD del mismo lote **no** genera transferencia (ni entrada ni salida). Solo hay transferencia cuando la población pasa de un lote a otro (traslado/conformación).
El contrato no lo dice con claridad hoy → texto explícito y prueba (`GP-V3-PHASE-01`).

### 1.6 Semántica de `birds_placed` y descartes
- `birds_placed_*`: aves **efectivamente recibidas y alojadas** al abrir el lote (conteo real tras recepción y sexaje), **no** la cantidad planificada/solicitada en la importación, y sin sumarle transferencias.
- `historical_culls_*`: **todo** descarte acumulado hasta el corte que redujo la población del lote: cría/levante, **selección y desalojo**, antes de conformar producción. Un mismo ave no se registra a la vez como descarte y como transferencia.
- Se refinan los textos **solo en `grandparent`** (sin cambio estructural → la plantilla sigue en v3; Reproductoras no cambia).

### 1.7 Sexaje
| Hipótesis | Evidencia |
|---|---|
| H1 reclasificación M↔H | Ningún anexo la describe. |
| **H2 descarte** | `ABU-ENG-A06 «Error en sexo»` (control de producción y `PES-02`): *«Registro de la cantidad de aves»*, regla de negocio: *«De 18 a 20 semanas el descarte se vuelve comercial. Todo descarte se vende a la misma empresa»* (texto idéntico a `ABU-ENG-A05 «Descarte»`); KPI «Descarte de aves y de huevos». |
| H3 otro | — |
**Clasificación (histórica, SUPERADA por el amendment §5): `UNRESOLVED` (con inclinación a H2).** El modelo actual **no tiene ningún concepto de sexaje** (0 coincidencias en app/seeds/docs/specs). La regla de A06 parece copiada de A05, así que no basta para afirmar H2 sin el usuario clave.
Consecuencias: **no se agregan campos** de corrección de sexo. Si fuera H2, ya queda cubierto por `historical_culls_*` (por sexo). Si fuera H1, el contrato **no puede** representarlo (la ecuación marcaría `INCONSISTENT`):
se deja una prueba diagnóstica que lo demuestra y la decisión **`OD-GP-SEXAGE-01 = OWNER_DECISION_REQUIRED`**, no bloqueante para las transferencias.

### 1.8 Peso
Un único `current_avg_weight_g` al corte; su único consumidor es el peso inicial de FCR. Los anexos pesan por lote del mismo sexo, y la operación normal ya admite `sex` por movimiento, pero el opening balance no necesita M/H separado.
**`WEIGHT_MODEL = SUFFICIENT`** para cutover. Peso por sexo = backlog `GP-WEIGHT-BY-SEX` (decisión Owner si se quiere).

### 1.9 Detalle histórico de huevo
`accumulated_egg_production` y `accumulated_eggs_to_hatchery` (con `to_hatchery ≤ producción`) son suficientes para el saldo inicial; la clasificación (incubable/sucio/roto/descartes) es analítica histórica.
**`EGG_HISTORY_MODEL = SUFFICIENT`**; detalle = `GP-EGG-HISTORICAL-DETAIL = BACKLOG / OWNER_DECISION_REQUIRED` (fuera de V3).

### 1.10 Capitalización e importación
Capitalización (≥ 24 semanas) es un **hito/estado** de paso a producción; no cambia la población ni exige campo de cutover. Importación no se reconstruye (no hay OC ni eventos ficticios).

### 1.11 Migración
**NO.** Se reutilizan columnas y estados de SPEC 014.

### 1.12 Brechas reales encontradas
| ID | Brecha | Dónde |
|---|---|---|
| G1 | Sin pruebas específicas de Progenitoras para transferencias (apply, fase≠transferencia, conformación, descarte en desalojo, post-corte) ni E2E. | tests |
| G2 | Las transferencias **no se ven** en el preview (no están en el resaltado) y sus columnas no tienen etiqueta i18n (aparece el nombre técnico); la reconciliación solo expone totales, no M/H. | backend preview + frontend |
| G3 | Textos del contrato ambiguos para Abuelas (`birds_placed`, descartes de desalojo, fase vs transferencia). | contrato + manual |
| G4 | Sexaje sin criterio documentado. | spec |

### 1.13 Decisiones
- **D-1** Sin campos nuevos ni versión nueva (`TRANSFERS = IMPLEMENTED`).
- **D-2** Textos de contrato refinados **solo para grandparent**: `birds_placed_*`, `historical_culls_*`, `historical_transfers_*` y `productive_phase_code`/fase (fase ≠ transferencia). Sin cambio estructural.
- **D-3** Visibilidad: el resaltado del preview de grandparent incluye las cuatro transferencias; etiquetas i18n es/en de las cuatro; la reconciliación añade claves **aditivas** por sexo (`historical_transfers_in_males|females`, `..._out_...`; `null` = UNKNOWN) manteniendo los totales. Sin cambios de tabla UI de reconciliación (backlog).
- **D-4** Sexaje: sin campos; prueba diagnóstica; `OD-GP-SEXAGE-01` abierta → **RATIFICADA como `HISTORICAL_CULL` (amendment §5)**.
- **D-5** Reconciliación cruzada `Σ salidas` vs `Σ entradas` entre lotes: **evaluada y NO implementada** (cargas parciales, origen cerrado, destino no migrado); `GP-XLOT-RECON = BACKLOG`.
- **D-6** Reproductoras: sin cambios de contrato ni de texto; las claves aditivas de reconciliación son infraestructura compartida y deben dejar Breeder V3 verde.

### 1.14 AUTHORIZATION_GATE
**PASS** para el alcance anterior (cobertura, visibilidad, semántica, documentación, E2E). La parte «crear V3 con cuatro campos» **no aplica** (ya existe). Sexaje queda como decisión Owner no bloqueante.

## 2. ACs
| AC | Enunciado |
|---|---|
| AC-GP-01 | Contrato grandparent v3: 4 transferencias presentes con los nombres canónicos de Breeder V3; textos refinados (birds_placed real, descartes incl. selección/desalojo, fase ≠ transferencia); Reproductoras con textos **intactos**. |
| AC-GP-02 | `GP-V3-T01..T11` (sin transferencias = V2; salida/entrada M/H; simultáneas; conformación; inconsistente = DENY; UNKNOWN no se inventa; negativo y decimal = DENY) en Progenitoras. |
| AC-GP-03 | `GP-V3-PHASE-01`: mismo lote CRÍA→PROD sin transferencias (0 conocido), sin doble conteo. |
| AC-GP-04 | `GP-V3-CONFORMATION-01`: lotes origen con salida + lote destino con entrada; `birds_placed`, mortalidad y descartes sin alterar; Σ salidas = Σ entradas **solo como aserción de prueba**. |
| AC-GP-05 | Descarte en desalojo: `placed 1000, mort 50, culls 20+30, out 900 → live 0` consistente sin doble conteo. |
| AC-GP-06 | Persistencia por sexo en `opening_balances` y estados; UNKNOWN = NULL. |
| AC-GP-07 | Evento posterior al corte: `current = apertura + post-corte`; lo histórico no se descuenta otra vez. |
| AC-GP-08 | Diagnóstico de sexaje: descarte por sexo cuadra; reclasificación M↔H marca `INCONSISTENT` (el contrato no la representa). |
| AC-GP-09 | Preview de grandparent muestra las 4 transferencias con etiqueta propia y UNKNOWN visible; reconciliación expone claves M/H aditivas. |
| AC-GP-10 | E2E Grandparent V3 (24 pasos del mandato) con tres lotes (Cría sin transferencias, origen con salida, producción con entrada), evento post-corte, refresh y relogin. |
| AC-GP-11 | Breeder V3 permanece verde (tests y E2E `p16b`). |

## 3. Tareas
T1 backend (contrato grandparent, preview highlight, claves de reconciliación) + tests GP-V3 · T2 frontend (etiquetas, preview) + vitest · T3 E2E Progenitoras V3 · T4 docs (manual + plantillas/matrices regeneradas) · T5 sensibilidad · T6 regresión completa + certificación.

## 4. Estado
Ver `audit/ga-cutover-grandparent-v3/CERTIFICATION.md`.

**Estado (2026-11-22):** implementación `e161d16` en `develop`. Backend 1986/0/59 · frontend 753 · E2E 227/0 · mutación 10/10. `TRANSFERS = IMPLEMENTED` (SPEC 014), `SEXAGE = OWNER_DECISION_REQUIRED` (OD-GP-SEXAGE-01), `WEIGHT_MODEL = SUFFICIENT`, `EGG_HISTORY_MODEL = SUFFICIENT`. Ver `audit/ga-cutover-grandparent-v3/CERTIFICATION.md`.

## 5. AMENDMENT — OD-GP-SEXAGE-01 = RATIFIED (2026-11-22)

Mandato `GA-GRANDPARENT-V3-OD-SEXAGE`. Cierra la única decisión de dominio pendiente de este ciclo. **No** reabre Grandparent V3: sin campos, sin versión nueva, sin migración, sin cambio de fórmula, Reproductoras intacta.

```text
Status:   RATIFIED
Decision: HISTORICAL_CULL
Owner date: 2026-11-22
SEXAGE_MODEL = HISTORICAL_CULL
```
**Decisión Owner.** En Progenitoras, un «error de sexaje» que implica la **salida del ave del lote** es un **descarte**. No es una reclasificación macho↔hembra dentro de la población activa. Se acumula en `historical_culls_males` o `historical_culls_females` según el sexo **bajo el cual estaba contabilizada** el ave antes de retirarla.

**Razonamiento de dominio.** Los anexos de Abuelas (`Control de Producción` y `PES-02`, hoja `ABU-ENG-A06 «Error en sexo»`) lo describen como *«registro de la cantidad de aves»* y su regla de negocio es el mismo texto de `ABU-ENG-A05 «Descarte»`
(*«De 18 a 20 semanas el descarte se vuelve comercial; todo descarte se vende a la misma empresa»*); el KPI asociado es «Descarte de aves y de huevos». Ningún anexo describe un cambio de sexo de un ave que permanece en el lote.
La hipótesis H1 (reclasificación) queda **descartada**; H2 (descarte) **ratificada**.

**Consecuencias de contrato (sin lógica nueva).**
- La ecuación certificada **no cambia** y el sexaje no añade ningún término: `live = placed + in − mortality − culls − out` (por sexo, solo con los seis KNOWN).
- **Sin campos** `historical_sex_correction_*` ni `sexage_error_*`.
- `historical_culls_*` (Progenitoras) = **todo** descarte acumulado antes del corte que redujo físicamente la población del lote: cría/levante, selección, desalojo, antes de conformar producción **y aves retiradas por error de sexaje**. Texto de la plantilla ampliado **solo en `grandparent`** (cambio de texto, no de columnas ni de schema; sigue `CUTOVER_GRANDPARENT_V3`).
- **UNKNOWN:** si no se conoce el acumulado de descartes (incluido el de sexaje), la celda va vacía: no se inventa 0 y el balance de ese sexo queda `NOT_FULLY_VERIFIABLE`.
- **Sin doble conteo:** un ave retirada por error de sexaje es **un descarte**, no «descarte + transferencia» (salvo que hayan ocurrido dos hechos distintos). Descartes → `historical_culls_*`; aves enviadas a otro lote → `historical_transfers_out_*`; aves recibidas → `historical_transfers_in_*`.
- Fase ≠ transferencia (sin cambio). Reconciliación entre lotes (sin cambio).
- **Una reclasificación silenciosa sigue sin ser posible:** si alguien carga vivas M/H «corregidas» sin descartes, la ecuación marca `CONSISTENCY_MISMATCH` (el sistema no corrige sexo).

**Verificación de código (§11 del mandato).** `historical_culls_*` participan en validación (ecuación), preview, apply (`accumulated_culls_male|female`), reconciliación (lifetime) y UNKNOWN (estado `culls_status`). **`APPLICATION_CODE_CHANGE_REQUIRED = NO`** para la lógica; solo se amplía el **texto** de instrucción del contrato de Progenitoras.

| AC | Enunciado |
|---|---|
| AC-SX-01 | SEXAGE-01: machos `placed 100, mortalidad 5, culls 10 (pueden ser error de sexaje), transfers 0 → live 85` válido y consistente. |
| AC-SX-02 | SEXAGE-02: hembras equivalente. |
| AC-SX-03 | SEXAGE-03: `historical_culls_males` UNKNOWN → sin error, `NOT_FULLY_VERIFIABLE`, NULL/UNKNOWN tras apply; nunca 0. |
| AC-SX-04 | SEXAGE-04: `100 M / 1000 H` con 10 aves «de sexaje» **sin** contarlas como cull (vivas M 90) → `CONSISTENCY_MISMATCH` (no hay corrección silenciosa de sexo). |
| AC-SX-05 | SEXAGE-05: `culls > 0` y `transfers_out > 0` en el mismo lote cuadran sin doble conteo (`1000 − 50 − (20+10+20) − 900 = 0`). |
| AC-SX-06 | El texto de instrucción de `historical_culls_*` de Progenitoras menciona el error de sexaje; el de Reproductoras queda idéntico (guarda). Plantilla `CUTOVER_GRANDPARENT_V3`, mismas columnas. |
