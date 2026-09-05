# CERTIFICACIÓN — P-11 · ACTIVACIÓN MANUAL DE LOTES EXISTENTES

**`GA-REM-016`** · 2026-09-05 · **`CERTIFIED`**

---

## 1. Qué es este proceso

El mecanismo con el que un cliente incorpora los lotes que **ya tiene en marcha** el día que
instala Global Avícola. `docs/02 §3.9` lo marca «Prioridad: Crítica (para implantación)».

No es un proceso más: es el que decide si la primera instalación real puede arrancar con la
operación existente o hay que fingir que todo empieza de cero.

## 2. Estuvo bloqueado por dos defectos, ambos ya certificados

| Hallazgo | Qué impedía | Spec |
|---|---|---|
| `R-67` | el saldo de apertura no alimentaba el balance: el lote incorporado no admitía **ninguna** mortalidad, descarte ni salida | `GA-REM-005`, enmienda |
| `R-47` | la fecha de inicio se descartaba: `BR-06` rechazaba **todo** evento retroactivo | `GA-REM-028` |

Cada uno por separado dejaba el proceso inservible. Ninguno se detectó por la vía habitual:
el primero lo destapó el recorrido de instalación limpia, el segundo la certificación de
`GA-REM-008`.

## 3. La cadena — las seis reglas de `docs/02 §3.9.2`

| # | Regla | Resultado |
|--:|---|---|
| 1 | El lote queda marcado como «activado manualmente» | **PASS** — `activation_type = manual` |
| 2 | Se audita usuario, fecha, motivo y datos cargados | **PASS** |
| 3 | Se adjunta soporte documental | **PASS** |
| 4 | Se evita el doble conteo | **PASS** — histórico no restado; activación rechazada si el lote ya opera |
| 5 | Se puede continuar la operación desde el saldo inicial | **PASS** — mortalidad retroactiva aceptada |
| 6 | Se genera el reporte de apertura | **PASS** |

## 4. La prueba temporal

El caso central representa un lote real a mitad de ciclo, y comprueba que las tres marcas
temporales permanecen separadas:

```
start_date  = hace 140 días    inicio del ciclo, según el negocio
created_at  = hoy              alta en el software
activación  = evento auditado  quién, cuándo, con qué motivo
```

Y que la consecuencia funcional se cumple: **una mortalidad fechada hace 30 días se
acepta**. Antes de `R-47`, `BR-06` la rechazaba porque el lote «empezaba hoy». Es la
diferencia entre poder incorporar un lote en marcha y no poder.

## 5. Saldo de apertura, sin historia falsa

```
apertura declarada .......... 5 000 aves
histórico acumulado ......... 200 bajas + 50 descartes  (no se restan · RR-08)
mortalidad registrada ....... 25
saldo resultante ............ 4 975
```

Comprobado por el rechazo de una mortalidad de 4 976 con el saldo real en el mensaje. **No
se genera ningún evento histórico** para cuadrar cifras: solo se declara lo que había.

## 6. Aislamiento — con el sujeto correcto

El primer intento midió lo que no debía: usaba un Super Administrador, que `activate_manual`
exime del filtro por compañía **a propósito**. Un pase ahí no habría probado nada.

Se construyó el sujeto adecuado por API: un rol nuevo con `lots:create` y un usuario
**acotado a la empresa B** con ese rol.

```
CONTROL      activa el lote de SU empresa      → 201
TRATAMIENTO  el mismo cuerpo, lote ajeno       → denegado
```

Con el permiso funcional concedido, la única razón posible de la denegación es la
pertenencia. Es la lección de `T-067-11` y de `R-72`, aplicada donde importa.

## 7. Validez de la evidencia

`6 / 6` casos, todos atraviesan el filtro de `PROCESS_E2E_VALIDITY_MATRIX.md`.

Sensibilidad demostrada mutando los tres elementos centrales —la fecha declarada, la guarda
de doble conteo y la comprobación de pertenencia— más el saldo de apertura: **tres casos
fallaron**, y los otros tres siguieron pasando porque no dependen de ellos. Código revertido
en el acto.

| Caso | Tipo | Válido |
|---|---|:--:|
| CADENA COMPLETA · seis reglas | happy path + persistencia + estado derivado + auditoría | **sí** |
| Un lote que ya opera no se activa | negative · doble conteo | **sí** |
| No se activa dos veces | negative | **sí** |
| Sin sesión no se alcanza | authorization | **sí** |
| Rol sin permiso no activa | RBAC · control y tratamiento | **sí** |
| No se activa el lote ajeno | aislamiento · control y tratamiento | **sí** |

## 8. Lo que queda anotado

| Hallazgo | Por qué no bloquea |
|---|---|
| `R-69` · la validación `accumulated ≤ initial` rechaza datos legítimos | caso límite: un lote con más bajas acumuladas que aves vivas. La cadena principal no lo atraviesa |
| `R-70` · 500 con una fase productiva inexistente | robustez de entrada, no semántica del proceso |
| `R-73` · el cierre de lote responde 500 | `lot_closure` no forma parte de esta cadena |

Los tres siguen abiertos en `GA-REM-019`. Ninguno se cierra por conveniencia.

## 9. Veredicto

```
P-11 = CERTIFIED
```

Con la cadena completa de su spec, no por capacidad aislada.
