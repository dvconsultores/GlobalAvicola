# MATRIZ DE BLOQUEANTES DE LOS PROCESOS `PARTIAL`

**`GA-REM-016`** · 2026-09-05 · análisis de alcance previo a elegir el siguiente frente

---

## 1. Estado de partida, verificado

```
15 procesos · 5 CERTIFIED · 10 PARTIAL · 0 READY_FOR_E2E
```

El encargo hablaba de **9** `PARTIAL`. La matriz dice **10**: `P-08` figura como `PARTIAL`
con bloqueo externo, no como una categoría aparte. Se usa el número real.

| Estado | Procesos |
|---|---|
| `CERTIFIED` | `P-02` · `P-04` · `P-05` · `P-07` · `P-11` |
| `PARTIAL` | `P-01` · `P-03` · `P-06` · `P-08` · `P-09` · `P-10` · `P-12` · `P-13` · `P-14` · `P-15` |

## 2. Una advertencia sobre la fuente

Los huecos por proceso vienen de `audit/06_PROCESS_COVERAGE.md`, escrito **antes** de las
Waves 1–3. Varios ya no existen y contarlos habría falseado el análisis. Se verificaron uno
a uno contra el código actual:

| Hueco del audit | Estado hoy |
|---|---|
| `mortality_recording` devuelve 500 (`P-01`, `P-03`, `P-06`) | **resuelto** — `P0-1` / `GA-REM-005` `CERTIFIED` |
| `LotDetailPage` rota (`P-03`, `P-06`, `P-10`) | **resuelto** — `FE_BE_CONTRACT_MATRIX C-03 CORREGIDO` |
| Corrección no aplica el valor (`P-07`) | **resuelto** — `RC-01` / `GA-REM-006` |
| `BR-14` eludible por `POST /review/complete` (`P-07`) | **resuelto** — `GA-REM-007` |
| Permisos «sin enforcement» (`P-13`) | **resuelto** — `GA-REM-002` |

Sin esta depuración, `LotDetailPage` habría parecido un bloqueante de fan-out 3.

## 3. La matriz

| Bloqueante | Spec | Sev. | Procesos afectados | AC que impide | Fan-out | ¿Funcional? | ¿Solo de test? |
|---|---|:--:|---|---|:--:|:--:|:--:|
| **`GA-TD-014`** · la OC SAP se guarda en `extra_data.sap_order_ref` y no en `sap_document_ref`; `BR-11` y `BR-18` quedan inertes y `validate_oc_limit` nunca se dispara | `GA-REM-010` · `C-15` **`DIFERIDO`** | **P1** | `P-01` · `P-03` · `P-06` | `VALIDATION` de la recepción contra la orden de compra | **3** | sí | no |
| **`R-73`** · `POST /lots/{id}/close` responde 500 siempre; el modelo de respuesta de la ruta no encaja con el resumen del servicio | ninguna | **P1** | `P-06` | el paso `lot_closure` de su cadena | **1** | sí | no |
| **`R-60`** · la trazabilidad automática busca el evento complementario con el **mismo** `lot_id`, de modo que nunca encuentra el par | `GA-REM-008` | P2 | `P-10` | el modo automático del proceso | **1** | sí | no |
| **`GA-TD-0xx`** · 8 de 19 maestros no registran `PUT`; `MasterListPage` lo emite para todos → `405` | — | P1 | `P-12` | edición de maestros | **1** | sí | no |
| Cobertura de auditoría: 6 de 21 acciones del enum se escriben; `AuditPage` envía parámetros que el backend no admite | — | P2 | `P-09` | registro de login, permisos, maestros e importación/exportación | **1** | sí | no |
| Notificaciones: 5 de 6 tipos exigidos no existen, y **no hay canal** (correo, push, Telegram) | `GA-REM-019` | P1 | `P-14` | el proceso entero | **1** | sí | no |
| `P-13`: roles y permisos **sin pantalla** | — | P2 | `P-13` | gestión por interfaz | **1** | sí | no |
| 4 KPI huérfanos; los KPI son cero hasta aprobar y la interfaz no lo explica | — | P2 | `P-15` | — (documental) | **1** | parcial | no |
| Alerta de peso fuera de curva (`GA-REQ-037`) | backlog | P2 | `P-01` · `P-14` | alerta de peso | 2 | sí | no |
| **`GA-REM-017`** · SAP real | `GA-REM-017` | — | `P-08` | envío real | 1 | — | `BLOCKED_EXTERNAL` |
| `R-69` · la validación del saldo de apertura rechaza datos legítimos | `GA-REM-019` | P2 | **ninguno** | caso límite de `P-11`, ya certificado | **0** | sí | no |
| `R-70` · 500 con una fase productiva inexistente | `GA-REM-019` | P2 | **ninguno** | robustez de entrada | **0** | sí | no |

### `R-69` y `R-70`, evaluados como exige el encargo

```
R-69 bloquea: ninguno
R-70 bloquea: ninguno
```

`P-11` está certificado y su cadena no atraviesa ninguno de los dos. **No se cierran por
eso**: siguen abiertos en `GA-REM-019` con su estado real.

## 4. La hipótesis, contrastada

El encargo proponía `R-73` como el de mayor impacto, «por tratarse del cierre de lote y
potencialmente afectar varias cadenas».

**La evidencia no lo sostiene.** `lot_closure` figura como paso obligatorio en **un solo
proceso**: `spec.md §4.8 Broiler / Fattening`, es decir `P-06`. `audit/06` lo confirma:
«P-06 · igual que P-03 más `lot_closure`». Ninguna otra cadena lo incluye.

```
R-73 fan-out = 1
```

El de mayor alcance es **`GA-TD-014`**, con **3**.

## 5. Por qué no se elige el de mayor fan-out

`GA-TD-014` está **deliberadamente diferido**, y la razón consta en
`FE_BE_CONTRACT_MATRIX C-15`:

> enviarlo **activa `BR-11` y `BR-18`**, que hoy están inertes. Es un cambio de
> comportamiento de negocio que puede bloquear registros de operadores. Requiere coordinarse
> con `GA-REM-010` y con la decisión de `RC-07`.

`RC-07` sigue `OWNER_DECISION_REQUIRED`. Elegirlo significaría **activar dos reglas de
negocio que hoy no se aplican**, sin autoridad para decidirlo y reabriendo una decisión ya
tomada. No es una cuestión técnica.

```
GA-TD-014 = fan-out 3 · BLOQUEADO POR DECISIÓN DEL PROPIETARIO (RC-07)
```

Queda como **el siguiente frente de mayor palanca en cuanto esa decisión exista**, y es lo
que conviene preguntar al propietario.

## 6. Selección

```
SELECTED_NEXT_BLOCKER = R-73
```

**Motivo.** Entre los bloqueantes *accionables* —los que no dependen de una decisión
pendiente— todos tienen fan-out 1, así que decide el criterio siguiente del encargo:
corrección y daño sobre el ciclo de vida.

`R-73` es el único que deja un endpoint devolviendo **500 siempre**: el cierre de lote nunca
ha funcionado. Es el paso terminal del ciclo productivo, y `BR-05` existe precisamente para
gobernarlo. Los demás son huecos de cobertura o de interfaz, no un camino roto.

Se elige, por tanto, **por corrección y criticidad de ciclo, no por fan-out** — y eso se
dice explícitamente para que nadie lea después que se eligió por alcance.

## 7. Lo que este análisis deja preparado

| Frente | Fan-out | Estado |
|---|:--:|---|
| `GA-TD-014` | 3 | espera decisión de `RC-07` — **mayor palanca disponible** |
| `R-73` | 1 | **seleccionado ahora** |
| `P-12` maestros sin `PUT` | 1 | accionable, sin dependencias |
| `P-09` cobertura de auditoría | 1 | accionable |
| `R-60` trazabilidad automática | 1 | accionable, `GA-REM-008` |
| `P-14` notificaciones | 1 | requiere canal: es desarrollo nuevo, no una corrección |
| `P-08` SAP real | 1 | `BLOCKED_EXTERNAL` |
