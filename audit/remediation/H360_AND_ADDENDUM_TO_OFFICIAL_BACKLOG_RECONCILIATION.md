# RECONCILIACIÓN H360 + H360A → BACKLOG OFICIAL

**WAVE A0-G** · 2026-09-09 · base `5d2e355` · **0 hallazgos sin disposición**

Regla: cada hallazgo se traza a su requisito raíz y a su causa raíz; si un `R-`, `GA-REM-`,
`P-`, `RC-`, `BU-D` u `OD` existente tiene la **misma causa raíz**, se **mapea** (`MAP`) y no se
crea nada; si es genuinamente nuevo recibe el **siguiente ID oficial** (`R-130`…; el último era
`R-129`). Todo ID nuevo conserva `source_finding`. Hallazgos con la misma causa raíz y la misma
unidad de trabajo se agrupan en un solo `R-`; los que solo comparten requisito, no.

Olas: `A` autoridad/seguridad/datos · `B` procesos faltantes · `C` KPI/trazabilidad · `D`
preparación SAP · `E` frontend/UX · `F` certificación · `G` SAP real.

| Hallazgo origen | Título | Sev. | Requisito raíz | ID existente | ID nuevo | ¿Dup.? | Disposición | Ola | ¿Spec? | ¿OD? | Estado |
|---|---|:--:|---|---|---|:--:|---|:--:|---|---|---|
| `H360-P01` | descarte y salida sin validar contra el saldo | P1 | `BR-01` · invariante de población | — | **`R-130`** | no | NUEVO | B | enm. `GA-REM-005` | no | abierto |
| `H360-K01` | «FCR» = alimento/1000 (propaga a índice de producción e IPE) | P1 | `Bases` p.2/p.13 | — | **`R-131`** | no | NUEVO | C | enm. `GA-REM-022` | no | abierto |
| `H360-K07` | índice de producción hereda FCR; edad con `date.today()` en lotes cerrados | P2 | `Bases` p.13 | — | `R-131` | causa compartida | AGRUPADO | C | ídem | no | abierto |
| `H360-K02` | % mortalidad = 0 sin `OpeningBalance` | P1 | `Bases` p.3 | — | **`R-132`** | no | NUEVO | C | enm. `GA-REM-022` | `AOD-10.e` (base) | abierto |
| `H360-K13` | tendencia de mortalidad sin filtro de estado; sin % contra población actual | P2 | Rec. §9 | — | `R-132` | misma base de cálculo | AGRUPADO | C | ídem | `AOD-10.e` | abierto |
| `H360-K03` | eficiencia de vacunación cuenta eventos | P1 | `Bases` p.10 | — | **`R-133`** | no | NUEVO | C | enm. `GA-REM-022` | no | abierto |
| `H360-K06` | AFCR suma aves como gramos | P1 | `Bases` p.13 | — | **`R-134`** | no | NUEVO | C | enm. `GA-REM-022` | no | abierto |
| `H360-P03` | `RETURNED` sin reenvío · `REJECTED` terminal | P1 | `docs/12 §4` fila 8 | — | **`R-135`** | no | NUEVO | B | nueva spec o enm. `GA-REM-006` + `spec §4.10` | **`OD-17`** ✓ | abierto |
| `H360-D09` | conflicto `docs/12` vs código sobre `REJECTED` | — | ídem | — | `R-135` | mismo | RESUELTO por `OD-17` | B | — | `OD-17` | resuelto |
| `H360-P05` | `reversals` sin servicio ni ruta; `BR-16` sin mecanismo | P1 (SAP) | `BR-16` · Rec. §24 · docs/16 G-R09 | — | **`R-136`** | no | NUEVO | B (modelo) · D (SAP) | nueva spec | no | abierto |
| `H360-S05` | `lots` sin identificador SAP | P1 (D) | Rec. §3.3, §25.3 | — | **`R-137`** | no | NUEVO | D | enm. `GA-REM-017` | **`AOD-03`** requerida | bloqueado por decisión |
| `H360-S01` | materiales locales sin clave SAP | P1 (D) | Rec. §5, §15 | — | **`R-138`** | no | NUEVO | D | enm. `GA-REM-017` | no | abierto |
| `H360-S02` | sin material por raza/sexo/huevo/pollito | P1 (D) | Rec. §5 | — | `R-138` | misma causa | AGRUPADO | D | ídem | `AOD-01` parcial | abierto |
| `H360-S03` | proveedor por dos vías (`suppliers.sap_code` y `sap_references.VENDOR`) | P2 | Rec. §15 | — | `R-138` | misma causa | AGRUPADO | D | ídem | no | abierto |
| `H360-A01` = `H360A-08` | 8 atajos `is_super_admin` no conformes con `OD-14.c/d` | **P1** | `OD-14.c/d` | — | **`R-139`** | no | NUEVO · **verificado** (`A01_SUPER_ADMIN_SHORTCUT_VERIFICATION.md`) | **A** (tanda propia) | enm. `GA-REM-002` (clase C) o `GA-REM-040` | no | abierto |
| `H360-P04` | `cancel` sin motivo ni rol; no bloquea `SAP_CONFIRMED`/`SAP_ERROR` | P2 | `docs/12 §4` fila 13 · Rec. §2 | — | **`R-140`** | no | NUEVO | B | enm. `GA-REM-006` | no | abierto |
| `H360-K04` | hen-day × 30 fijo | P2 | `spec §4.12` | — | **`R-141`** | no | NUEVO (grupo KPI 2.º orden) | C | enm. `GA-REM-022` | `AOD-10.b` | abierto |
| `H360-K05` | índice de bienestar heurístico | P2 | `Bases` p.3 | — | `R-141` | grupo | AGRUPADO | C | ídem | `AOD-10.c` | abierto |
| `H360-K11` | % pollitos sanos con denominador «cargados» | P2 | `Bases` p.10 | — | `R-141` | grupo | AGRUPADO | C | ídem | no | abierto |
| `H360-K08` | ganancia diaria aproximada (peso inicial 0) | P3 | `Bases` p.2 | — | `R-141` | grupo | AGRUPADO | C | ídem | no | abierto |
| `H360-K10` | 12 KPI del cliente sin productor | P2 | `Bases` (26 KPI) | `GA-REM-022` | — | sí | **MAP** → `GA-REM-022` (alcance base «completitud de KPI») | C | ya existe | `AOD-10.a` (fertilidad) | abierto |
| `H360-D10` | dos denominadores de fertilidad en la fuente | — | `Bases` p.5/p.8 | `AOD-10` | — | sí | **MAP** → `AOD-10.a` | C | — | pendiente | pendiente |
| `H360-P06` | `CORRECTED` usado como «pendiente de aprobador» | P2 | `docs/12 §4` fila 6 | — | **`R-142`** | no | NUEVO | B | enm. `GA-REM-006` | no | abierto |
| `H360-P10` | `docs/12 R2` (corrector ≠ aprobador) no implementada | P2 | `docs/12 §6 R2` | — | **`R-143`** | no | NUEVO | B | enm. `GA-REM-007` | no | abierto |
| `H360-P08` | resumen de cierre sin FCR ni peso final | P2 | `BR-05` · Rec. §13 | — | **`R-144`** | no | NUEVO | B/C | enm. `GA-REM-029` | `AOD-08` (semántica) | abierto |
| `H360-S07` | backoff fijo 1 min (docs/10: 1/5/15) | P2 | `docs/10 §6.2` | — | **`R-145`** | no | NUEVO (grupo preparación SAP) | D | enm. `GA-REM-010` | no | abierto |
| `H360-D11` | conflicto docs/10 vs código (backoff) | — | ídem | — | `R-145` | mismo | AGRUPADO (resuelto por evidencia: manda docs/10) | D | — | no | abierto |
| `H360-S10` | consolidación sin validación de integridad (`docs/12 §10.3`) | P2 | `docs/12 §10` | — | `R-145` | grupo | AGRUPADO | D | ídem | no | abierto |
| `H360-S11` | outbox pasivo (sin worker) | P2 | `spec §4.3` | — | `R-145` | grupo | AGRUPADO | D | ídem | no | abierto |
| `H360-S13` | `external_transaction_id` solo tras éxito; `sap_reference_item` nunca poblado | P2 | Rec. §19 | — | `R-145` | grupo | AGRUPADO | D | ídem | no | abierto |
| `H360-S04` | OT no validada en `feed_registration` | P2 | Rec. §8 | — | `R-145` | grupo | AGRUPADO | D | ídem | no | abierto |
| `H360-S08` | payload no mapeable a documento SAP; sin matriz por proceso | P1 (D) | Rec. §16, §22, §24 | `GA-REM-017` (tema) | **`R-157`** | causa distinta del conector | NUEVO bajo alcance de `GA-REM-017` | D | enm. `GA-REM-017` | `AOD-01…05` | bloqueado por decisión |
| `H360-S09` | sin confirmación entrante SAP → app; estados SAP sin productor | P1 (D) | Rec. §18, §26 | `GA-REM-017` | `R-157` | misma unidad de diseño | AGRUPADO | D | ídem | no | abierto |
| `H360-S12` | sin `idempotency_key` de cliente en móvil | P2 | Rec. §17 «duplicidad» | — | **`R-146`** | no | NUEVO | E | enm. `GA-REM-011` | `AOD-16` relacionada | abierto |
| `H360-S06` | período cerrado = 90 días fijos | P3 | Rec. §15 | — | **`R-155`** | no | NUEVO | D | — | **`AOD-15`** | pendiente de decisión |
| `H360-B05` = `H360A-10` | consumo de agua ausente | P1 | `Bases` p.2/4/12 | **`R-13`** / `GA-REM-021` | — | sí | **MAP** | B | ya existe (`SPEC_READY`) | no | abierto |
| `H360-B01` | cuadre de recepción (♀+♂+mort.+rechazo) | P2 | Rec. §6 | `GA-REM-021` | — | mismo tema (captura exigida por el cliente) | **MAP** → `GA-REM-021` enmienda pendiente | B | enm. | no | abierto |
| `H360-B02` | pesos en rango en recepción | P2 | Rec. §6 | `GA-REM-021` | — | ídem | **MAP** | B | enm. | no | abierto |
| `H360-B03` | alimento sin lote/silo/diferencias | P2 | Rec. §8 | `GA-REM-021` | — | ídem | **MAP** | B | enm. | no | abierto |
| `H360-B04` | evidencia no obligatoria antes de aprobar | P2 | Rec. §6 | `GA-REM-021` | — | ídem | **MAP** | B | enm. | **`AOD-14`** | pendiente |
| `H360-B13` | sanos/débiles no distinguidos al nacer | P2 | `Bases` p.9 | `GA-REM-021` | — | ídem | **MAP** | B | enm. | no | abierto |
| `H360-B11` | peso reportado por proveedor vs granja | P3 | legado p.18 | — | **`R-156`** | no | NUEVO (paridad de legado, nivel 6) | B | enm. `GA-REM-021` | no | abierto |
| `H360-B06` | unidad de medida sin catálogo | P2 | Rec. §17 | — | **`R-147`** | no | NUEVO (grupo constantes/tipos) | B/C | nueva spec | no | abierto |
| `H360-B07` | umbrales T°/H° fijos 18-35 / 40-90 | P2 | `docs/02:516` | — | `R-147` | grupo | AGRUPADO | B | ídem | no | abierto |
| `H360-B10` | `sex` `String` vs `SexEnum` | P3 | modelo | — | `R-147` | grupo | AGRUPADO | B | ídem | no | abierto |
| `H360-B12` | capacidad de incubadora no validada | P3 | `BR-17` (análogo) | — | `R-147` | grupo | AGRUPADO | B | ídem | no | abierto |
| `H360-B08` | pasos de aprobación por nombre de rol | P3 | `GA-REM-040 §4.1` (principio) | — | `R-147` | grupo | AGRUPADO | B | ídem | no | abierto |
| `H360-B09` | `date.today()` sin zona horaria (10 sitios) | P2 | `GA-REM-028` | **`R-80`** | — | sí | **MAP** → `R-80` (fecha local vs UTC) | C | enm. `GA-REM-028` | no | abierto |
| `H360-D04` | auditoría inmutable solo en aplicación | P2 | `docs/13 §8` | — | **`R-148`** | no | NUEVO | B | enm. `GA-REM-032` | no | abierto |
| `H360-D01` | `OD-04/06/08` sin archivo propio | P2 | `GA-REM-001` | — | **`R-149`** | no | NUEVO (grupo documental) | A (documental) | — | no | abierto |
| `H360-D02` = `H360-D12` | `spec §14` → `docs/17` inexistente | P2 | `spec §14` | — | `R-149` | grupo | AGRUPADO | A | enm. `spec` | no | abierto |
| `H360-D03` | `BR-17…19` fuera de `spec §5` | P2 | `spec §5` | — | `R-149` | grupo | AGRUPADO | A | enm. `spec` | no | abierto |
| `H360-D05` | `GA-REM-016` en `SPEC_DRAFT` mientras ampara 15 certificaciones | P2 | `GA-REM-016` | `GA-REM-016` | `R-149` | grupo | AGRUPADO | F | pasar a `SPEC_READY` | no | abierto |
| `H360A-07` | `docs/03 §3.5` enum de tres valores | P3 | `docs/03` | — | `R-149` | grupo | AGRUPADO | A | — | no | abierto |
| `INDEX.md` deriva (§2 de la matriz de autoridad) | 10 estados desactualizados | P2 | `GA-REM-001` | — | `R-149` | grupo | **RESUELTO en este commit** | A | — | no | cerrado |
| `H360-D06` = `H360A-06` | granjas/empresa: Rec. §1/§15 vs `docs/02 §3.2.1`; `companies` colapsa entidad e inquilino | P1 | Rec. §1 | **`R-124`** / `AOD-06` | — | sí | **MAP** | D | — | `AOD-06` | pendiente |
| `H360-D07` | identidad local vs SAP IAM | P3 | Rec. §15 | `AOD-07` | — | sí | **MAP** | G | — | `AOD-07` | pendiente |
| `H360-D08` | cierre de lote operativo vs liquidación SAP | P2 | Rec. §13/§21 | `AOD-08` | — | sí | **MAP** | B | — | `AOD-08` | pendiente |
| `H360-C01` | 67/208 rutas sin `response_model` | P2 | `GA-REM-011` | `GA-REM-011` (`PARTIALLY CERTIFIED`) | — | sí | **MAP** → alcance restante de `GA-REM-011` | E | enm. | no | abierto |
| `H360-T01` | CI sin `FEATURE_SAP_ENABLED` (9 tests SAP saltan) | P2 | `GA-REM-013` | `GA-REM-013` | — | sí | **MAP** → enmienda `GA-REM-013` | A | enm. | no | abierto |
| `H360-F01` | ninguna pantalla oculta acciones por permiso | P1 | `GA-REM-040 §14.2` | **`R-98`** / **`R-119`** | — | sí | **MAP** | E (fase 9) | ya existe | no | abierto |
| `H360-F02` | estados de error solo en `/users` | P2 | `R-120` (cerrado solo para `/users`) | — | **`R-150`** | no (generalización) | NUEVO | E | enm. `GA-REM-011` | no | abierto |
| `H360-F03` | evidencia solo en el detalle, no en la captura | P2 | Rec. §6 · `docs/02 §7` | — | **`R-151`** | no | NUEVO | E | nueva spec | `AOD-16` relacionada | abierto |
| `H360-P02` | `DRAFT` sin productor | P3 | `docs/12 §4` fila 1 | — | **`R-154`** | no | NUEVO (grupo estados/campos muertos) | B | — | no | abierto |
| `H360-P09` | dos artefactos llamados «cierre» | P3 | `GA-REM-029` | — | `R-154` | grupo | AGRUPADO | B | — | `AOD-08` | abierto |
| `H360-P11` | `version` nunca se incrementa | P3 | `docs/13` | — | `R-154` | grupo | AGRUPADO | B | — | no | abierto |
| `H360A-01` | la interfaz asume las cuatro unidades; no lee la sesión | P2 | `GA-REM-040 §14.2-14.3` · `OD-16` | `GA-REM-040` fase 9 | — | sí | **MAP** → fase 9 (bloqueada por `R-127`) | E | ya existe | no | abierto |
| `H360A-02` | importación de abuelas sin estructura (`docs/02 §3.4.1`) | P2 | `docs/02 §3.4.1` | — | **`R-152`** | no | NUEVO | B | nueva spec | no | abierto |
| `H360A-03` | creación automática del lote de abuelas | P3 | `docs/02 §3.4.2` | — | **`R-153`** | no | NUEVO | B | nueva spec | no | abierto |
| `H360A-04` | E2E de progenitoras sin fase ni cierre | P2 | `GA-REM-016` | `GA-REM-016` | — | sí | **MAP** → enmienda de evidencia `P-01` | F | enm. | no | abierto |
| `H360A-05` | activación por empresa sin certificación de proceso (0 E2E · 0/15) | P2 | `OD-16` · `GA-REM-040` fases 10-11 | `GA-REM-040` | — | sí | **MAP** → fases 10-11 | F | ya existe | `BU-D10` (reactivación) | abierto |
| `H360A-09` | quién habilita: comercial vs operativo | P2 | `BU-D07` | `BU-D07` | — | sí | **MAP** | — | — | `BU-D07` pendiente | pendiente |

```
hallazgos reconciliados ......... 75   (65 H360 + 10 H360A, más la deriva de INDEX)
sin disposición ................. 0
IDs nuevos ...................... 28   R-130 … R-157
mapeados a ID existente ......... 20
agrupados bajo un ID nuevo ...... 27
resueltos en esta ola ........... 2    (H360-D09 por OD-17 · deriva de INDEX)
```

Cada `R-13x/14x/15x` aparece en `REMEDIATION_BACKLOG.md` con su `source_finding`, y en
`DEPENDENCY_MAP.md` con su ola.
