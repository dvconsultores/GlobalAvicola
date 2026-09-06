# `P-09` · CONTRATO DE CONSULTA DE AUDITORÍA

Fase de análisis · 2026-09-06 · sin desarrollo

---

## 1. Qué filtros exige la norma

`docs/02 §3.11.2` — Vista de Auditoría, prioridad **Alta**:

> **Filtros:** por usuario, lote, fecha, tipo de operación, módulo, estado, documento SAP

Siete. Y `spec.md §4.12` añade, del lado de informes: «Auditoría por usuario / lote /
documento SAP».

## 2. Las tres partes, comparadas

| Capacidad | La interfaz envía | El backend acepta | La norma exige | Estado |
|---|---|---|:--:|---|
| usuario | — | `user_id` | **sí** | backend listo, **la interfaz no lo ofrece** |
| lote | — | `lot_id` | **sí** | ídem |
| fecha | `date_from` `date_to` | `date_from` `date_to` | **sí** | **alineado** |
| tipo de operación | — | `action` | **sí** | backend listo, **la interfaz no lo ofrece** |
| módulo | — | `module` | **sí** | ídem |
| **estado** | — | — | **sí** | **ausente en los dos lados** |
| **documento SAP** | — | — | **sí** | **ausente en los dos lados** |
| granja | — | `farm_id` | no (es un dato registrado, no un filtro exigido) | extra admisible |
| entidad | — | `entity_type` `entity_id` | no | extra admisible |
| **búsqueda libre** | **`search`** | — | **no** | **la interfaz inventa un filtro** |
| **contiene acción** | **`action_contains`** | — | **no** | ídem |
| **agrupación** | **`group_by`** | — | **no** | ídem |

## 3. Lo que ocurre hoy, dicho con precisión

`AuditPage.tsx:45,48,49` construye la petición con:

```ts
if (searchTerm)                  params.set('search', searchTerm)
if (activeTab === 'corrections') params.set('action_contains', 'correct')
if (activeTab === 'by_user')     params.set('group_by', 'user')
```

FastAPI **descarta en silencio** los parámetros no declarados. De modo que:

| Elemento de la interfaz | Lo que el usuario cree | Lo que ocurre |
|---|---|---|
| caja de búsqueda | filtra la auditoría | **no hace nada** |
| pestaña «Correcciones» | muestra solo correcciones | **muestra todo** |
| pestaña «Por usuario» | agrupa por usuario | **muestra todo sin agrupar** |

Esto no es un detalle estético. Un auditor que abre la pestaña «Correcciones», ve una lista
y concluye algo sobre las correcciones **está leyendo otra cosa**. Una vista de auditoría que
aparenta filtrar sin filtrar es peor que no ofrecer el filtro.

## 4. Quién está fuera de contrato

La pregunta de `§22` del encargo —¿manda el frontend o el backend?— la resuelve la norma:

- `user_id`, `lot_id`, `action`, `module`, `date_*` **coinciden con los siete filtros
  normativos**. El backend va bien encaminado; le faltan dos.
- `search`, `action_contains`, `group_by` **no aparecen en ninguna fuente normativa**. Los
  inventó la interfaz.

```
La interfaz está fuera de contrato por partida doble:
  · pide tres capacidades que la norma no define y que nadie atiende
  · no ofrece cuatro que la norma exige y el backend ya sabe atender
```

## 5. Lo que el backend sí hace bien

Los filtros que declara **se aplican de verdad** en la consulta
(`audit/service.py:34-58`), con recuento coherente. **No** es el patrón de `R-47` —aceptar y
descartar—: aquí lo aceptado se usa.

Y `audit_logs` es de solo inserción: no hay un `UPDATE` ni un `DELETE` en toda la aplicación.
La inmutabilidad de `§4.11` se sostiene por construcción.

## 6. Hallazgo

```
R-82 · P1 · la vista de auditoría aparenta filtrar y no filtra. Envía tres parámetros que
            el backend descarta en silencio —búsqueda libre, pestaña de correcciones y
            agrupación por usuario— y no ofrece cuatro filtros normativos que el backend ya
            implementa. Faltan además dos filtros exigidos en ambos lados: estado y
            documento SAP.
```

**Causa distinta de `R-81`.** Aquella es ausencia de emisores; ésta es deriva de contrato
entre dos capas. Se registran por separado, conforme a `§19`–`§21` del encargo.

**Severidad P1**: en un módulo de auditoría, una lista filtrada que no lo está induce a
conclusiones falsas sobre el propio registro de rendición de cuentas.

## 7. Una observación que no se convierte en hallazgo todavía

`audit/service.py:31` filtra siempre por `company_id == self.company_id`, **sin exención para
el Super Admin**. Un Super Admin sin empresa activa (`company_id = None`) vería una auditoría
vacía, lo que choca con `spec.md §8.15` —«Super Admin ve todas las compañías»—.

No se eleva a hallazgo sin comprobarlo en ejecución: se verificará durante la fase de
pruebas y, si se confirma, tendrá su propia entrada.


---

# ESTADO FINAL · tras `GA-REM-032` (2026-09-06)

| Capacidad | Interfaz | Backend | Norma | Estado |
|---|---|:--:|:--:|---|
| usuario | — | `user_id` | sí | backend listo |
| lote | — | `lot_id` | sí | backend listo |
| fecha | `date_from` `date_to` | **corregido** (`R-84`) | sí | **alineado** |
| tipo de operación | **`action`** | `action` | sí | **alineado** |
| módulo | **`module`** | `module` | sí | **alineado** |
| estado | — | **`state`** nuevo | sí | backend listo |
| documento SAP | — | **`sap_reference_id`** nuevo | sí | backend listo |
| búsqueda libre | **retirada** | — | no | **resuelto** |
| contiene acción | **retirada** | — | no | **resuelto** |
| agrupación | **retirada** | — | no | **resuelto** |

```
7 de 7 filtros normativos implementados y aplicados en servidor
0 parámetros inertes
```

## Lo que se retiró de la interfaz, y por qué

Las pestañas «por lote» y «por usuario» no enviaban filtro alguno y mostraban el registro
entero. La de «Correcciones» ahora envía `action=corrected`, que sí acota. La caja de
búsqueda libre se sustituyó por dos desplegables —tipo de operación y módulo— que son
filtros normativos y funcionan.

Retirar un control que nunca filtró no pierde cobertura: la aparentaba.

## `R-84`, descubierto al escribir la prueba de fecha

`created_at >= date_from` comparaba `timestamptz` con texto: **500**. Era el único filtro que
la pantalla enviaba. Corregido con conversión a instante; `date_to` cubre el día completo.
