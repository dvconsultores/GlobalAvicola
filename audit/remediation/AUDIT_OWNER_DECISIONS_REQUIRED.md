# DECISIONES DEL PROPIETARIO REQUERIDAS — AUDITORÍA 360°

**2026-09-09** · base `7310adb` · **AUDIT ONLY**

Regla: `NO DECIDIR POR EL PROPIETARIO` · `NO ASIGNAR OD-ID DEFINITIVOS sin consultar el registro`.
El registro (`specs/remediation/OD-09…OD-15`) llega a **`OD-15`**; las decisiones de esta
auditoría se numeran **`AOD-nn` (provisional)** y recibirán `OD-16+` cuando el propietario las
resuelva y se redacten. `BU-D10` **no se resuelve aquí** (instrucción expresa). Cada entrada
dice por qué la evidencia no basta, qué bloquea y qué ola la necesita.

| AOD | Pregunta | Opciones (sin preferencia) | Por qué no se resuelve por evidencia | Bloquea | Prioridad · Ola |
|---|---|---|---|---|---|
| **AOD-01** | ¿El ave viva es **inventario valorizado** en SAP o **solo población productiva**? (Rec. §25.1) | A inventario (recepción = entrada de mercancía por unidad; mortalidad = baja) · B población (KPI y costo por lote; sin stock de aves) | ninguna fuente de nivel 1-4 se pronuncia; cambia el documento SAP de recepción, mortalidad y salida | mapeo del payload (`H360-S08`), `AOD-04` | **P1 · WAVE D** |
| **AOD-02** | ¿El galpón es **almacén SAP**, **ubicación técnica PM** o **dimensión operativa** de la app? (Rec. §25.2) | A almacén · B ubicación técnica · C dimensión local | ídem; la Recomendación §4 desaconseja «cada galpón = almacén» pero no decide | detalle por galpón hacia SAP; origen de `houses.capacity` | P1 · WAVE D |
| **AOD-03** | ¿El lote productivo es **batch**, **orden interna**, **orden de producción** o **custom object**? ¿Y qué identificador SAP guarda `lots`? (Rec. §25.3, `H360-S05`) | A batch · B orden interna · C orden de producción · D custom; + campo `sap_lot_ref` obligatorio/opcional | ídem; la app legada tenía «Id SAP» en el lote (nivel 6, no normativo) | «cada recepción asociada a un lote oficial» (Rec. §3.3); costeo por lote | **P1 · WAVE D** (la columna puede prepararse en WAVE B) |
| **AOD-04** | ¿La mortalidad genera **movimiento de inventario** o es **solo indicador/costo**? (Rec. §25.4 = `RC-07`) | A movimiento (baja/merma) · B indicador · C estadístico + CO | `RC-07_BUSINESS_DECISION_DOSSIER.md` lo dejó en `OWNER_DECISION_REQUIRED` el 2026-09-03; sigue igual | payload de mortalidad | P1 · WAVE D |
| **AOD-05** | ¿La bioseguridad/inspección vive en **SAP QM/custom** o **solo en la app con resumen a SAP**? (Rec. §25.5) | A QM · B app + resumen | la Recomendación recomienda B pero pide decisión de la empresa | qué se envía de `farm_inspection` y alertas | P2 · WAVE D |
| **AOD-06** | ¿Empresas y granjas **vienen de SAP** (sociedad/centro) o son **maestros locales** con código SAP? (`R-124`, `H360-D06`) | A importadas, no editables · B locales con `sap_code` obligatorio · C locales sin vínculo (estado actual) | conflicto nivel 2 (Rec. §1/§15) vs nivel 3 (`docs/02 §3.2.1`) | `P-12`, `SAP_DEFERRED_LOCAL_PLACEHOLDERS PL-05/06`, fase 9 (selector de empresa muestra maestros locales) | **P1 · antes de WAVE D; no bloquea fase 9** |
| **AOD-07** | ¿La identidad de usuario es **local** (estado actual, `OD-13`) o **SAP IAM/SSO**? (Rec. §15 «Usuarios autorizados → SAP/IAM», `H360-D07`) | A local · B SSO con SAP/IdP · C local ahora, SSO después | conflicto nivel 2 vs nivel 3 | nada hoy; diseño de `P-13` a largo plazo | P3 · WAVE G |
| **AOD-08** | ¿Qué significa `lots.status = closed`? ¿**Cierre operativo** local (Rec. §13 «datos de cierre») distinto de la **liquidación** SAP (Rec. §21), o el mismo acto? (`H360-D08`) | A cierre operativo, SAP liquida después (dos actos) · B un solo acto disparado por SAP · C un solo acto disparado por la app (**contradice Rec. §21**) | terminología no declarada en spec ni código | resumen de cierre (`H360-P08`), payload de cierre de engorde | P2 · WAVE B |
| **AOD-09** | ¿`REJECTED` es **terminal** (código) o el operador **reenvía corregido** (`docs/12 §4` fila 8)? ¿`RETURNED` se reenvía por el operador o solo por corrección? (`H360-P03`, `H360-D09`) | A terminal (corregir `docs/12`) · B reenviable (implementar `REJECTED → REGISTERED` con motivo) · C `RETURNED` editable + `submit` | nivel 3 y nivel 5 discrepan; la spec calla | `P-07`, UX móvil de devolución | **P1 · WAVE B** |
| **AOD-10** | Definiciones KPI abiertas: (a) denominador de **fertilidad** (puestos · recogidos · recibidos en incubadora); (b) **hen-day**: período y base (hembras vivas vs iniciales); (c) **índice de bienestar**: definición; (d) **uniformidad**: CV entre pesajes vs % dentro de ±10 %; (e) base del % de mortalidad: inicial, actual o ambas (Rec. §9) | por KPI | `Bases` da dos fórmulas o ninguna; Ross/Cobb son referencia, no requisito | `H360-K04/K05`, `P-15` conformidad | P2 · WAVE C |
| **AOD-11** | Regla del **alta del primer cliente real** en `ENV-01` (único entorno): qué se vacía, qué se importa de SAP, qué maestro local queda definitivo (`SAP_DEFERRED_LOCAL_PLACEHOLDERS §4`) | A vaciado total + importación · B conservar catálogos operativos, importar maestros SAP · C nada hasta `GA-REM-017` | decisión de operación, no de código | frontera placeholder/real; riesgo de datos ficticios en producción | P1 · WAVE D/G |
| **AOD-12** | ¿Dónde viven las **credenciales/configuración SAP**: por empresa (`Company.sap_config`, hoy `R-127`) o por entorno (`.env`)? ¿Debe `sap_config` viajar en el listado de maestros? | A por empresa, expuesto solo en superficie administrativa · B por entorno · C ambos | diseño no fijado; `data-model.md` solo tipa `JSON` | forma final de la corrección de `R-127` (**no** su necesidad: el tipo `JSON` ya lo fija la spec) | P2 · WAVE A (solo la parte de exposición) |
| **AOD-13** | Módulos/capacidades **activables por empresa** (`R-125`) | A por unidad de negocio (ya existe) · B además por módulo funcional · C no | producto | `GA-REM-040` fases 10-11 | P2 · WAVE E |
| **AOD-14** | ¿Qué procesos exigen **evidencia adjunta** antes de aprobar? (Rec. §6 «Que exista evidencia»; `H360-B04`) | por tipo de evento: obligatoria / recomendada / no | política operativa | validación de aprobación | P2 · WAVE B |
| **AOD-15** | **Período cerrado**: ¿mantener los 90 días como *placeholder* configurable, o eliminar la regla hasta que SAP provea períodos? (`BR-19`, `H360-S06`) | A configurable por empresa · B eliminar · C mantener fijo | ninguna fuente fija 90 | consistencia con SAP FI/CO | P3 · WAVE D |
| **AOD-16** | ¿La v1 exige **captura offline** en móvil? (`docs/02:595` «futuro»; `spec §9` no lo excluye; `docs/00` «operador de campo es el usuario más importante») | A no en v1 · B sí, cola local con `idempotency_key` | alcance | `H360-S12`, `H360-F03`, arquitectura móvil | P2 · WAVE E |
| `BU-D10` | (pendiente desde `GA-REM-040`) | — | **no se toca** | — | — |

## Orden sugerido de resolución (no vinculante)

```
antes de WAVE B ..... AOD-09 · AOD-08 · AOD-14 · ~~AOD-21~~ (→ `OD-19`, resuelta 2026-09-09)
antes de WAVE C ..... AOD-10
antes de WAVE D ..... AOD-01 · AOD-02 · AOD-03 · AOD-04 · AOD-05 · AOD-06 · AOD-11 · AOD-15
antes de WAVE E ..... AOD-13 · AOD-16
WAVE A solo necesita AOD-12 en su parte de exposición; la corrección de tipo de R-127 no espera a nadie.
```

---

## Registro de formalización (2026-09-09 · WAVE A0-G)

| Provisional | Oficial | Estado | Nota |
|---|---|---|---|
| — | **`OD-16`** | VIGENTE | requisito de producto aprobado directamente por el propietario (cuatro unidades · activación por empresa); no procede de esta lista |
| `AOD-09` | **`OD-17`** | VIGENTE | un rechazo corregible no es terminal; `RETURNED`/`REJECTED` se corrigen y reenvían; SAP: reenvío explícito, nunca automático. Implementación en `WAVE B` |
| `AOD-12` | **`OD-18`** | VIGENTE | el catálogo general de empresas no expone `sap_config`; persistencia `DEFERRED`; sin migración |
| `AOD-01…08`, `AOD-10`, `AOD-11`, `AOD-13…16` | — | pendientes | sin decisión del propietario; no se asigna `OD` |
| `BU-D10` | — | `PENDING_RATIFICATION` | ver `BUSINESS_UNIT_OWNER_DECISION_MATRIX.md §7` |

La numeración `AOD-nn` de este documento **no se renumera**.

## `AOD-21` · registro del pre-flight del tranche 5 (2026-09-09 · WAVE B)

| AOD | Pregunta | Opciones (sin preferencia) | Por qué no se resuelve por evidencia | Bloquea | Prioridad · Ola |
|---|---|---|---|---|---|
| **AOD-21** | **Reverso interno** (`R-136`, `G-R09`, Rec. 7.17): ¿cómo se neutraliza un registro **aprobado** aún no enviado a SAP? (a) **estado**: reutilizar `CANCELLED` para el aprobado (contradice `docs/12 §2`: Anulado solo desde Borrador/Registrado) o crear `REVERSED` (vocabulario nuevo + migración); (b) **contrapartida**: excluir el original del conjunto de efectos con fila `reversals`, o registrar un **evento inverso** que pase por el flujo de aprobación (`R13`), o ambas; (c) **elegibilidad**: solo `APPROVED`, o también `CONSOLIDATED` (exige des-consolidar el lote, `R8`); (d) **autoridad**: qué permiso reversa (mismo caso que «solo administrador», `AOD-18`) y si quien aprobó puede reversar lo suyo; (e) **huevos/incubación**: incluir pese a `R-161` o excluir hasta cerrarlo | A `CANCELLED` + `reversals` + exclusión · B `REVERSED` nuevo + `reversals` + exclusión (migración) · C evento inverso aprobado (contrapartida contable) + `reversals` · D combinaciones; autoridad: permiso nuevo / `approvals:*` / `operations:delete` | `BR-16`/`R16` solo gobiernan el ajuste **post-SAP** y nombran el reverso sin definirlo; `OD-17.a` lo declara clase terminal distinta de `CANCELLED` sin definirlo; Rec. §24 («Reverso: cómo se anula») es un PDF no versionado; `docs/16 §8` deja el gap explícito («no hay REVERSADO con registro compensatorio»); el modelo `Reversal` fija solo motivo obligatorio y vínculo al original | `R-136` interno (P1) · toda corrección de un aprobado pre-SAP · el payload SAP futuro (`AOD-04`) | **P1 · WAVE B** (la parte post-SAP sigue en WAVE D con `AOD-04`/`OD-12`) |

Evidencia: `R136_INTERNAL_REVERSAL_PREFLIGHT.md` · `R136_INTERNAL_REVERSAL_EFFECT_MATRIX.md`. El registro de `OD-*` llega a `OD-18`; `AOD-21` recibirá su `OD-nn` cuando se resuelva.

**`AOD-21` → `OD-19`** (2026-09-09): resuelta por el propietario; texto formalizado en `specs/remediation/OD-19-INTERNAL-REVERSAL-OF-APPROVED-RECORDS.md`; spec `GA-REM-041`.

## `AOD-22` y `AOD-23` · registro del pre-flight del tranche 8 (2026-09-10 · WAVE B)

| AOD | Pregunta | Opciones (sin preferencia) | Por qué no se resuelve por evidencia | Bloquea | Prioridad · Ola |
|---|---|---|---|---|---|
| **AOD-22** | **Alimento por transferencia** (`GA-REM-021 B03`, Rec. §8 «registrar diferencias · lote de alimento · silo o almacén destino»): (a) ¿una orden de transferencia (OT) de alimento admite **varias llegadas parciales**, y la **diferencia** se calcula **por llegada** o **acumulada** contra la cantidad de la OT? (b) ¿la diferencia es un **dato declarado** por el operador o se **deriva** de la OT (recibida − transferida), y un cero es dato o ausencia? (c) cuando la **unidad** de la OT no es kg (`R-147`/`AOD-19`), ¿la app compara, convierte o declara «no comparable»? (d) ¿«lote de alimento» y «silo o almacén destino» se registran como **referencias SAP** (identificadores; el maestro es de SAP, `SoR:28`) — lectura que la evidencia favorece — o exigen maestro local? | (a) una llegada por OT · varias, diferencia por llegada · varias, diferencia acumulada (extensión de `OD-04` a OT) · (b) declarada · derivada · (c) solo kg / declarar no comparable / conversión (requiere `AOD-19`) · (d) referencias SAP · maestro local | `OD-04` decidió parciales para **órdenes de compra y aves**; `GA-REM-035 §4` prohíbe extenderla por inferencia. Ninguna fuente de nivel 1-4 fija la diferencia, su signo, su persistencia ni la unidad. `RR-11` (ausencia ≠ 0) colisiona con una diferencia legítima de 0. Matriz: `GA_REM_021_B03_FEED_TRANSFER_MATRIX.md` | `B03` (código); no bloquea `B13`, `R-170`, `R-169`, `R-168` | P2 · B |
| **AOD-23** | **Nacimiento** (`GA-REM-021 B13`, `Bases` p.9): ¿**sanos + débiles = nacidos** (partición completa: todo pollito nacido queda clasificado) o pueden quedar pollitos **sin clasificar** (`sanos + débiles ≤ nacidos`)? | igualdad exigida · desigualdad admitida | `Bases` p.9 define ambos como subconjuntos disjuntos de «nacidos» (garantiza `≤`) y **no afirma** la igualdad; la elección cambia qué registros se rechazan. `B13` se implementa con la restricción derivable (`≤`); la igualdad, si se decide, es un endurecimiento sin migración | nada (endurecimiento posterior) | P3 · B |

`AOD-22` se resolverá como `OD-20+`; `AOD-23` ídem. Ninguna se decide aquí (`NO DECIDIR POR EL PROPIETARIO`).

## Registro del pre-flight del tranche 10 (2026-09-10 · WAVE B)

Sin decisión nueva. `R-173` (cambio de lote y cancelación frente a los saldos), `R-172` (qué huevo cuenta como disponible), `R-174` (despacho de pollitos
de 0) y `R-171` (catálogo de incubadora) se resuelven por fuentes de nivel 2-4 (`RC-14`, `RC-15`, `RR-16`, `GA-REM-005-B §B.2`); las trazas están en
`R173_EDIT_CANCEL_BALANCE_EFFECT_MATRIX.md §7`, `R172_EGG_TYPE_AVAILABILITY_MATRIX.md §6` y `R174_ZERO_QUANTITY_DISPATCH_AUTHORITY_TRACE.md §2`.
Pendientes sin cambio: `AOD-08`, `AOD-14`, `AOD-17`, `AOD-18`, `AOD-19`, `AOD-20`, `AOD-22`, `AOD-23`.

## `AOD-24` · registro del pre-flight del tranche 11 (2026-09-10 · WAVE B)

| AOD | Pregunta | Opciones (sin preferencia) | Por qué no se resuelve por evidencia | Bloquea | Prioridad · Ola |
|---|---|---|---|---|---|
| **AOD-24** | **Tipo de huevo y resultado de ovoscopía** (`R-177`, `R177_EGG_TYPE_OVOSCOPY_DOMAIN_MATRIX.md`): hoy un solo campo libre (`egg_movements.egg_type`) guarda los tipos de huevo de la recolección (`docs/02 §3.6.2`, `docs/03 :277`: fértil, sucio, roto, infértil, descartado, comercial) **y** los resultados de la ovoscopía (`docs/02 §3.7.3`, `spec.md :192`: infértiles, embriones muertos tempranos/tardíos, contaminados). ¿Deben ser (A) un único conjunto cerrado que incluya ambos, o (C) dos datos distintos —`egg_type` en la recolección/clasificación y un resultado propio en la ovoscopía—? ¿Y qué valores exactos admite cada evento? | **A** · enum cerrado único (`docs/03` + categorías de `spec.md :192`) · **C** · dos campos/conceptos (los documentos los describen en eventos distintos). B (maestro configurable) y D (maestro existente) no tienen respaldo documental | los niveles 2-4 nombran las categorías pero no dicen si son el mismo atributo ni cómo se almacenan; la elección cambia el modelo de datos, la captura y la validación | `R-177` (validación de valores, etiquetas, UI) — no bloquea saldos (`RR-17` independiente) | P3 · WAVE B |

`AOD-24` se resolverá como `OD-20+`. No se decide aquí (`NO DECIDIR POR EL PROPIETARIO`). `R-176` y `R-178` no requieren decisión (fuentes en
`R176_CREATE_EDIT_CORRECTION_VALIDATION_PARITY_MATRIX.md §7` y `R178_LINEAGE_CANCEL_MOVE_INTEGRITY_MATRIX.md §3`).
