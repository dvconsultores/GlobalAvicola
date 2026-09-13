# R-221 · SPEC — DERIVACIÓN DE UNIDAD EN EVENTOS SIN LOTE (INSPECCIONES) Y GUARDA DE ESCRITURA ESTRICTA

Fecha: 2026-09-13 · Hallazgo canónico: **R-221** (P2 · bloquea) · HEAD `c0b4afc` · Origen registro G-34 · Secciones §47.

## 1 · Contexto

`POST /operations` acepta tres tipos sin lote (`service.py:61-68`). La importación de abuelas deriva su unidad del tipo (R-153 C2b). Las inspecciones no: nacen `business_unit_id=null` y la guarda de escritura (`exigir_unidad_operativa`) degrada a «alguna unidad». Resultado: `hatchery_inspection` registrable con `hatchery` apagada o sin concesión.

## 2 · Evidencia

`R-221_FINDING.md §1`: `service.py:61-68,185-197,242-246`; `business_units/service.py:278-290`; `classification.py:65-113`; runtime `OD16b-global-actor-bu-off-api` (201 con hatchery OFF, restaurada).

## 3 · Causa raíz

Derivación por tipo puntual (importación) no generalizada; `unidad=None` en la guarda como «alguna unidad» en vez de exigir la unidad real del tipo inequívoco; `farm_inspection` (tipo ambiguo) sin regla decidida.

## 4 · Impacto de negocio

Escritura productiva fuera de la unidad habilitada/concedida (violación OD-16.e/OD-09); eventos mal clasificados en la bandeja; dependencia de una guarda laxa para tipos de cadena inequívoca.

## 5 · Comportamiento actual

| Caso | Hoy | Esperado |
|---|---|---|
| Global situada; `hatchery` OFF; `hatchery_inspection` sin lote | **201** (unidad null; «alguna habilitada») | **403/400** — la unidad del tipo (`hatchery`) está apagada |
| Actor con concesión solo `broiler`; `hatchery_inspection` | **201** (efectivas no vacío) | **denegado** (sin concesión `hatchery`) |
| Actor con `hatchery`; `hatchery_inspection` | 201, `business_unit_id=null` | 201 con `business_unit_id=hatchery` |
| `farm_inspection` sin lote | 201, `business_unit_id=null`; va a clasificación | regla decidida (C-02): derivar de granja/galpón declarado **o** mantener clasificación previa |

## 6 · Comportamiento esperado

1. **Derivación por tipo inequívoco** en el alta: `hatchery_inspection` ⇒ `business_unit_id = hatchery` (patrón `unidad_directa` de `grandparent_import`). El conjunto de tipos inequívocos se declara explícitamente (hoy: `grandparent_import` → grandparent; `hatchery_inspection` → hatchery).
2. **Guarda estricta**: con unidad derivada, `exigir_unidad_operativa` exige **esa** unidad (apagada o sin concesión ⇒ denegado), también para la autoridad global (OD-16.e).
3. **`farm_inspection` sin lote** (decisión C-02, por defecto propuesto): derivar la unidad de la granja/galpón declarados **si** la granja declara cadena única; si no, mantener clasificación previa (bandeja) y exigir «alguna unidad» como hoy — documentado. El propietario puede decidir «exigir clasificación previa siempre».
4. Regresión: `grandparent_import` intacto (R-153); eventos con lote intactos (la derivación por lote manda).

## 7 · Alcance

- `backend/app/operations/service.py`: generalizar `unidad_directa` (declarar tipos inequívocos); sin cambiar la firma pública del alta.
- `backend/app/business_units/service.py`: sin cambio de resolutor (la guarda ya recibe `unidad`); se documenta la semántica estricta cuando `unidad` viene derivada.
- Tests: `backend/tests/test_r221_unit_derivation_no_lot.py` (nuevo) + extensión de `test_operations_bu_enforcement.py` (W-xx sin lote) y `test_pending_classification.py` (caso `farm_inspection`).
- Sin migración; sin endpoints; sin permisos nuevos.

## 8 · Fuera de alcance

- `classification.py` (reclasificación): sin cambio salvo lo que C-02 decida para `farm_inspection`.
- Frontend: el asistente ya ofrece los tipos sin lote; los mensajes de denegación se renderizan como hoy (R-189).
- Otros tipos del catálogo: solo los de `LOT_OPTIONAL_EVENTS`.

## 9 · Impacto frontend

Ninguno de contrato. El caso denegado se muestra como los demás 400/403 (texto vía `getErrorMessage`). Regresión UI: registrar `hatchery_inspection` legítimo (con hatchery ON y concedida) sigue en 201.

## 10 · Impacto backend

`operations/service.py` (derivación por tipo + guarda estricta). Sin cambios en modelos.

## 11 · Contrato frontend↔backend

Mismo `POST /operations`. Cambia el resultado para el actor sin la unidad del tipo (201→denegado) — corrección de seguridad. El evento legítimo nace con `business_unit_id` poblado (mejor dato; la bandeja de clasificación deja de recibirlo en tipos inequívocos).

## 12 · Impacto en datos

Sin migración. Los eventos históricos con `business_unit_id=null` de estos tipos permanecen (no se reescriben). Decisión C-02 puede implicar que `farm_inspection` siga naciendo null (bandeja) — documentado.

## 13 · Seguridad

Cierra la escritura fuera de unidad (OD-16.e) para tipos inequívocos; fail-closed. La autoridad global queda sujeta a la unidad apagada (sin excepción de atajo).

## 14 · Inquilino

`company_id` ya verificado en el alta; sin cambio.

## 15 · Unidad de negocio

Es el objeto del paquete: derivación al nacer + guarda estricta; semántica OD-16/OD-09 aplicada a la escritura sin lote.

## 16 · RBAC

`operations:create` sin cambio.

## 17 · Transacciones

Dentro de la transacción del alta; sin bloqueos nuevos.

## 18 · Auditoría

Sin cambio en el alta (audita `CREATED`); el evento ahora nace con unidad (mejor traza). La clasificación previa de `farm_inspection` si C-02 la mantiene sigue igual.

## 19 · i18n

N/A (mensajes API existentes).

## 20 · Escritorio · 21 · Móvil

Sin cambio de UI; regresión de registro de `hatchery_inspection` por UI en ambos viewports.

## 22 · Manejo de errores

La denegación usa los errores existentes de `exigir_unidad_operativa` (`no_habilitada`/`sin_empresa`/`sin_concesion` → 400/403 según patrón vigente; sin códigos nuevos).

## 23 · Impacto de migración

Ninguna.

## 24 · Impacto SAP

Indirecto (eventos de origen con unidad correcta). Sin cambio de contrato SAP.

## 25 · Compatibilidad hacia atrás

- Actores con la unidad del tipo y ON: idéntico (evento ahora con `business_unit_id` poblado — mejora visible solo en datos).
- Actores sin la unidad o con la unidad OFF: 201→denegado (corrección).
- `grandparent_import`: idéntico (R-153).
- `farm_inspection`: según C-02 (por defecto, sin cambio funcional si la granja no declara cadena única).

## 26 · Criterios de aceptación

| AC | Criterio |
|---|---|
| AC-R221-01 | Global situada; `hatchery` OFF; `hatchery_inspection` sin lote ⇒ **denegado** (no 201) |
| AC-R221-02 | Actor solo `broiler`; `hatchery_inspection` ⇒ denegado; cero filas |
| AC-R221-03 | Actor con `hatchery` concedida y ON ⇒ 201 y `business_unit_id = hatchery` |
| AC-R221-04 | `farm_inspection` sin lote ⇒ regla C-02 aplicada (derivada de granja o clasificación previa documentada); sin regresión del flujo actual decidido |
| AC-R221-05 | `grandparent_import` sin lote intacto (R-153: creación de lote al aprobar; AC58/59) |
| AC-R221-06 | Eventos con lote intactos (la unidad del lote manda) |
| AC-R221-07 | Doble control: apagar `hatchery` revierte el 201 legítimo a denegado; re-encender (sin regrant) no revive concesiones (OD-23) |
| AC-R221-08 | Sin migración/endpoint/permiso; sin reescribir históricos |
| AC-R221-09 | Bandeja de clasificación: los tipos inequívocos dejan de aparecer como pendientes si nacen clasificados |
| AC-R221-10 | Regresión: `test_operations_bu_enforcement.py` (W02…W14), `test_lots_bu_enforcement.py`, `test_pending_classification.py`, `test_r153_import_lot_auto.py` verdes |

## 27 · Pruebas RED→GREEN

`R-221_RED_E2E_UAT_DESIGN.md §1`: `test_r221_01_hatchery_off_deniega_inspeccion`, `test_r221_02_sin_concesion_deniega`, `test_r221_03_con_unidad_nace_clasificado`, `test_r221_04_farm_inspection_regla_decidida`, `test_r221_05_grandparent_intacto` (control), `test_r221_06_con_lote_intacto` (control).

## 28 · E2E

API sobre pila local (`§2`): `R221-RT-01…06` (OFF/denegado; sin concesión; con unidad; regrant; import intacto; con lote intacto); artefacto `evidence/r221/runtime-{red,c3}.json`. Regresión UI: registro de `hatchery_inspection` legítimo (201) y denegado (mensaje seguro).

## 29 · UAT

Requiere **micro-decisión** C-02 (propietario): «¿qué unidad tiene una inspección de granja sin lote?». Opciones: (A) derivar de la granja/galpón declarados cuando declaren cadena única; (B) exigir clasificación previa siempre; (C) mantener «alguna unidad» (statu quo) — recomendado A con fallback B. La UAT en sí es técnica (API/UI con actores), 10 min.

## 30 · Criterios de cierre

C-02 decidida · RED válida · GREEN local (AC01-10) · sensibilidad (S1: retirar derivación ⇒ AC01/03 rojas; S2: relajar guarda con unidad derivada ⇒ AC01/02 rojas) · sin migración/endpoint/permiso · R-221 → `CLOSED` con GA-REM asignado.
