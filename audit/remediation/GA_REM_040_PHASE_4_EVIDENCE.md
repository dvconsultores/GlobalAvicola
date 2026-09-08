# `GA-REM-040` FASE 4 · AGREGADOS Y KPI · EVIDENCIA

2026-09-07 · `T-040-11` · `T-040-12`

```
LO QUE NO SE PUEDE VER COMO FILAS
NO PUEDE REAPARECER COMO TOTAL
```

---

## 1. La forma del riesgo no era la que se suponía

El encargo señalaba `/api/v1/reports/kpis/mortality` como un agregado de empresa. **No lo es.**

```
@router.get("/kpis/mortality")
async def get_mortality_kpi(lot_id: int = Query(...))     ← obligatorio
```

Casi todos los indicadores de `P-15` son **por lote**. No sumaban la compañía, y lo que hacían
era distinto —y peor de lo que parecía—: devolver el detalle de **cualquier** lote cuyo
identificador alguien conociera.

```
usuario de Reproductora  ·  GET /kpis/mortality?lot_id=<lote de Incubadora>

    200 OK
    {"initial_population": 1000, "total_deaths": 7, "mortality_rate_pct": 0.7}
```

Es más de lo que el listado de la fase 3 ocultaba: población inicial, muertes y tasa, servidas
en una sola llamada.

**Los agregados de empresa de verdad son otros**, y ahí estaba la fuga de manual.

## 2. Inventario de superficies

| Superficie | Forma | Fuente | Clase | Estado |
|---|---|---|:--:|:--:|
| `/kpis/mortality` · `feed-conversion` · `egg-production` · `animal-welfare` · `vaccination-efficiency` · `transfer-efficiency` · `afcr` · `production-index` | por lote (`Query` obligatorio) | eventos del lote | `A` operativa | **ACOTADA** |
| `/kpi/ipe/{lot_id}` · `/kpi/weight-uniformity/{lot_id}` · `/reports/lot/{lot_id}` | por lote (ruta) | ídem | `A` | **ACOTADA** |
| `/kpis` · `/kpis/hatchery` · `/reports/sap-comparison` | lote **opcional** | eventos | `A` | **ACOTADA** |
| `/dashboard/admin` · `/dashboard/mobile` — `lots_by_type` | agrupado por cadena | `lots` | `A` | **ACOTADA** |
| `/dashboard/*` — contadores, `top_event_types`, `last_7_days`, tendencia, alertas | agregados de empresa | `operational_events` | `A` | **ACOTADA** vía lote |
| exportaciones `CSV` · `XLSX` · `PDF` | — | — | — | **no existen** como ruta propia |

```
SUPERFICIES REVISADAS     16
ACOTADAS                  16
CONTROL COMPANY-WIDE       0     no se implementa ninguna vista de control en esta fase
APLAZADAS                  0     ninguna quedó fuera
```

**No se implementa vista de control.** `OD-09.a` permite a contraloría visibilidad transversal,
pero **por política explícita**, y esta fase no la construye: hacerlo requeriría decidir qué
superficies la ofrecen, que es diseño de producto. Mientras tanto, contraloría ve lo que su
concesión le da — que es lo conservador y no rompe nada.

## 3. Arquitectura

```
unidades efectivas (fases 1.1 y 2)
        ↓
lotes_alcanzables(empresa, unidades)        una subconsulta, no un JOIN por indicador
        ↓
CONJUNTO AUTORIZADO  →  AGREGAR
```

**Nunca al revés.** Agregar la compañía entera y descontar lo ajeno deja el total correcto y el
camino abierto: cualquier consulta que se olvide del descuento vuelve a filtrar. Y todo se
resuelve en la base, no en memoria.

Se reutilizan `unidades_efectivas_por_id` (fase 1.1) y `predicado` (fase 3). **No hay un motor
de autorización propio de los indicadores.**

### 3.1 El evento sin lote

```
un evento sin `lot_id` NO contribuye a ningún agregado
```

Misma decisión que la fase 3 tomó con el lote sin cadena declarada: `OD-10.c` manda lo no
clasificable a «pendiente de clasificar», que es la fase 6. Hasta entonces lo seguro es que no
sume. **Queda declarado, no es efecto colateral**, y es fail-closed: la alternativa —que un
evento sin cadena cuente para todos— sería la puerta abierta.

## 4. La fuga de dimensión

El caso de libro, y estaba vivo:

```json
"lots_by_type": {"BirdTypeEnum.BREEDER": 3, "BirdTypeEnum.HATCHERY": 5}
```

Ninguna fila de incubadora se devuelve, y sin embargo el panel **dice que existe y cuántos hay**.
Acotar el total y dejar la dimensión suelta no protege nada: se filtran los grupos en la
consulta.

## 5. Las fórmulas de `P-15` no se tocan

```
numerador · denominador · semántica de aprobación · redondeo · fecha de negocio
```

Sin cambios. El alcance por unidad se aplica **además**, no en lugar. Se comprueba con valores
exactos: un lote con 10 muertes aprobadas y 500 pendientes de revisión sigue devolviendo 10.

```
P-15  FUNCIONALMENTE CERTIFICADO   sin cambios
```

### 5.1 Una observación al pasar

Al buscar la suite de `P-15` para la regresión apareció que **ninguna prueba existente cubría
el indicador de mortalidad por su endpoint**: el único fichero que lo toca es el de esta fase.
No se corrige aquí —`P-15` está funcionalmente certificado por otras vías y reabrirlo no es de
esta fase— pero se deja registrado.

## 6. Trazabilidad

| Comprobación | Prueba | Estado |
|---|---|:--:|
| **`CONTROL`** · indicador propio, con valores exactos | `test_el_kpi_del_lote_propio_funciona` | **PASS** |
| **`TRATAMIENTO`** · indicador de otra cadena | `test_el_kpi_de_un_lote_de_otra_cadena_es_inalcanzable` | **PASS** |
| Usuario de dos cadenas alcanza ambos | `test_el_usuario_de_dos_cadenas_alcanza_los_dos_kpi` | **PASS** |
| Usuario sin unidades | `test_el_usuario_sin_unidades_no_alcanza_ningun_kpi` | **PASS** |
| Otra empresa | `test_el_kpi_de_otra_empresa_sigue_siendo_inalcanzable` | **PASS** |
| Unidad apagada por la empresa | `test_apagar_la_unidad_retira_su_kpi` | **PASS** |
| Los otros siete indicadores con `Query` | `test_los_demas_kpi_por_lote_tambien_se_acotan` | **PASS** |
| Los tres con lote en la ruta | `test_los_kpi_por_ruta_con_lote_tambien` | **PASS** |
| Fuga de dimensión en el panel | `test_el_panel_no_revela_las_cadenas_ajenas_como_grupo` | **PASS** |
| Panel de dos cadenas (control) | `test_el_panel_del_usuario_de_dos_cadenas_las_muestra` | **PASS** |
| Panel sin unidades | `test_el_panel_del_usuario_sin_unidades_no_muestra_ninguna` | **PASS** |
| Contadores de evento acotados | `test_los_contadores_del_panel_no_cuentan_eventos_ajenos` | **PASS** |
| Contadores con cero unidades | `test_el_panel_del_usuario_sin_unidades_no_cuenta_eventos` | **PASS** |
| El nombre del rol no amplía | `test_llamarse_contralor_no_amplia_el_agregado` | **PASS** |
| La regla de aprobación sobrevive | `test_el_filtro_de_seguridad_no_altera_la_regla_de_aprobacion` | **PASS** |

```
PRUEBAS DE LA FASE 4     15 / 15
```

Con **valores discriminantes** —10 frente a 7—: si las dos cadenas tuvieran el mismo número, una
fuga daría el mismo total con filtro y sin él, y la prueba no probaría nada.

## 7. Sensibilidad

| # | Mutación | Resultado | Cayeron |
|:--:|---|:--:|:--:|
| 1 | quitar el alcance del indicador | **RED** | 7 |
| 2 | usar todas las unidades **habilitadas** en vez de las concedidas | **RED** | 5 |
| 3 | sin unidades → toda la empresa | **RED** | 2 |
| 4 | el grupo del panel vuelve a nombrar lo ajeno | **RED** | 3 |
| 5 | quitar el filtro de inquilino | **RED** | 1 |
| 6 | atajo por nombre de rol | **RED** | 1 |
| 7 | el panel deja de acotar sus contadores | **RED** | 2 |
| 8 | romper la semántica de aprobación de `P-15` | **RED** | 3 |

### 7.1 Dos mutaciones encontraron huecos de cobertura

Como en la fase 3, y conviene registrarlo:

**La 7 no rompió nada al principio.** El acotamiento de los contadores del panel estaba puesto,
pero ninguna prueba lo sujetaba. Se añadieron
`test_los_contadores_del_panel_no_cuentan_eventos_ajenos` y su variante de cero unidades.

**La 8 no tenía contra qué correr.** `tests/test_kpis.py` no existe, y ninguna suite cubría la
mortalidad por su endpoint. Se añadió un registro **sin aprobar** a la fixture —500 muertes
pendientes sobre un lote con 10 aprobadas— y la prueba que exige que el indicador siga diciendo
10. Sin ella, una implementación que sustituyera el filtro de estado por el de unidad habría
pasado desapercibida multiplicando el indicador por cincuenta.

```
MUTACIONES        8 / 8 detectadas
RESTAURACIÓN      los tres ficheros idénticos a su instantánea
PATRONES          seis comprobaciones positivas · 14 guardas de lote · 0 menciones a role_name
```

## 8. Regresión

```
BACKEND                  585 passed · 49 skipped     (eran 570)
P-15 FUNCIONAL           verde · fórmulas y aprobación intactas
FASE 3                   verde · filas, detalle, mutaciones, sub-recursos
FASE 2                   verde · empresa efectiva, guarda, clasificación
FASE 1 + 1.1             verde
INQUILINO · `R-111`      verde
RBAC                     verde
MIGRACIÓN                ninguna · FRONTEND 0 archivos
```

## 9. Lo que **no** se ha logrado

```
CONTRATOS DE TRASPASO              NO IMPLEMENTADOS   fase 5
DESTINO DEL DESPACHO               NO IMPLEMENTADO    fase 5
CLASIFICACIÓN PENDIENTE            NO IMPLEMENTADA    fase 6
VISTA DE CONTROL TRANSVERSAL       NO IMPLEMENTADA    requiere diseño de producto
EVENTOS SIN LOTE                   NO CONTRIBUYEN     dependencia declarada de la fase 6
```

```
FILA ACOTADA   ≠   AGREGADO ACOTADO   ≠   CONTRATO ENTRE UNIDADES
```

Las dos primeras están; la tercera no ha empezado.

## 10. Certificación

```
CERTIFICACIÓN FUNCIONAL              14 / 15   sin cambios
CERTIFICACIÓN DE ACCESO POR UNIDAD    0 / 15   sin cambios
```

**Ningún `PASS`, tampoco para `P-15`.** Sus quince indicadores quedan acotados, y eso no
certifica el proceso: `P-15` consume eventos operativos, que dependen de la fase 6, y los
indicadores de traspaso, que dependen de la fase 5. Certificar por endpoint es exactamente lo
que `GA-REM-016 AC05` prohíbe — la unidad de certificación es el **proceso**.

## 11. Siguiente

```
GA-REM-040 · FASE 5 — CONTRATOS DE TRASPASO ENTRE UNIDADES     T-040-13 … T-040-15
NO INICIADA
```
