# GA-REQ-061 · RECONCILIACIÓN R-67 — «SALDO DE APERTURA»

Evidencia: `audit/remediation/R-67-OPENING-BALANCE-CERTIFICATION.md` (2026-09-04, **CERTIFIED**) + código actual (`app/lots/models.py:37`, `app/lots/service.py:616,738`, `app/lots/router.py:99`, `reports/service.py:193`).

## 1 · Auditoría de R-67 (las 10 preguntas del mandato)

| # | Pregunta | Respuesta | Evidencia |
|---|---|---|---|
| 1 | Qué problema resolvió | `activate-manual` guardaba población en `opening_balances` pero `get_current_bird_balance` no la leía ⇒ lote incorporado quedaba **inoperable** (mortalidad rechazada: «excede el saldo (0)») | R-67 cert §1-§2 |
| 2 | Alcance | Incorporación de **un lote ya en marcha** (activación manual) al operar desde el saldo inicial | cert §2; `docs/02 §3.9` |
| 3 | Entidad afectada | `OpeningBalance` (1:1 con `Lot`, `unique lot_id`) + balance vivo en reportes | `models.py:37+` |
| 4 | Comportamiento implementado | Saldo vivo = `initial_male+female` MENOS eventos post-activación; acumulados históricos (mortalidad/descarte/alimento/huevos/nacimientos/broiler recibido) como **historia**, NO restados de nuevo | cert §3 (RC-08 = evidencia nivel 3) |
| 5 | Vigente | **SÍ** — certificado y en código; también produce auditoría (RA `audit_accion`, T8) | código + T8 |
| 6 | Saldo inicial ya soportado | Sí, **por lote y manual** (API `POST /lots/activate-manual`), con pertenencia de lote (AC-R67-11) y cadena (GA-REM-040 fase 3) | `service.py:627-636` |
| 7 | Específico de otro dominio | No — dominio lotes; cubre campos de producción/reproducción y broiler recibido | `models.py:37-80` |
| 8 | Reutilizable | **Sí, como snapshot base** | — |
| 9 | Colisiona con GA-REQ-061 | No; es la misma semántica (saldo vivo al corte). **Prohibido crear un segundo concepto** | mandato §9 |
| 10 | Caso parcial | Sí: 1 lote por llamada; sin batch/Excel/staging/aprobación/checksum/provenance; `default=0` impide UNKNOWN; sin correcciones formales post-apply; sin campos de incubación en curso | comparación con ACs |

## 2 · Veredicto

**`PARTIAL_REUSE`**

- `OpeningBalance` (+ `activate_manual` + consulta de balance) es la **pieza canónica** del opening y se **extiende** para GA-REQ-061; NO se crea concepto paralelo de “saldo inicial”.
- Extensiones PROPOSED (en la tranche T14, no ahora):
  1. Enlace a `CutoverBatch`/`CutoverItem` (batch, aprobación, apply transaccional).
  2. Semántica `KNOWN|UNKNOWN|NOT_APPLICABLE` por métrica (conservando `0` = cero conocido; hoy `default=0` no distingue).
  3. Provenance: `source_system`, `source_reference`, `legacy_lot_code`, `source_checksum_sha256`.
  4. Inmutabilidad post-APPLY + `OpeningBalanceCorrection` (before/after/delta/reason) reutilizando el framework de correcciones.
  5. Campos de incubación en curso (etapa de carga, huevos en proceso…) tras auditoría fina del dominio de incubadora.
- **Compatibilidad**: el endpoint y el modelo actuales siguen funcionando durante la transición; la activación manual 1-lote queda como caso particular del batch (o se documenta su convivencia si T14 lo decide).
