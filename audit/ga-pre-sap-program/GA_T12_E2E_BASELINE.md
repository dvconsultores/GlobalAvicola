# T12 · RECERTIFICACIÓN E2E — BASELINE PRE-DECISIÓN WAVE C

Fecha: 2026-09-15 · Estado: **BASELINE VERDE · CLOSURE BLOQUEADO POR OWNER GATE
`AOD-08`/`AOD-10`** (Encuesta `SCHEDULED (antes de T12)` en
`GA_OWNER_GATE_QUEUE.md:97`).

## 1 · Corrida de recertificación (producto remediado T1–T14)

- Comando: `bash scripts_e2e.sh e2e/` (stack aislado 8099/5199, base de pruebas
  reseteada, Chromium único — entorno de certificación).
- Resultado: **111/111 passed · 0 failed · 2.2m** · 18 specs
  (`test-results/` y log serializado `evidence/t12/e2e-full-111.log`).
- Matriz por proceso (todos ✓):
  - **proceso-01** recepción de aves · **proceso-02** control producción diario ·
    **proceso-03** revisión/corrección/aprobación.
  - **P-01** progenitoras cría · **P-02** progenitoras producción huevo ·
    **P-03** curvas UI + reproductoras cría · **P-04** reproductoras huevo
    fértil · **P-05** incubación · **P-06** pollo de engorde ·
    **P-09** auditoría interna · **P-10** trazabilidad generacional ·
    **P-11** activación manual de lotes · **P-12** datos maestros ·
    **P-13** roles y permisos · **P-14** notificaciones ·
    **P-15** reportes e indicadores.
  - **P-16** cutover operacional / Cargas Iniciales (nuevo, GA-REQ-061):
    4/4 BUs con journals (golden broiler 9.965/535/UNKNOWN + negativas).

## 2 · Suites de regresión al cierre

| Suite | Resultado |
|---|---|
| BE full (`scripts/run_tests.sh`) | **1428 / 0F / 49S** (21:17) |
| FE full (`vitest run`) | **524 / 524** |
| Build FE (`tsc -b && vite build`) | **EXIT 0** |
| E2E procesos (esta corrida) | **111 / 111** |

## 3 · OWNER GATE — `AOD-08` / `AOD-10` (Wave C: cierre/FCR y fórmulas KPI)

**Pregunta del propietario pendiente** (`GA_OWNER_GATE_QUEUE.md:97`, roadmap §T12):
¿se **corrigen** las fórmulas KPI abiertas o se **aceptan documentadas**? Si
«corregir» ⇒ redactar spec **`GA-REM-022`** (no redactada aún) y micro-tranche
previa a T12; afecta a **P-15** y contamina el **IPE** (hoy correcto en escala,
no en valor).

Hallazgos vivos (ola C, P1/P2 — `evidence/E_domain_ledger.md:210-213,288`):

| Ref | Hallazgo | Dónde | Prioridad |
|---|---|---|---|
| **R-131** | FCR = `feed_kg/1000` y edad con `date.today()` incluso en lotes cerrados (debe usar `end_date`) | `reports/service.py:161,605,660` | P1 |
| **R-132** | `% mortalidad` con denominador solo `OpeningBalance` ⇒ 0 % / viabilidad 100 % en lotes por recepción; tendencia sin filtro de estado (E-24) | `reports/service.py:143-146`; `dashboard/service.py:185-200` | **P1** |
| **R-133** | Vacunación cuenta eventos `/1000` | `reports/service.py:490-499` | P2 |
| **R-134** | AFCR suma `quantity` como gramos; sin peso de muertos | `reports/service.py:554-566` | P2 |
| **R-141** | Agregados sin filtro de estado (familia E-24/E-05) | `reports/service.py` varios | P1 (parcial) |

**Impacto**: los indicadores expuestos hoy **pasan** las suites (P-15 ✓) pero su
**valor** puede ser incorrecto en tres escenarios reales: lotes activados por
recepción (saldo ≠ apertura), lotes cerrados (edad), y agregaciones con eventos
cancelados. Los E2E no lo detectan porque no afirman sobre el valor de esos KPIs.

## 4 · Opciones para el propietario

1. **Corregir mínimo (recomendado por ingeniería)**: R-131 (edad/FCR) + R-132
   (denominador de mortalidad) — P1 con impacto operativo directo; micro-tranche
   con RED sobre los dos casos reales (lote por recepción; lote cerrado) y
   re-recertificación P-15. R-133/R-134/R-141 quedan `ACEPTADO_DOCUMENTADO`.
2. **Corregir completo**: GA-REM-022 con R-131…R-134 + R-141; mayor alcance y
   tiempo; re-recertifica P-15 y dashboard.
3. **Aceptar documentado todo**: T12 cierra con limitaciones KPI documentadas
   (IPE contaminado aceptado); riesgo residual trasladado a fase SAP/UAT.

La recertificación E2E **no puede declararse cerrada** hasta registrar esta
decisión (criterio de salida de T12 en el roadmap: «paridad runtime + decisión
Wave C»).

## 5 · Artefactos

- `evidence/t12/e2e-full-111.log` — corrida completa serializada.
- Journals del cutover: `audit/ga-claude-final-audit/specs/GA-REQ-061/evidence/e2e/e2e-*.json`.
- Suites BE/FE/build: `specs/GA-REQ-061/evidence/green/be-full-1428.log` y `evidence/fe/`.
