# R-221 · FINDING — EVENTOS SIN LOTE NO DERIVAN UNIDAD: INSPECCIONES REGISTRABLES FUERA DE LA UNIDAD HABILITADA/CONCEDIDA

| Campo | Valor |
|---|---|
| **ID canónico** | **R-221** (asignado en `GA_CLAUDE_DISCOVERED_GAP_SPEC_REGISTER.md §0`; máximo previo R-189) |
| **Título** | Los eventos de `LOT_OPTIONAL_EVENTS` sin lote nacen con `business_unit_id = null`; la guarda de unidad solo exige «alguna unidad» ⇒ `hatchery_inspection` se registra con `hatchery` **apagada** (autoridad global) o sin concesión `hatchery` (actor de empresa) |
| **Severidad** | **P2** (§49: escritura productiva fuera de la unidad habilitada/concedida; doctrina OD-16.e/OD-09) |
| **Clase** | `SECURITY` (escritura fuera de unidad) / `DATA_INTEGRITY` (evento nacido sin cadena inequívoca) |
| **Proceso** | P-05 (inspección de incubadora), P-01/P-03/P-06 (inspecciones de granja) |
| **Fecha · HEAD** | 2026-09-13 · `c0b4afc` (== `origin/main`) |
| **Familia** | Vecino `R-153 C2b` (que derivó solo `grandparent` para la importación); OD-16.e; `classification.py` («tipo inequívoco» solo para lectura) |
| **Paquete** | `audit/ga-claude-final-audit/specs/R-221/` (completo, 6 ficheros) |
| **GA-REM** | a asignar al autorizar; siguiente libre **GA-REM-043** |
| **Bloquea SAP** | **SÍ** (escritura productiva fuera de la unidad habilitada; fiabilidad de eventos de origen) |
| **UAT del propietario** | sí, para C-02 (`farm_inspection` sin lote: qué unidad tiene) — decisión acotada; el resto es técnico |

## 1 · Evidencia

### 1.1 Código (verificado en HEAD)

- `backend/app/operations/service.py:61-68` — `LOT_OPTIONAL_EVENTS = {FARM_INSPECTION, HATCHERY_INSPECTION, GRANDPARENT_IMPORT}`.
- `:242-246` — `unidad_directa` se fija **solo** para `grandparent_import` (patrón R-153 C2b); `hatchery_inspection` y `farm_inspection` no lo tienen.
- `:185-197` — sin lote y sin `business_unit_id` ⇒ `unidad=None`; la guarda `exigir_unidad_operativa` (`business_units/service.py:278-290`) con `unidad=None` acepta si hay **alguna** unidad habilitada (global) o **alguna** efectiva (actor de empresa).
- `backend/app/business_units/classification.py:65-113` — el «tipo inequívoco» existe solo para **lectura** (predicado de visibilidad), no para asignar unidad al nacer.
- El evento queda con `business_unit_id=null` (pendiente de clasificar) aunque `hatchery_inspection` sea de cadena inequívoca.

### 1.2 Evidencia runtime (local, 2026-09-13)

`evidence/ui-e2e-local-pass2.json` caso `OD16b-global-actor-bu-off-api`: `POST /operations {event_type:'hatchery_inspection'}` sin lote ⇒ **201** con `hatchery` **apagada** (disable por UI 200 inmediatamente antes; enable 200 después, restaurado). Por construcción, un actor de empresa con concesión solo `broiler` (`efectivas ≠ ∅`) también puede registrar `hatchery_inspection`.

### 1.3 Contradicción normativa

OD-16.e («apagado = inaccesible también para la autoridad global») y OD-09 (concesión por unidad). El caso de la importación (`grandparent_import`) sí derivó su unidad en R-153 C2b; las inspecciones quedaron fuera.

## 2 · Causa raíz

La derivación de unidad por tipo se implementó como parche puntual (importación de abuelas) en lugar de regla para tipos inequívocos; los dos tipos de inspección sin lote caen en `unidad=None` y la guarda de escritura degrada a «alguna unidad» en vez de exigir la unidad real del evento.

## 3 · Impacto

- Escritura productiva aceptada con la unidad apagada (debe ser inaccesible, OD-16.e) o sin concesión (OD-09) — la violación deja rastro en `operational_events` y en la bandeja de clasificación pendiente.
- La bandeja de pendientes acumula eventos que debieron nacer clasificados (menos ruido de clasificación si el tipo es inequívoco).
- Precedente para R-204/R-212 (doctrina de unidad): el borde de escritura es la última línea.

## 4 · Dedup realizada (§48)

| Registro | Resultado |
|---|---|
| R-001…R-189 | `R-153 C2b` derivó `grandparent`; la frontera «demás tipos sin cambio» es explícita en su anexo. `OD-16` acotó lecturas; el alta sin lote no tiene hallazgo. |
| GA-REM-001…042 | `GA-REM-002` (tenencia) y `GA-REM-040` (clasificación) tocan la clasificación pendiente; no la derivación al nacer. |
| Informe D (B.13) | La frontera de escritura OD-16 «PASS» se verificó con eventos con lote; el caso sin lote no estaba cubierto (el propio informe propone «tests W-xx con unidad apagada/no concedida para eventos sin lote»). |

Conclusión: **nuevo**; ID asignado **R-221**.

## 5 · Propietario sugerido

Equipo backend (`operations` + `business_units`). Requiere micro-decisión del propietario para `farm_inspection` (C-02): la granja puede pertenecer a cualquier cadena ⇒ su tipo **no** es inequívoco.

## 6 · Bloquea SAP y por qué

**SÍ.** Un evento productivo nacido sin cadena correcta (o aceptado con la unidad apagada) contamina la clasificación, los KPI por unidad y la futura definición de eventos fuente. El cierre es condición de la doctrina OD-16/OD-09 completa.

## 7 · Interdependencias

- **R-153 C2b** (patrón de derivación): se generaliza el mecanismo `unidad_directa` a tipos inequívocos.
- **classification.py** (bandeja de pendientes): `farm_inspection` sin derivación sigue yendo a clasificación (o se decide otra regla).
- **R-204/R-212**: misma doctrina; tranche de seguridad/alcance coordinada.
