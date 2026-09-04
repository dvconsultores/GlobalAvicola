# CHECKLIST DE INSTALACIÓN DESDE CERO

**GA-REM-025 §62** · verificado 2026-09-04 sobre PostgreSQL 16.2 aislado

Esta lista tiene dos usos. Hoy sirve para dejar el entorno compartido en un baseline
limpio. Mañana es el guion de instalación para el primer cliente real: el camino es el
mismo, y por eso conviene que esté probado antes de que haya alguien esperando.

---

## Resultado

```
34 comprobaciones · 32 PASS · 2 hallazgos documentados
```

| # | Comprobación | Estado | Evidencia |
|--:|---|:--:|---|
| 1 | Base de datos creada, vacía | **PASS** | `certify_baseline.sh` paso 2 |
| 2 | `alembic upgrade head` sobre base vacía | **PASS** | 0 errores; cadena completa |
| 3 | Revisión en cabeza, una sola cabeza | **PASS** | `l2m3n4o5p6q7 (head)` |
| 4 | Deriva de esquema, tablas y columnas | **PASS** | `verify.sh` 3/8 · 0 deriva |
| 5 | Deriva de enums (`R-40`, `R-41`) | **PASS** | 0 valores sin migración |
| 6 | Reconciliación RBAC sobre base vacía | **PASS** (añade 0, como debe) | no crea roles: los busca por nombre |
| 7 | Seed de baseline aplicado | **PASS** | 6 roles · 55 permisos · 2 empresas · 1 admin |
| 8 | 46 asociaciones operativas, permiso a permiso | **PASS** | `T-025-02`, contra la matriz de la migración |
| 9 | Ningún permiso concedido fuera de `docs/12 §3` | **PASS** | `T-025-02` |
| 10 | 9 comodines del Super Administrador | **PASS** | `T-025-02` |
| 11 | Settings requeridos presentes | **PASS** | umbrales 3 % / 8 % (`T-025-03`) |
| 12 | Administrador puede autenticarse | **PASS** | login HTTP 200 |
| 13 | Sin contraseñas literales en los seeds | **PASS** | `verify.sh` 5/8 (`GA-REM-004`) |
| 14 | Dos tenants deterministas disponibles | **PASS** | `TEST COMPANY A` / `B` |
| 15 | Los fixtures crean sus precondiciones | **PASS** | `T-025-05` |
| 16 | Los fixtures se retiran sin residuo | **PASS** | `T-025-06` |
| 17 | El baseline es idempotente | **PASS** | `T-025-07`, dos siembras idénticas |
| 18 | El reset es reproducible | **PASS** | dos ejecuciones, 182 → 0 filas |
| 19 | La guarda destructiva es fail-closed | **PASS** | `T-025-08` (8 casos), `T-025-09`, `T-025-10` |
| 20 | Backend arranca contra base limpia | **PASS** | uvicorn sirviendo |
| 21 | Estado vacío · lotes | **PASS** | HTTP 200 |
| 22 | Estado vacío · operaciones | **PASS** | HTTP 200 |
| 23 | Estado vacío · alertas | **PASS** | HTTP 200 |
| 24 | Estado vacío · panel | **PASS** | HTTP 200 |
| 25 | Estado vacío · maestros | **PASS** | HTTP 200 |
| 26 | Estado vacío · revisión y aprobaciones | **PASS** | HTTP 200 |
| 27 | Estado vacío · auditoría | **PASS** | HTTP 200 |
| 28 | Primeros maestros creables | **PASS** | granja, galpón, línea, raza, causa |
| 29 | Primer lote creable | **PASS** | HTTP 201 |
| 30 | Primera operación registrable | **PASS** | recepción + mortalidad |
| 31 | El saldo derivado es correcto | **PASS** | 5.000 recibidas − 12 muertas |
| 32 | Aislamiento de lectura entre tenants | **PASS** | 4 comprobaciones, usuario no-superadmin |
| 33 | Aislamiento de escritura entre tenants | **PASS** | `R-42`, escritura cruzada denegada |
| 34 | Saldo de apertura → saldo de aves | **`R-67`** | un lote activado manualmente rechaza toda mortalidad |
| 35 | Alta visible para la petición inmediata | **`R-68`** | 3 de 5 altas con 201 fallan al leerse al instante |

## Cómo se reproduce

```sh
cd backend
./scripts/certify_baseline.sh
```

Un solo comando: crea la base vacía, migra, siembra, la ensucia con datos de desarrollo,
la resetea dos veces, comprueba que la guarda bloquea un entorno prohibido, y recorre el
primer flujo de negocio de extremo a extremo.

## Requisitos de inicialización del sistema (§61)

Lo único que una instalación nueva **no puede** crear por sí misma:

```
roles + asociaciones de permiso     no hay API que cree las asociaciones
primer usuario administrador        hace falta uno para llamar a cualquier API
fases productivas                   creables, pero son catálogo del dominio
```

Todo lo demás —granjas, galpones, líneas genéticas, causas, vacunas, transportes, pasos de
aprobación— lo crea el propio usuario por la interfaz. **El baseline no los inventa.**

## Lo que esta lista descubrió

El valor de la comprobación 34 no es la comprobación: es que nadie lo había probado.
`activate-manual` es el camino previsto para incorporar lotes que ya existen cuando se
instala el sistema —justo lo que hará el primer cliente— y produce lotes sobre los que no
puede registrarse ninguna mortalidad. Era invisible mientras todos los lotes del entorno
compartido venían de eventos de recepción sembrados.
