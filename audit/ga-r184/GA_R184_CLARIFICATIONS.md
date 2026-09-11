# GA-R184 · CLARIFICACIONES (C01–C20)

Resueltas contra fuentes canónicas; **no se preguntó al propietario nada respondible por repositorio**.

| # | Pregunta | Respuesta canónica | Fuente |
|---|---|---|---|
| C01 | Ruta exacta | `GET /api/v1/reports/kpi/ipe/{lot_id}` | `app/reports/router.py` |
| C02 | Permiso exacto | `reports:read` (0 permisos nuevos) | íd. |
| C03 | Fórmula exacta del IPE | `(Viabilidad% × Ganancia_Diaria_g × 100) / (FCR × 10)` | docstrings router+servicio; traza §1 |
| C04 | Entradas de fecha | `Lot.start_date` (aware) + `date.today()` | traza temporal §1 |
| C05 | Operandos exactos del fallo | `date.today()` (`date`) − `lot.start_date` (`datetime` aware) | repro local + runtime |
| C06 | Dominio DATE vs DATETIME | **DATE** (día de calendario) para la edad | `lots/service.py:379`, `operations/service.py:776`, R-75/GA-REM-028 |
| C07 | Convención de conteo | `(hoy − día_inicio).days`; mismo día ⇒ clamp 1; sin inicio ⇒ 30 (legado) | `service.py` pre-fix, preservado |
| C08 | Lote abierto | Calcula; edad contra hoy (provisional) | código vigente, preservado |
| C09 | Lote cerrado | Calcula; **la edad no se congela al cierre** (limitación preexistente registrada) | código vigente |
| C10 | `planned_close_date` | **Irrelevante para IPE** (SLA aparte, R-182) | grep de uso; matriz de estados |
| C11 | Fecha «hoy» | `date.today()` del proceso; simulable (`GA_TEST_SIMULATED_TODAY`, R-28) | convención vigente |
| C12 | Zona horaria | Sin framework nuevo; día de negocio anclado UTC en persistencia; comparación calendario vs calendario; sin off-by-one | `_inicio_declarado`/`_fecha_de_negocio` |
| C13 | Datos ausentes | Matriz de disponibilidad (agregados vacíos = 0; nunca 500/NaN) | matriz |
| C14 | Denominador cero | Guardas `fcr > 0` y clamp `age_days` ⇒ IPE 0.0 controlado | código |
| C15 | Redondeo/precisión | Preservado (ipe 1d, fcr 2d, ganancia 2d, etc.) | traza negocio §5 |
| C16 | Esquema de respuesta | Sin cambios (8 claves + `reference` literal) | router/servicio |
| C17 | Consumidor frontend | **USER_VISIBLE**: `LotDetailPage`, `LotReportPage` (tarjeta oculta si el fetch falla) | grep frontend |
| C18 | ¿Owner UAT? | **SÍ** (superficie visible) — corta: KPI carga, valor visible, refresco, móvil | spec §21 |
| C19 | Respuesta de seguridad | 404 anti-enumeración (ajeno/inexistente/fuera de alcance), 403 RBAC; OD-16 aplicado (global no bypassa BU OFF) | `_exigir_lote` + scope |
| C20 | Criterio de cierre | 500 resuelto + fórmula preservada + AC críticos + regresión + limpieza ⇒ CLOSED | spec §20 |

**Subcaso que requirió clasificación (no STOP):** la tensión escala-fórmula vs bandas `reference` **no impide** resolver R-184 (la fórmula está canonizada y se preserva); queda como **observación de negocio** registrada para el propietario (`OWNER_DECISION_REQUIRED`, no bloquea). No se inventó ninguna fórmula alternativa.
