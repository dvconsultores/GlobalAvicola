# `GA-REM-021` · `B03` · MATRIZ DE CONTRATO DEL ALIMENTO POR TRANSFERENCIA

**WAVE B · tranche 8 · pre-flight** · 2026-09-10 · `H360-B03` (P2, «alimento sin lote/silo/diferencias») · fuente `Recomendación
central.pdf` §8 (p.11-12) · resultado: **`OWNER_DECISION_REQUIRED` (`AOD-22`) + dependencia `AOD-19` (`R-147`, unidades) → sin código**.

## 1. Requisito exacto (nivel 2, textual)

```
§8 Proceso recomendado: alimento por transferencia
En SAP: orden de transferencia · centro/almacén origen · centro/almacén destino · material alimento · lote/batch · cantidad · unidad · fecha · documento logístico.
En la app: consultar transferencias activas · confirmar llegada · registrar cantidad recibida · registrar diferencias · registrar lote de alimento ·
           registrar silo o almacén destino · registrar evidencia · registrar consumo parcial diario/semanal.
Envío a SAP — dos eventos: (1) recepción del alimento transferido («Llegó la transferencia X con cantidad real Y. SAP registra la recepción o
           diferencia») · (2) consumo («Lote productivo A consumió X kg del alimento Y» → salida de inventario contra centro de costo / orden interna / lote).
```

`docs/02 §3.5.3` (nivel 3) solo define el **consumo** («Cantidad (kg), Orden de alimento SAP (si aplica)»). `spec.md` (nivel 4): un solo tipo,
`feed_registration` = consumo. `docs/16 §6.3` (mapa del auditor): consultar ✅ (`SapReference TRANSFER_ORDER`), confirmar llegada ✅
(`feed_registration` con `sap_order_id`), cantidad recibida ✅ (`quantity_kg`), **diferencias ❌ · lote ❌ · silo/almacén ❌**, evidencia (`B04`),
consumo parcial ✅. `SoR`: OT `ESPEJO_LECTURA` (`:26`), material `LOCAL_PLACEHOLDER` (`:21`), inventario `SAP_DEFERRED` (`:27`), almacenes/silos
`SAP_DEFERRED` (`:28`), validación operativa `APP_MANDANTE` (`:52`). `H360-S04` (OT no validada) → `R-145`, ola D (fuera).

## 2. Gate — ¿qué es `B03`?

`B03` = los tres datos ausentes de la **llegada** de una transferencia de alimento: **diferencia** contra la OT, **lote/batch** del alimento y
**silo o almacén destino**. No es el consumo (cubierto), no es la validación de la OT (`S04`), no es la evidencia (`B04`), no es inventario (SAP).

## 3. Matriz de contrato (por unidad)

| BU | Proceso | Fuente | Recurso origen | Recurso destino | Material | Cantidad | UoM | Fecha | Referencia | SoR | Efecto app | Efecto SAP | ¿Varias/día? | Duplicado | Corrección | Aprobación | Reverso | Inquilino | BU auth | RBAC | Auditoría | Soporte actual | Brecha | Decisión | AC | Test |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Reproductoras · Engorde · Progenitoras | llegada de alimento por OT | Rec. §8 | centro/almacén origen (SAP) | **silo o almacén destino (SAP `STORAGE_LOCATION`, `SAP_DEFERRED`)** | alimento (SAP MM; `feed_types` placeholder) | recibida | **la de la OT** (SAP); la app solo conoce kg (nivel 3, consumo) | llegada (`event_date`) | OT (`SapReference TRANSFER_ORDER`, `quantity`, `unit`) · **lote/batch** (`SAP_BATCH`, sin uso) | app: captura · SAP: entrada/ajuste | registro operativo | recepción o diferencia | **no gobernado** | `sap_order_id` texto en la fila; `BR-10` no aplica | `P-07` | existente | no elegible (`GA-REM-041 §3.5`) | cadena certificada | cadena certificada | `operations:create` | existente | `feed_registration` (mismo tipo que el consumo) + `sap_order_id` | **sin diferencia, sin lote, sin silo, sin tipo de evento distinto del consumo** | **`AOD-22`** | — | — |
| Incubadora | — | §12 no lista alimento | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | N/A | — | — | — | — |

## 4. Cada semántica, con su nivel — y las que ningún nivel fija

| Semántica | ¿Gobernada? | Por qué |
|---|:--:|---|
| la llegada es un hecho distinto del consumo (dos eventos SAP) | sí (nivel 2) | usar `feed_registration` para ambas duplicaría el alimento «consumido» en `_sum_feed_kg`, cierre de lote y consolidación SAP |
| captura de lote/batch y de silo/almacén destino como **referencias** (identificadores SAP, sin maestro local) | sí (nivel 2 + `SoR:28`) | el maestro es de SAP (`SAP_DEFERRED`); un maestro local sería «ERP paralelo» (`SoR:5`) |
| **diferencia** = recibida − transferida: ¿por llegada o acumulada contra la OT? ¿admite la OT varias llegadas parciales? | **no** | `OD-04` decidió entregas parciales **para órdenes de compra y aves**; `GA-REM-035 §4`: «extenderla sería inventar política». Con parciales, la diferencia por llegada es engañosa y la acumulada exige la regla de `OD-04` que no existe para OT |
| unidad: la OT viene con su `unit` (SAP); la app mide kg; sin catálogo de unidades ni conversión | **no** | `R-147`/`H360-B06` → `AOD-19` (pendiente); `GA-TD-014 §14` esquivó la conversión porque en aves no la había |
| ¿la diferencia se persiste (dato) o se deriva (lectura)? ¿signo? ¿cero es dato o ausencia? | **no** | ninguna fuente; `RR-11` (ausencia ≠ 0) colisiona con una diferencia de 0 legítima |
| ¿el consumo debe citar el lote de alimento? | no (implícito) | Rec. §8 lo pide en la llegada; nada lo exige en el consumo |

**Regla de escalado:** las semánticas 3-5 cambian el comportamiento de negocio y no las fija ningún nivel por encima de la implementación
→ **`OWNER_DECISION_REQUIRED` (`AOD-22`)**. Además, la comparabilidad de unidades depende de `AOD-19`. Las semánticas gobernadas (tipo de
evento propio, referencias de lote y silo) no cierran `B03` por sí solas: el dato central del §8 («diferencias») es el bloqueado.

## 5. Independencia y sistema de registro

`B03` no depende de `B13` ni al revés; no toca `R-130` ni `R-161`; no requiere SAP real para la captura, pero **la diferencia contra la OT es
justamente el dato que SAP convierte en entrada o ajuste** (`docs/10:77-81`), por lo que su semántica no puede fijarse desde la app.
Sistema de registro: SAP para OT, material, lote/batch, almacenes, inventario; app para la captura operativa.

## 6. Resultado del gate

```
B03 gobernado por completo .......... NO (diferencia · parciales · unidad · persistencia del cero)
B03 depende de B13 .................. NO            B13 depende de B03 ............ NO
dependencia SAP ..................... PARCIAL (semántica de la diferencia = documento SAP; maestros SAP_DEFERRED)
decisión del propietario ............ SÍ → AOD-22 (+ AOD-19 pendiente)
modo del tranche .................... C · B13 ONLY (+ R-170 · R-169 · R-168) · NO B03 CODE
```

## Resultado (2026-09-10)

`B03` **no se implementó**: `OWNER_DECISION_REQUIRED` (`AOD-22`) + dependencia `AOD-19`. Registrado en `AUDIT_OWNER_DECISIONS_REQUIRED.md`.
