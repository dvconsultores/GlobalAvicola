# PLACEHOLDERS LOCALES DIFERIDOS A SAP

**Auditoría 360°** · 2026-09-09 · base `7310adb` · **AUDIT ONLY**

Inventario de todo lo que la app mantiene **localmente en lugar de SAP**, con la regla que
debe acompañar a cada uno hasta que SAP lo sustituya. Un placeholder no es un defecto; un
placeholder **no declarado** sí lo es, porque se convierte en maestro paralelo por inercia.

Estado de cada uno: `DECLARADO` (el código o la spec dicen que es provisional) ·
`NO_DECLARADO` (nada lo dice) · `HARD_CODED` (valor fijo en código que SAP debería proveer).

---

## 1. Maestros locales que SAP sustituirá

| # | Placeholder | Tabla / ruta | Qué proveerá SAP | Clave externa hoy | Estado | Regla de contención propuesta (no implementar en esta auditoría) |
|---|---|---|---|---|---|---|
| PL-01 | Tipos de alimento | `feed_types` · `/masters/feed-types` | Material MM por tipo (pre-iniciador…finalizador, macho/hembra, medicado; Rec. §5) | `code` opcional | `NO_DECLARADO` | añadir `sap_material_code` y marcar maestro como `origen=LOCAL` hasta importación |
| PL-02 | Vacunas | `vaccines` · `/masters/vaccines` | Material MM sanitario con lote y vencimiento (Rec. §10) | ninguna | `NO_DECLARADO` | ídem; `vaccine_lot_number` ya viaja en el evento |
| PL-03 | Medicinas | `medications` · `/masters/medications` | Material MM sanitario | ninguna | `NO_DECLARADO` | ídem |
| PL-04 | Proveedores | `suppliers` · `/masters/suppliers` | Business Partner | `sap_code` opcional · **además** `sap_references.VENDOR` | `NO_DECLARADO` (doble vía) | una sola representación; `sap_code` obligatorio cuando `SAP_ADAPTER=real` |
| PL-05 | Empresas | `companies` · `/masters/companies` | Sociedad | ninguna | `NO_DECLARADO` · `R-124` | `AOD-06` |
| PL-06 | Granjas | `farms` · `/masters/farms` | Centro / atributo operativo | `code` opcional | `NO_DECLARADO` · `R-124` | `AOD-06` |
| PL-07 | Galpones y capacidad | `houses.capacity` · `/masters/houses` | PM/EAM / custom (Rec. §25.2) | ninguna | `NO_DECLARADO` | `AOD-02`; `BR-17` seguirá válido contra el valor importado |
| PL-08 | Incubadoras, nacedoras, plantas de incubación | `hatcheries`, `incubators`, `hatchers` | PM/EAM | ninguna | `NO_DECLARADO` | ídem PL-07 |
| PL-09 | Lote productivo | `lots.lot_code` | batch / orden interna / orden producción / custom (Rec. §25.3) | **ninguna** | `NO_DECLARADO` · `H360-S05` | `AOD-03`; hasta entonces `lot_code` debe poder **contener** el id SAP futuro (hoy `String(100)` único, suficiente) |
| PL-10 | Plantas de beneficio | `processing_plants` | Centro SAP o cliente | ninguna | `NO_DECLARADO` | baja prioridad |
| PL-11 | Referencias SAP importadas | `sap_references` (PO, STO, material, vendor, plant, sloc, cost center, batch) | las mismas, por API | `sap_code` | `DECLARADO` (`spec.md §4.3` «modo inicial manual») | ✓ es el único espejo honesto |

## 2. Reglas de negocio locales que SAP debería gobernar

| # | Placeholder | Dónde | Valor fijo | Estado | Observación |
|---|---|---|---|---|---|
| PL-12 | Período cerrado | `validate_period_open` `BR-19` (`validators.py:485-497`) | **90 días** | `HARD_CODED` | Rec. §15 «Períodos abiertos → SAP FI/CO». Ninguna fuente fija 90; no es configurable; no distingue período contable de logístico → `H360-S06` |
| PL-13 | Unidad de medida | `consolidated_movements.unit`, `sap_references.unit` (`String`), `feed_movements.quantity_kg`, `avg_weight` en gramos implícitos | sin catálogo | `NO_DECLARADO` | Rec. §17 «Unidad de medida inválida» no se valida → `H360-B06` |
| PL-14 | Stock disponible | (ausente) | — | `SAP_DEFERRED` correcto | consumo > stock (Rec. §17) no se valida; no debe validarse localmente |
| PL-15 | Existencia de galpón/material/centro/almacén «en SAP» | validación local de FK | — | `DECLARADO` en `docs/16 §7.3-7.7` | correcto mientras el maestro sea local |

## 3. Constantes que sustituyen a un parámetro de negocio

| # | Constante | Dónde | Valor | ¿Configurable? | Fuente que lo autoriza | Estado |
|---|---|---|---|---|---|---|
| PL-16 | Umbrales de mortalidad | `config.py` `MORTALITY_ALERT_WARNING_PCT`, `MORTALITY_ALERT_CRITICAL_PCT` | 3 % / 8 % | sí (`.env`) | `docs/02:516` «umbral configurable» | ✓ `DECLARADO` |
| PL-17 | Rango de temperatura/humedad de inspección | `operations/service.py:428-429` | 18–35 °C · 40–90 % | **no** | ninguna | `HARD_CODED` → `H360-B07`; la referencia de dominio (Cobb) da 32–34 °C en semana 1, luego descendente: un rango único por edad es un placeholder |
| PL-18 | Días base del hen-day | `reports/service.py:166` | `* 30` | no | ninguna (Bases p.5 no define hen-day) | `HARD_CODED` → `KPI` |
| PL-19 | Factor «FCR» | `reports/service.py:155` | `/ 1000` | no | ninguna; el propio código lo llama «simplificado» | `HARD_CODED` → `H360-K01` |
| PL-20 | Edad por defecto sin fecha de inicio | `reports/service.py:596,642` | `else 30` | no | ninguna | `HARD_CODED` |
| PL-21 | Holgura de día futuro | `validators.py:503` | `-1` día | no | comentario `R-30` | `DECLARADO` (con motivo) |
| PL-22 | SLA de revisión | `notifications/sla.py` | 24 h | no (intervalo sí) | `docs/02 §3.14` | ✓ `DECLARADO` |
| PL-23 | Niveles de aprobación | `companies.approval_levels` | default 2 | sí, por empresa | `docs/12 §5` | ✓ |
| PL-24 | Nombres de rol en `seed_default_steps` | `review/service.py:625-680` `_get_role_by_name("Supervisor Avícola" / "Aprobador" / "Analista SAP")` | nombres literales | no | semillas | acoplamiento por nombre: renombrar un rol rompe el sembrado de pasos → `H360-B08` (P3) |

## 4. Datos sembrados que son placeholders (jamás datos de producción)

| Semilla | Contenido | Se ejecuta | Clasificación |
|---|---|---|---|
| `seeds/baseline_seeds.py` | 7 roles (matriz importada de la migración `l2m3n4o5p6q7`), fases, `EMPRESAS_CERTIFICACION`, líneas genéticas, admin, catálogo de 4 unidades (solo catálogo, sin habilitaciones) | **manual** — `docker-entrypoint.sh` solo ejecuta `alembic upgrade head` | baseline de certificación (`GA-REM-025`) |
| `seeds/dev_seeds.py` | 2 empresas, usuarios, 3 granjas, 1 galpón, 5 proveedores, 9 alimentos, 10 vacunas, 10 medicinas, 12 causas mortalidad, 8 causas descarte, 6 razas, 1 planta incubación, 4 incubadoras, 2 nacedoras, 2 plantas, 4 transportes; **0 `sap_references`** | manual | **todo PL-01…PL-10 poblado con datos ficticios** |
| `seeds/usuarios_de_revision.py` | 2 cuentas de revisión | manual | revisión integral (`ENV-01`) |

Consecuencia: como `ENV-01` es el único entorno y es compartido, **no existe frontera** entre
placeholder y dato real. La regla que falta (y que solo el propietario puede fijar) es la del
alta del primer cliente real: qué se vacía, qué se importa de SAP y qué maestro local queda
como definitivo. Es `AOD-11`.

## 5. Lo que NO es placeholder (para no confundir)

- `evidences` (evidencia vive en la app; SAP recibe referencia — Rec. §3.5, §6) ✓
- `audit_logs`, `correction_logs`, `approval_actions` (trazabilidad operativa es de la app) ✓
- `operational_alerts`, `notifications` (banderas operativas son de la app; SAP recibe solo alerta crítica — Rec. §7) ✓
- `genetic_weight_curves` (referencia de dominio administrada por la app) ✓
- `business_units`, `company_business_units`, `user_business_units` (plano de control de producto, `OD-09`) ✓
