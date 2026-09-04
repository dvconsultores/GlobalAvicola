# INVENTARIO DE DATOS DEL ENTORNO COMPARTIDO

**GA-REM-025 §24** · 2026-09-04 · clasificación previa a cualquier borrado

---

## 1. Estado de acceso

```
SHARED ENV API .......... DISPONIBLE
SHARED ENV DATABASE ..... NOT_REACHABLE
SHARED ENV SSH .......... BLOCKED_BY_AUTH
```

El puerto 5432 del servidor acepta TCP pero corta el intercambio de PostgreSQL antes de
negociar, con la credencial que el propio `backend/.env` del proyecto declara. Es una
barrera de red o de `pg_hba.conf`, no de contraseña. **No se probaron credenciales
alternativas ni se buscaron claves** (política vigente, §9 del encargo).

Consecuencia: **los recuentos reales de filas del entorno compartido no pudieron leerse.**
Lo que sigue es la clasificación completa del modelo —que es lo que gobierna el borrado— y
los recuentos medidos sobre una réplica de certificación construida con los mismos seeds.
La herramienta `scripts/environment_reset.py --inventory` produce los recuentos reales en
cuanto se ejecute donde la base sea alcanzable.

## 2. Alcance

**48 tablas**: las 47 del modelo ORM más `alembic_version`. Cobertura verificada por prueba
(`T-025-11`): ninguna tabla queda sin clasificar. Lo no clasificado nunca se borra.

## 3. Resumen

| Categoría | Tablas | Destino |
|---|--:|---|
| `SYSTEM_REQUIRED` | 1 | conservar |
| `AUTH_REQUIRED` | 4 | conservar |
| `CONFIGURATION_REQUIRED` | 1 | conservar |
| `REFERENCE_MASTER_REQUIRED` | 1 | conservar |
| `CLIENT_MASTER_DATA` | 17 | **borrar** |
| `TEST_BUSINESS_DATA` | 20 | **borrar** |
| `SIMULATED_SAP_DATA` | 4 | **borrar** |
| `UNKNOWN` | 0 | (se conservaría) |

**41 tablas se vacían · 7 se conservan.**

## 4. Recuentos medidos sobre la réplica de certificación

Base construida desde vacío con `alembic upgrade head` + `seeds/dev_seeds.py` +
fixtures, que es como se pobló el entorno compartido:

```
Baseline recién sembrado ............   0 filas borrables en 41 tablas
Tras sembrar datos de desarrollo .... 182 filas borrables en 41 tablas
Tras el reset .......................   0 filas borrables en 41 tablas
```

Distribución de esas 182: 170 en maestros de cliente (galpones 24, causas de mortalidad 24,
alimentos 18, medicamentos 20, vacunas 20, granjas 6, razas 6, proveedores 10, transportes
8, incubadoras 8, nacedoras 4, plantas 4, incubadoras de planta 2) y 12 en historia de
lotes creada por fixtures.

## 5. Tabla completa

| Tabla | Categoría | ¿Arranque? | ¿Maestro? | ¿Negocio/test? | ¿Borrable? | Depende de |
|---|---|:--:|:--:|:--:|:--:|---|
| `alembic_version` | SYSTEM_REQUIRED | sí | no | no | no | — |
| `companies` | AUTH_REQUIRED | sí | no | no | no | — |
| `permissions` | AUTH_REQUIRED | sí | no | no | no | roles |
| `roles` | AUTH_REQUIRED | sí | no | no | no | — |
| `users` | AUTH_REQUIRED | sí | no | no | no | roles |
| `approval_steps` | CONFIGURATION_REQUIRED | no | no | no | no | companies, roles |
| `productive_phases` | REFERENCE_MASTER_REQUIRED | no | sí | no | no | — |
| `breeds` | CLIENT_MASTER_DATA | no | sí | no | **sí** | genetic_lines |
| `correction_types` | CLIENT_MASTER_DATA | no | sí | no | **sí** | companies |
| `cull_causes` | CLIENT_MASTER_DATA | no | sí | no | **sí** | companies |
| `farms` | CLIENT_MASTER_DATA | no | sí | no | **sí** | companies |
| `feed_types` | CLIENT_MASTER_DATA | no | sí | no | **sí** | companies |
| `genetic_lines` | CLIENT_MASTER_DATA | no | sí | no | **sí** | companies |
| `hatcheries` | CLIENT_MASTER_DATA | no | sí | no | **sí** | companies |
| `hatchers` | CLIENT_MASTER_DATA | no | sí | no | **sí** | hatcheries |
| `houses` | CLIENT_MASTER_DATA | no | sí | no | **sí** | farms |
| `incubators` | CLIENT_MASTER_DATA | no | sí | no | **sí** | hatcheries |
| `medications` | CLIENT_MASTER_DATA | no | sí | no | **sí** | companies |
| `mortality_causes` | CLIENT_MASTER_DATA | no | sí | no | **sí** | companies |
| `processing_plants` | CLIENT_MASTER_DATA | no | sí | no | **sí** | companies |
| `rejection_reasons` | CLIENT_MASTER_DATA | no | sí | no | **sí** | companies |
| `suppliers` | CLIENT_MASTER_DATA | no | sí | no | **sí** | companies |
| `transports` | CLIENT_MASTER_DATA | no | sí | no | **sí** | companies |
| `vaccines` | CLIENT_MASTER_DATA | no | sí | no | **sí** | companies |
| `approval_actions` | TEST_BUSINESS_DATA | no | no | sí | **sí** | approval_steps, operational_events, review_batches, users |
| `audit_logs` | TEST_BUSINESS_DATA | no | no | sí | **sí** | companies, farms, houses, lots, sap_references, users |
| `bird_movements` | TEST_BUSINESS_DATA | no | no | sí | **sí** | breeds, houses, operational_events |
| `chick_batches` | TEST_BUSINESS_DATA | no | no | sí | **sí** | egg_batches, lots, operational_events |
| `consolidated_movements` | TEST_BUSINESS_DATA | no | no | sí | **sí** | companies, lots, users |
| `correction_logs` | TEST_BUSINESS_DATA | no | no | sí | **sí** | correction_types, operational_events, users |
| `egg_batches` | TEST_BUSINESS_DATA | no | no | sí | **sí** | lots, operational_events |
| `egg_movements` | TEST_BUSINESS_DATA | no | no | sí | **sí** | operational_events |
| `egg_storage` | TEST_BUSINESS_DATA | no | no | sí | **sí** | lots, operational_events |
| `evidences` | TEST_BUSINESS_DATA | no | no | sí | **sí** | companies, operational_events, users |
| `feed_movements` | TEST_BUSINESS_DATA | no | no | sí | **sí** | feed_types, operational_events |
| `hatchery_params` | TEST_BUSINESS_DATA | no | no | sí | **sí** | hatcheries, hatchers, incubators, operational_events |
| `inspection_details` | TEST_BUSINESS_DATA | no | no | sí | **sí** | houses, operational_events |
| `lot_phases` | TEST_BUSINESS_DATA | no | no | sí | **sí** | lots, productive_phases |
| `lots` | TEST_BUSINESS_DATA | no | no | sí | **sí** | breeds, companies, farms, genetic_lines, houses |
| `opening_balances` | TEST_BUSINESS_DATA | no | no | sí | **sí** | lots, productive_phases, users |
| `operational_alerts` | TEST_BUSINESS_DATA | no | no | sí | **sí** | companies, lots, operational_events, users |
| `operational_events` | TEST_BUSINESS_DATA | no | no | sí | **sí** | companies, cull_causes, farms, houses, lots, medications,… |
| `reversals` | TEST_BUSINESS_DATA | no | no | sí | **sí** | companies, operational_events, users |
| `review_batches` | TEST_BUSINESS_DATA | no | no | sí | **sí** | companies, users |
| `sap_payloads` | SIMULATED_SAP_DATA | no | no | sí | **sí** | companies |
| `sap_references` | SIMULATED_SAP_DATA | no | no | sí | **sí** | companies, users |
| `sap_responses` | SIMULATED_SAP_DATA | no | no | sí | **sí** | sap_payloads |
| `sap_sync_jobs` | SIMULATED_SAP_DATA | no | no | sí | **sí** | companies, users |

## 6. Lo que un cliente nuevo puede crear por sí mismo

Determinante para decidir qué es «configuración requerida» y qué es dato inventado:

| Recurso | Autoservicio | Evidencia |
|---|---|---|
| Los 19 maestros | **sí**, CRUD completo | `app/masters/router.py:88-106` |
| Pasos de aprobación | **sí**, con `POST /approval-steps/seed-defaults` | `app/review/router.py:206` |
| Roles | **sí** | `app/auth/router.py:132` |
| Fases productivas | **sí**; ningún código depende de sus `code` | `app/masters/router.py:101` |
| **Asociaciones rol→permiso** | **no**: no hay API | `app/auth/service.py:315` |
| **Primer usuario** | **no**: hace falta uno para llamar a cualquier API | — |

Por eso el baseline siembra exactamente eso —roles, permisos, un administrador— y nada más
de negocio. Todo lo demás lo crea quien use el sistema.

## 7. Un detalle que cambia el análisis

La migración `l2m3n4o5p6q7` **no crea roles**: los busca por nombre y salta los que no
existen (`alembic/versions/l2m3n4o5p6q7:121-126`). Verificado sobre base vacía:

```
[R-44] asociaciones rol-permiso añadidas: 0
```

De modo que reconciliar no basta para una instalación nueva. El seed de baseline es
obligatorio, y por eso deriva su matriz **de esa misma migración** en vez de copiarla:
mantener dos copias fue la causa de `R-44`.
