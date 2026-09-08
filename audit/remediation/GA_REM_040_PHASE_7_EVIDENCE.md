# `GA-REM-040` · FASE 7 · `API` DE ADMINISTRACIÓN POR UNIDAD DE NEGOCIO

`T-040-18` · `T-040-19` · `OD-09.b` · 2026-09-08

```
FASE 7 = COMPLETE
39 pruebas nuevas · 10 mutaciones de sensibilidad · 10 detectadas
REGRESIÓN COMPLETA  687 passed · 49 skipped · 0 failed
SIN MIGRACIÓN · SIN FRONTEND · SIN NUEVO MODELO DE ACL
```

---

## 1. Lo que había que construir, y lo que ya estaba

El esquema de la fase 1 ya sostenía las dos relaciones —`company_business_units` y
`user_business_units`—, el resolutor central ya las leía y `conceder_unidad` ya era el camino
de escritura sancionado. Lo que **no** existía era la forma de administrarlas: la configuración
solo se podía tocar por `SQL` o por semillas.

Por eso esta fase no crea modelo ni migración. Añade seis rutas, un módulo `RBAC` propio y una
capa de servicio que no reimplementa ninguna regla existente.

```
NUEVAS TABLAS      0        el esquema de la fase 1 bastaba
NUEVAS MIGRACIONES 0        head sigue `s9t0u1v2w3x4`
NUEVO MODELO ACL   0        `BusinessUnit` · `CompanyBusinessUnit` · `UserBusinessUnit`
NUEVO RESOLUTOR    0        se usa el de la fase 2
```

---

## 2. El permiso: lo que se decidió y por qué

`GA-REM-040 §5` dice que **el plano de control tiene permisos propios**. Se creó el módulo
`business_units` con cuatro acciones, en lugar de reutilizar `users` o `masters`:

```
users:*     administra personas, no cadenas productivas de la empresa
masters:*   una unidad de negocio no es un maestro
```

Reutilizar cualquiera de los dos habría atado dos autoridades que el propietario puede querer
repartir entre personas distintas — y habría hecho que quien edita un maestro pudiera contratar
una línea de producción.

---

## 3. `AC` → `API` → permiso → regla → prueba → mutación

| `AC` | Superficie | Permiso | Regla de inquilino | Prueba | Mutación |
|---|---|---|---|---|:--:|
| `AC-A02` | `GET /business-units` | `read` | empresa efectiva | `el_listado_muestra_el_catalogo…` | — |
| `AC-A03` | `PATCH …/enable` · `/disable` | `update` | empresa + código | `habilitar_una_unidad_apagada…` · `deshabilitar_apaga…` | `M5` |
| `AC-A04` | `PATCH …/disable` | `update` | ídem | `deshabilitar_no_borra_las_concesiones…` | `M8` |
| `AC-A05` | proyección `is_effective` | `read` | ídem | `el_listado_separa_otorgada_de_efectiva` | — |
| `AC-A06` | rehabilitar | `update` | ídem | `deshabilitar_no_borra…_y_rehabilitar_las_devuelve` | `M8` |
| `AC-A07` | todas | — | nada cruza inquilinos | `habilitar_toca_la_fila_de_la_empresa_propia…` | `M5` |
| `AC-B01` | `POST …/business-units` | `create` | objetivo de la empresa | `conceder_una_unidad_habilitada` | — |
| `AC-B05` | `DELETE …/{code}` | `delete` | ídem | `revocar_retira_el_acceso_de_inmediato…` | — |
| `AC-B07` | `GET /users/{id}/business-units` | `read` | concesiones **bajo** la empresa | `una_concesion_de_la_empresa_anterior_no_se_lista…` | — |
| `AC-B10` | `POST` | `create` | usuario + habilitación | `no_se_concede_a_un_usuario_de_otra_empresa` | `M4` |
| `AC-B11` | `DELETE` | `delete` | — | `revocar…conserva_la_historia` | `M8` |
| `AC-B12` | resolutor | — | — | `volver_a_la_empresa_anterior_no_reactiva…` | — |
| `AC-B04` | resolutor | — | — | `con_las_cuatro_habilitadas_y_cero_concesiones…` | `M7` |
| `AC-F03` | las seis | las cuatro | empresa efectiva | `control_el_administrador_sin_la_unidad_puede_administrarla` | — |
| `AC-F04` | — | — | — | `tratamiento_ese_mismo_administrador_no_ve_dato_productivo` | `M1` |
| `AC-F05` | las seis | las cuatro | — | `llamarse_administrador_no_administra_nada` | `M6` |
| `AC-I03` | enable · disable · grant · revoke | — | — | `…quedan_auditados` (dos pruebas) | `M10` |

---

## 4. La evidencia central de `OD-09.b` es un par, no una prueba

```
CONTROL      ADMIN · `business_units:*` · CERO concesiones de unidad
             → habilita, deshabilita, concede y revoca Incubadora        200 · 201
TRATAMIENTO  el MISMO actor, la MISMA sesión
             → `GET /lots`            no devuelve ningún lote de Incubadora
             → `GET /lots/{id}`       404 con el identificador en la mano
```

Por separado ninguna mitad demuestra nada. «Puede administrar» sería compatible con un permiso
que lo abre todo; «no puede leer» sería compatible con un actor sin ninguna autoridad. Es la
**simultaneidad** lo que se mide, y por eso las dos mitades usan el mismo sujeto (`R-72`).

Y una tercera prueba cierra la puerta por detrás: después de ejercer toda la autoridad
administrativa, el alcance operativo de `ADMIN` sigue siendo `[]`.

---

## 5. Sensibilidad · 10 mutaciones, 10 detectadas

Protocolo: verde → instantánea → **una** mutación → rojo esperado → restaurar solo la
mutación → árbol idéntico al commit → verde dirigido.

| # | Mutación | Prueba que debía romperse | Resultado |
|:--:|---|---|:--:|
| `M1` | el administrador obtiene todas las unidades habilitadas | `tratamiento…` · `administrar_no_cambia…` | **2 failed** |
| `M2` | habilitar concede a todos los usuarios de la empresa | `habilitar_no_concede_la_unidad_a_nadie` | **1 failed** |
| `M3` | conceder habilita la unidad | `conceder_no_habilita_la_unidad…` | **1 failed** |
| `M4` | sin comprobación de empresa del usuario objetivo | `no_se_concede_a_un_usuario_de_otra_empresa` | **1 failed** |
| `M5` | sin comprobación de empresa de la habilitación | `habilitar_toca_la_fila_de_la_empresa_propia…` | **1 failed** |
| `M6` | atajo por nombre de rol en `tiene_permiso` | `llamarse_administrador_no_administra_nada` | **1 failed** |
| `M7` | sin concesiones, devolver todo lo habilitado | `…cero_concesiones_el_alcance_es_vacio` | **1 failed** |
| `M8` | deshabilitar borra las concesiones | `deshabilitar_no_borra…` | **1 failed** |
| `M9` | la ruta deja de declarar `response_model` | `…contrato_de_respuesta` | **1 failed** |
| `M10` | conceder deja de auditarse | `conceder_y_revocar_quedan_auditados` | **1 failed** |

```
APLICADAS 10 / 10      ninguna abortó por ancla ausente
DETECTADAS 10 / 10     ninguna sobrevivió
RESTAURACIÓN           `git status` vacío tras cada ciclo
VERDE DIRIGIDO         39 / 39
```

El guion aborta si el ancla de la mutación no aparece **exactamente una vez**. Es la lección de
la fase 5, donde una mutación no llegó a ejecutarse y no probaba nada: una mutación que no
ocurre no es una mutación que sobrevive.

**`M8` no resuelve `BU-D10`.** Demuestra que hoy la implementación conserva, que es lo que
`AC-A04` exige; no dice qué debe pasar cuando una línea se cierra de verdad.

---

## 6. Lo que la fase encontró y no arregló

### `R-113` · ningún rol administra el acceso por unidad

Lo detectó `test_rbac.py`, que exige que todo permiso reclamado por una ruta lo conceda algún
rol o conste como exclusivo del Super Administrador. Al no haber rol, las cuatro acciones
entraron en `SOLO_SUPER_ADMIN`, y el **segundo** guardián —el que vigila que esa lista no
crezca— saltó con el diagnóstico correcto: falta un rol administrativo.

No se inventó. Ninguna de las cinco figuras sembradas administra accesos, y `business_units:create`
permite conceder a cualquier usuario de la empresa **incluido uno mismo**: dárselo a «Supervisor
Avícola» convertiría a todo supervisor en alguien capaz de concederse las cuatro cadenas.

El tope del guardián se subió de 15 a **17 exactos** —no a un número holgado— con la razón
escrita en su propia docstring, y la pregunta va al propietario. La siguiente adición vuelve a
romperlo, que es para lo que sirve.

### La política vigente permite concederse a uno mismo

`§51` del encargo pedía auditar la política real y **no inventar una excepción si no está
decidida**. No lo está: ni `GA-REM-040` ni `OD-09` separan conceder a otro de concederse a uno
mismo. Queda documentado, probado y auditado con actor y objetivo — que es lo que permite
detectarlo. Restringirlo sería una decisión del propietario.

### Dos aserciones vacías, mías, de la fase 6

`test_pending_classification` tomaba «el último» registro de auditoría de una consulta **sin
`ORDER BY`**. Pasaba por coincidencia del orden físico de las filas en `PostgreSQL`; una suite
nueva que escribiera antes en la misma tabla bastó para romperlo. Corregidas las dos con orden
explícito. Es la tercera vez en este programa que aparece la misma clase de defecto —una
aserción que no comprobaba lo que decía comprobar— y conviene que quede contada.

### Lo que no se tocó

```
R-112     ocho rutas SAP sin `response_model`   sigue registrado, sin remediar
          la lección sí se aplicó: las seis rutas nuevas declaran contrato
BU-D10    PENDING_RATIFICATION · la fase no la resolvió ni la cerró por omisión
P-08      BLOCKED_EXTERNAL · intacto
R-99 · frontend · despliegue · `EX-01`         intactos
```

---

## 7. Regresión

| Suite | Fase | Resultado |
|---|---|:--:|
| `test_business_units.py` | 1 · 1.1 | 31 |
| `test_business_unit_guard.py` | 2 | 25 |
| `test_lot_row_scope.py` | 3 · `R-111` | 21 |
| `test_kpi_scope.py` | 4 | 15 |
| `test_handoff_contract.py` | 5 | 13 |
| `test_sap_transversal.py` | 5 · `OD-12` | 15 |
| `test_pending_classification.py` | 6 | 35 |
| `test_business_unit_admin.py` | **7** | **39** |
| `test_rbac.py` | `P-13` | 21 |
| `test_audit_coverage/query/reports.py` | `P-09` | 23 |

```
SUITES DE FASE   238 passed
BACKEND COMPLETO 687 passed · 49 skipped · 0 failed · 0 error
FRONTEND         0 ficheros `.ts` / `.tsx` modificados
```

---

## 8. Certificación · recalculada, no heredada

```
CERTIFICACIÓN FUNCIONAL              14 / 15    sin cambios
CERTIFICACIÓN DE ACCESO POR UNIDAD    0 / 15    sin cambios
PROCESOS CERTIFICADOS POR LA FASE 7        0
```

La fase 7 es **plano de control**. Administrar quién accede a una cadena no certifica ningún
proceso de negocio: `P-01`…`P-15` siguen exactamente donde estaban. No hay certificación por
fase, ni por endpoint, ni por transitividad.

Y conviene decirlo al revés, que es como se malinterpreta: que ahora exista la `API` para
conceder Incubadora no dice nada sobre si el proceso de incubación respeta la unidad en todas
sus superficies. Eso se mide proceso a proceso, y sigue sin medirse.
