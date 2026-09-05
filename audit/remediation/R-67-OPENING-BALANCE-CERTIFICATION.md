# CERTIFICACIÓN — `R-67` · SALDO DE APERTURA

**`GA-REM-005`, enmienda `R-67`** · 2026-09-04 · **`CERTIFIED`**

---

## 1. El defecto

`POST /lots/activate-manual` guardaba la población del lote en `opening_balances` y
`get_current_bird_balance` **no la consultaba**. Ningún otro punto del código la leía.

```
activate-manual → 201, initial_male=1000 initial_female=4000
mortalidad de 12 → 400 «Mortalidad (12) excede el saldo de aves disponibles (0)»
```

Un lote incorporado manualmente quedaba **inoperable**: no admitía mortalidad, ni descarte,
ni salida.

## 2. Por qué importaba

La activación manual es el mecanismo previsto para incorporar **lotes ya en marcha cuando
el sistema se instale en un cliente** — `docs/02 §3.9`, prioridad «Crítica (para
implantación)». El defecto recaía exactamente sobre el primer cliente real.

Era invisible porque todos los lotes del entorno compartido venían de eventos de recepción
sembrados. Lo descubrió el recorrido de instalación limpia de `GA-REM-025`, que es
precisamente lo que ese trabajo buscaba.

## 3. `RC-08` — qué significa «saldo inicial»

Al resolverlo apareció una contradicción entre dos piezas existentes. Se resolvió por la
jerarquía de evidencia, **no por criterio técnico**.

| Alternativa | Sostenida por | Nivel |
|---|---|:--:|
| **A** · `initial_*_count` es el saldo vivo; los acumulados son histórico | `docs/02 §3.9.1` distingue «Saldos iniciales de aves» de «Mortalidad acumulada previa» y «Descartes acumulados» · §3.9.2 «continuar operación desde el saldo inicial» y «Se evita doble conteo» · `reports/service.py:193` ya lo calculaba así | **3** |
| **B** · es la población original y hay que restar los acumulados | el mensaje «Mortalidad acumulada no puede exceder población inicial» (`lots/service.py:209`) | 5 |

**A · `RESOLVED_BY_EVIDENCE`.** El nivel 5 no puede contradecir al nivel 3.

> **`RR-08`.** El saldo de apertura es `initial_male_count + initial_female_count`. Los
> campos `accumulated_*` son histórico previo a la implantación y **no se restan**:
> restarlos sería el doble conteo que `docs/02 §3.9.2` prohíbe.

## 4. La corrección

**Regla de balance**, en `validators.py::get_current_bird_balance`:

```
SALDO = saldo de apertura + Σ(entradas) − Σ(salidas)
```

Detalle completo en [`BIRD_BALANCE_SOURCE_MATRIX.md`](BIRD_BALANCE_SOURCE_MATRIX.md).

**Sin historia inventada.** No se genera ningún evento de recepción ficticio al activar:
falsificaría historia empresarial. `AC-R67-02` lo verifica contando eventos tras la
activación — cero.

**Doble conteo**, en `lots/service.py::activate_manual`: la activación se rechaza con `409`
si el lote ya tiene operaciones no canceladas. `docs/02 §3.9.2` lo exigía y nada lo
implementaba.

**Y una corrección de aislamiento que la certificación destapó.** Al comprobar `AC-R67-11`
resultó que lo único que impedía activar el lote de otra empresa era **carecer del permiso
`lots:create`**:

```
usuario de la empresa B, rol propio  → 403 «Permiso requerido: lots:create»
```

`activate_manual` buscaba el lote por identificador sin filtrar por compañía. Quien tuviera
ese permiso en su propia empresa podía fijar el saldo de apertura de un lote ajeno. Se
añadió la comprobación de pertenencia que ya usa el resto del sistema
(`tenancy.verificar_pertenencia`, `GA-REM-002 AC10`).

## 5. Criterios de aceptación

| AC | Criterio | Prueba | Resultado |
|---|---|---|---|
| **AC-R67-01** | Activar con N produce saldo N de inmediato | `T-067-01` | **PASS** — 5 000 |
| **AC-R67-02** | Sin evento histórico ficticio | `T-067-01` | **PASS** — 0 eventos creados |
| **AC-R67-03** | La mortalidad posterior reduce el saldo | `T-067-02` | **PASS** — 4 988 |
| **AC-R67-04** | Las entradas posteriores lo aumentan | `T-067-04` | **PASS** — 5 500 |
| **AC-R67-05** | Sin doble conteo | `T-067-05`, `T-067-06` | **PASS** — acumulados no restados; activación de lote con historia rechazada con 409 |
| **AC-R67-06** | El flujo normal no cambia | `T-067-07`, `T-067-08` | **PASS** — 2 000 → 1 975 |
| **AC-R67-07** | Correcciones y ajustes sin cambios | — | ninguna regla nueva |
| **AC-R67-08** | Saldo de apertura 0 y lote inactivo | `T-067-09` | **PASS** — `BR-01` rechaza coherentemente |
| **AC-R67-09** | `BR-01` usa el saldo correcto | `T-067-03` | **PASS** — 400 con la cifra real |
| **AC-R67-10** | La auditoría de la activación se conserva | `T-067-10` | **PASS** |
| **AC-R67-11** | Aislamiento entre empresas | `T-067-11`, `T-067-12` | **PASS** |
| **AC-R67-12** | Regresión completa en verde | suite | **PASS** |

## 6. Las pruebas no son vacías

Dos verificaciones deliberadas, porque un test que pasa igual con y sin el arreglo no
prueba nada:

**`T-067-12`** — retirada la comprobación de pertenencia, falla:

```
AssertionError: con el permiso concedido, la pertenencia dejó pasar la activación
                de un lote ajeno
```

Sin ese test, `T-067-11` habría sido engañoso: pasaba con un `403` por falta de permiso,
que no tiene nada que ver con el aislamiento.

**`T-067-01`** parte de un lote recién creado y comprueba que su saldo es 0 antes de
activar, de modo que el 5 000 posterior sólo puede venir del saldo de apertura.

## 7. Regresión

```
Backend ............ 307 pasados · 49 omitidos · 0 fallos   (108 s)
                     295 antes + 12 nuevas
Instalación limpia . 37/37 pasos     (era 35/37 con R-67 y R-68 abiertos)
Deriva de esquema .. 0
Alembic ............ 1 head · 1 base
TypeScript ......... PASS
Vitest ............. 61/61
Paridad i18n ....... 866 = 866
```

Sin migración: `R-67` no cambia el esquema, sólo cómo se lee.

## 8. Huecos anotados, no resueltos

| ID | Hueco |
|---|---|
| — | Saldo **de huevos y pollitos** de un lote incorporado en producción: `docs/02 §3.9.1` pide «producción acumulada», que no es saldo disponible; el modelo no tiene campo y ninguna fuente lo exige |
| `R-69` | La validación `accumulated_mortality ≤ initial_count` rechaza datos legítimos bajo `RR-08` |
| `R-70` | `activate-manual` devuelve 500 con una fase productiva inexistente |

## 9. Veredicto

```
SALDO DE APERTURA ALIMENTA EL BALANCE ..... sí
SIN HISTORIA FICTICIA ..................... sí
SIN DOBLE CONTEO .......................... sí
BR-01 CON EL SALDO CORRECTO ............... sí
AISLAMIENTO ENTRE EMPRESAS ................ sí, por pertenencia y no por permiso
FULL BACKEND .............................. GREEN

R-67 = CERTIFIED
```
