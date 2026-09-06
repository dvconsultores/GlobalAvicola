# `P-09` · AUDITORÍA INTERNA — INFORME DE CERTIFICACIÓN

`spec.md §4.11` · `docs/02 §3.11` · `GA-REM-032` · 2026-09-06

```
P-09 = CERTIFIED
R-81 = CERTIFIED   R-82 = CERTIFIED   R-84 = CERTIFIED   R-83 = OPEN (§8)
```

---

## 1. Una corrección de partida

El encargo trataba `AC13` como el catálogo de lo auditable. **No lo es**: `AC13` es la
enmienda F de `GA-REM-016` —escrita el día anterior— y dice que toda prueba invocada como
evidencia debe poder fallar. Se ha aplicado a este tramo, pero quien responde «qué debe
auditarse» es `docs/02 §3.11` y `spec.md §4.11`.

## 2. El alcance, medido y no supuesto

El encargo daba «6 de 21 acciones emitidas». **Eran 12.** Solo existen dos escritores
—`audit/listeners.py` y `audit/helpers.py`— y se enumeraron sus valores; las otras nueve no
aparecían fuera de la definición del enum, comprobado una por una.

Y **21 valores del enum no son 21 requisitos**:

| | |
|---|---|
| Obligatorias por `§3.11.1` | **19** |
| Fuera por no tener superficie que auditar | **2** — `CONFIG_CHANGE` (no hay configuración) y `LOGOUT` (no hay endpoint de cierre de sesión; el token se descarta en el cliente) |
| Emitidas antes | 12 |
| **Emitidas ahora** | **19 de 19** |

Las dos exclusiones se documentan en vez de implementarse: auditar algo que no ocurre no es
cobertura, es decorado. Si algún día existen esas superficies, vuelven a la lista.

## 3. `R-81` · seis módulos sin un solo registro

Los listeners vigilan tres tipos de modelo, de modo que de los once módulos declarados en
`AuditModule`, seis no producían nada: `auth`, `masters`, `lots`, `users`, `config`,
`reports`. Ocho acciones obligatorias no se escribían nunca, entre ellas **el intento de
acceso fallido** y **el cambio de permisos** — las primeras que un auditor busca.

**P1 y no P2**: un cambio de permisos sin rastro deja sin respuesta «quién concedió esto».

## 4. `R-82` · una vista que aparentaba filtrar

`AuditPage` enviaba `search`, `action_contains` y `group_by`. FastAPI descarta en silencio
lo no declarado, así que **la caja de búsqueda no buscaba, la pestaña «Correcciones» mostraba
todo y la de «Por usuario» no agrupaba**. Ninguno de los tres aparece en fuente normativa:
los inventó la interfaz.

Mientras tanto faltaban dos de los siete filtros que `§3.11.2` exige —**estado** y
**documento SAP**— y la interfaz no ofrecía cuatro que el backend ya atendía.

Quien estaba fuera de contrato era la interfaz, y se resolvió por norma, no por comodidad.

## 5. `R-84` · el único filtro que la interfaz enviaba devolvía 500

Apareció al escribir la prueba de fecha: `created_at >= date_from` comparaba una columna
`timestamptz` con una cadena y PostgreSQL respondía *«operator does not exist»*. Es decir,
**la fecha —el único filtro que la pantalla mandaba— rompía la vista**.

Se convierte a instante antes de comparar, y `date_to` cubre el día entero, que es lo que un
auditor espera al escribir una fecha.

## 6. La cadena, paso a paso

| # | Paso | Estado | Evidencia |
|:--:|---|:--:|---|
| 1 | alta de evento operativo | PASS | ya cubierto |
| 2 | transiciones de estado | PASS | ya cubierto |
| 3 | correcciones | PASS | ya cubierto |
| 4 | envío a SAP | PASS | ya cubierto |
| 5 | **acceso al sistema** | **PASS** | `AC01` · `test_t_081_01/02` · E2E |
| 6 | **maestros y lotes** | **PASS** | `AC02` · `test_t_081_03` · E2E |
| 7 | **cambio de permisos** | **PASS** | `AC03` · `test_t_081_04` · E2E |
| 8 | **importación y exportación** | **PASS** | `AC04` · `test_t_081_06` |
| 9 | **cierre de revisión** | **PASS** | `AC05` · `test_t_081_05` |
| 10 | inmutabilidad | PASS | sin `UPDATE` ni `DELETE` sobre `audit_logs` |
| 11 | visor para roles autorizados | PASS | `AC13` · `test_t_082_11` · E2E |
| 12 | **filtros de la vista** | **PASS** | `AC09` `AC10` · 9 pruebas · E2E |
| 13 | aislamiento entre empresas | **PASS** | `AC12` · `test_t_082_10` |
| 14 | contenido del registro | **PASS** | `AC06` `AC07` · actor, módulo, entidad, fecha |

```
14 pasos · PASS 14 · FAIL 0 · BLOCKED 0
```

## 7. Una decisión de arquitectura que hubo que tomar explícitamente

El registro de `LOGIN_FAILED` se escribía y **el 401 lo revertía**: la petición fallida
arrastra un `rollback` (`GA-REM-026`).

`§43` del encargo advertía de no elegir por comodidad. La norma decide: si el único rastro
de un intento de acceso fallido desaparece con el propio fallo, no hay auditoría. Se confirma
ese registro —y solo ése— antes de propagar el 401, porque en esa rama no hay ninguna otra
escritura pendiente. El resto de emisiones siguen el patrón vigente y viajan en la
transacción del negocio.

## 8. Una limitación que queda abierta, no escondida

```
R-83 · P2 · abierto
```

`AuditLog.company_id` **no es nulable**. Las acciones que no pueden atribuirse a ninguna
empresa —un intento de acceso con un usuario inexistente, o el login de un Super Admin sin
contexto— **no pueden auditarse**.

Se prefirió dejarlo visible antes que hacer nulable la columna: la consulta filtra por
`company_id`, así que esos registros existirían sin que ninguna consulta pudiera
recuperarlos. Sería una auditoría que nadie puede leer, que es peor que su ausencia
declarada.

El caso relevante para seguridad —**el ataque contra una cuenta que existe**— sí queda
registrado.

## 9. Evidencia

### Fase roja, antes de tocar la aplicación

| Prueba | Resultado con el código anterior |
|---|---|
| `test_t_081_01`…`06` | **6 fallan** — «el registro no existe», no por autenticación ni fixture |
| filtro por estado · documento SAP | **fallan** — el parámetro no existía |
| filtro por fecha | **500** — `operator does not exist` |

### Puerta de sensibilidad

| Mutación | Efecto | Restaurado |
|---|---|:--:|
| se desactiva la emisión genérica | **6 de cobertura fallan**; las 11 de consulta siguen verdes | 17/17 |
| se desactiva el filtro por estado | **1 falla** | 17/17 |
| se revierte la conversión de fecha | **1 falla** | 17/17 |

Cada mutación golpea exactamente lo suyo. `git diff` tras revertir: solo lo previsto.

Que las pruebas de consulta sobrevivan a la mutación de emisión es deliberado: insertan sus
registros directamente, porque miden la **consulta** y mezclarlas con la emisión habría
hecho que un fallo no dijera cuál de las dos falló.

### Regresión

| | Antes | Después |
|---|---|---|
| Backend | 335 · 49 omitidas | **352 · 49 omitidas · 0 fallos** |
| E2E | 85/85 | **91/91** |
| `tsc` | — | **PASS** |
| `vitest` | 61/61 | **61/61** |
| Paridad i18n | 866 = 866 | **866 = 866** |

## 10. Modalidad de la evidencia

`API_E2E` de proceso, conforme a `GA-REM-016 AC05`. `§3.11` no exige comportamiento visible
para ninguna de sus reglas, así que **no se fabricaron pruebas de interfaz** por vocabulario.
El cambio en `AuditPage` se verifica por revisión del diff y `tsc`, que es lo que `AC11` pide.

## 11. Veredicto

```
P-09 = CERTIFIED     ·     19 de 19 acciones obligatorias · 7 de 7 filtros normativos
```
