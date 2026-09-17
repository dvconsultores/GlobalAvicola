# GLOBAL AVÍCOLA — CUTOVER / GO-LIVE GAP MATRIX

Fecha: 2026-09-17 · Baseline: `fef7289` · Estado: **G0 (discovery — sin implementación)**
Convención: `BLOQ` = debe resolverse antes de Go-Live · `POST` = puede resolverse después · `DEC` = decisión Owner requerida para clasificar.

## 1 · Cutover (capacidad)

| ID | Gap | Severidad | Pre/Post | Resolución | Estado |
|---|---|---|---|---|---|
| CUT-01 | **Acta de cutover inexistente** (firma, hashes encadenados, responsables) — el flujo actual termina en reconciliación | Alta | **BLOQ** | G2: AC `CUT-GL-01` (spec→AC→RED→impl→cert) | SPEC propuesto (`CUTOVER_MASTER_SPEC.md` §5) |
| CUT-02 | **Guarda de fecha vs `cutover_datetime`** en eventos de lotes migrados no existe (evento con fecha anterior al corte) | Alta | **BLOQ** | G2: AC `CUT-GL-02` (o procedimiento de reconciliación aprobado) | Identificado |
| CUT-03 | **Secuencia multi-BU/multi-empresa** sin dependencias declaradas (incubadora→lote origen) | Media | **BLOQ** | G2: AC `CUT-GL-03` | Identificado |
| CUT-04 | **Cierre de OC/entregas parciales** tras el corte (OC abiertas con entregas futuras reales) | Media | DEC | Decisión funcional GL-OD-08/13 + G2 si aplica | Identificado |
| CUT-05 | **Reapertura/corrección post-firma**: no existe reapertura de batch (solo correcciones de opening) | Media | POST | G2/G4: AC `CUT-GL-05` según decisión | Identificado |
| CUT-06 | **Campos de incubación en curso**: auditoría fina de columnas pendiente (diseño §4 GA-REQ-061 lo exige al implementar) | Alta | **BLOQ** | G2 (previo al uso real de la BU `hatchery`) | Pendiente de auditoría de implementación |

## 2 · Datos reales

| ID | Gap | Severidad | Pre/Post | Resolución | Estado |
|---|---|---|---|---|---|
| DATA-01 | **Sin acceso a datos reales** del negocio (poblaciones, acumulados, pesos, genética, usuarios) | Alta | **BLOQ** | Cadena `SAP-0 → GL-OD-06`: determinar qué datos siguen disponibles en el SAP actual y por qué mecanismo; luego fuentes/formato (`REAL_DATA_MIGRATION_PLAN.md` §2) | **`PENDING_SAP0_DISCOVERY`** |
| DATA-02 | **Definición de "lote real" por empresa/BU** (nomenclatura `legacy_lot_code`) | Media | **BLOQ** | Taller funcional G1 con formato fijado | Pendiente |
| DATA-03 | **Datos que NO deben migrarse** sin declarar formalmente (p. ej., histórico viejo sin valor operacional) | Media | **BLOQ** | Declaración en `REAL_DATA_MIGRATION_PLAN.md` §5 a completar con Owner | Borrador |
| DATA-04 | **Calidad de datos reales** (pesos, fechas, unidades heterogéneas; identificación de UNKNOWN legítimo) | Alta | **BLOQ** | Rehearsal (set R2 sanitizado) + reglas de transformación §4 | Pendiente |
| DATA-05 | **Protección de datos reales** (PII de usuarios; datos comerciales) — entorno segregado para rehearsal/apply | Alta | **BLOQ** | Procedimiento de custodia + acceso mínimo (G1) | Especificado en planes |
| DATA-06 | Inventarios operacionales / saldos no-lote: definir universo real (almacén, huevos, medicación en uso) | Media | DEC | GL-OD-06/07 + `REAL_DATA_MIGRATION_PLAN.md` §3 | Identificado |

## 3 · Infraestructura / Operaciones

| ID | Gap | Severidad | Pre/Post | Resolución | Estado |
|---|---|---|---|---|---|
| INF-01 | **Topología productiva sin decidir** (mismo host compartido vs instancia nueva separada) | Alta | **BLOQ** | GL-OD-01 (Owner) | Recomendación: instancia nueva (ver infra doc) |
| INF-02 | **Mecanismo de despliegue para producción**: B (auto Watchtower) diseñado para entorno compartido, no para operación con datos reales | Alta | **BLOQ** | GL-OD-02: mantener B o promover deploy gated (aprobación humana por ventana) | Recomendación: deploy gated para prod |
| INF-03 | **Observabilidad inexistente** (métricas, alertas, uptime, error tracking) | Alta | **BLOQ** | GL-OD-03: proveedor y alcance | Identificado |
| INF-04 | **Correo saliente inexistente** (notificaciones por email, restablecimiento de clave) | Alta | DEC | GL-OD-04: SMTP/servicio + alcance (o declarar email fuera de v1 con workaround) | Identificado |
| INF-05 | **Backups**: política local existe (diaria + pre-upgrade, RPO≤24h/RTO≤4h) pero **sin destino off-site ni restore ensayado** sobre copia | Alta | **BLOQ** | GL-OD-05: destino off-site + cadencia de prueba de restore | Política vigente extendible |
| INF-06 | **Secretos**: `.env` en host, sin rotación formal ni bóveda | Media | **BLOQ** | GL-OD-09: rotación inicial + custodios (sin imprimir secretos en ningún paso) | Identificado |
| INF-07 | **SSL/DNS de dominio productivo**: certificado del dominio de UAT existe; dominio definitivo no declarado | Media | **BLOQ** | GL-OD-01/10: dominio + renovación | Identificado |
| INF-08 | **Capacidad/sizing**: recursos del host no dimensionados para carga real multiempresa | Media | DEC | Medición en rehearsal + decisión | Pendiente |
| INF-09 | **Contingencia manual / rollback operacional** documentado a nivel sistema (más allá de backup) | Media | **BLOQ** | Plan de contingencia (G1) — quién, cómo, cuándo | Spec en infra doc §ops |
| INF-10 | **Usuarios técnicos y cuentas admin reales** (NBO-01): provisión, MFA no disponible hoy → riesgo aceptado explícito | Media | **BLOQ** | Checklist ops + GL-OD-11 | Identificado |
| INF-11 | **Mantenimiento y ventanas**: política de upgrades (Alembic en entrypoint OK) y ventanas de mantenimiento | Baja | POST | Procedimiento operativo | Identificado |
| INF-12 | **Monitoreo de backups/restore trimestral**: mecanismo de recordatorio/verificación | Baja | POST | Calendario operativo | Identificado |

## 4 · Producto / funcional (heredados relevantes)

| ID | Gap | Severidad | Pre/Post | Resolución | Estado |
|---|---|---|---|---|---|
| OPS-01 | **NBO-03 · OD-19** reverso huevos/incubación diferido — impacto operativo real al corregir cargas/nacimientos | Alta | DEC | `GL-OD-08` (`PENDING_OWNER_DECISION`; tratamiento propuesto no vinculante en este pack): aceptar limitación (con workaround documentado) o programar en G2 | Decisión Owner |
| OPS-02 | **AOD-13** (unidad de `farm_inspection` sin lote) — registro de decisión pendiente del Pre-SAP | Baja | DEC | GL-OD-13 (registro administrativo) | Accionable |
| OPS-03 | **NBO-02** R-133/R-134 definiciones KPIs | Baja | POST | Roadmap G4 | Registrado |
| OPS-04 | **RES-07** (filas VNC con UAT) / **G-06** (sondas C3) — notas administrativas heredadas | Baja | POST | Cierre administrativo en G4 | Registrado |

## 5 · Resumen

- **BLOQ (antes de Go-Live)**: CUT-01, CUT-02, CUT-03, CUT-06, DATA-01, DATA-02, DATA-03, DATA-04, DATA-05, INF-01, INF-02, INF-03, INF-05, INF-06, INF-07, INF-09, INF-10 → **17** (varios dependen de decisiones GL-OD).
- **DEC (decisión Owner para clasificar)**: CUT-04, DATA-06, INF-04, INF-08, OPS-01, OPS-02 → **6**.
- **POST (tras Go-Live)**: CUT-05, INF-11, INF-12, OPS-03, OPS-04 → **5**.
- **Dependencia SAP-0 (reconciliación 2026-09-17)**: `DATA-01` (y con él todo el frente de datos) queda `PENDING_SAP0_DISCOVERY`; cadena `SAP-0 → GL-OD-06 → REAL DATA MIGRATION → CUTOVER G1/G2`. SAP no es fuente definitiva hasta verificar el landscape actual.
- Ninguno de estos gaps es una regresión del baseline `fef7289`: son extensiones/operación de la nueva fase.
