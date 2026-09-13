# R-211 · SPEC — CAPACIDAD DEL GALPÓN POR FILA (BR-17) Y DECISIÓN DE ACUMULACIÓN

Fecha: 2026-09-13 · Hallazgo canónico: **R-211** (P2 · bloquea) · HEAD `c0b4afc` · Origen B-16/E-04 · Registro G-23. Secciones §47.

## 1 · Contexto

La recepción de aves captura filas por galpón. El backend valida BR-17 con la Σ del evento contra un solo galpón (`house_id` del evento). La UI asigna `house_id = primer target_house_id` (F-01e). Resultado: falso positivo de exceso en multi-galpón.

## 2 · Evidencia

`R-211_FINDING.md §1`: `OperationFormPage.tsx:725-772,392-393`; `validators.py:712-725`; `service.py:900-902`; `E_domain_ledger.md` (E-04).

## 3 · Causa raíz

Validación heredada del modelo mono-galpón; sin agregación por `target_house_id`.

## 4 · Impacto de negocio

Recepción multi-galpón imposible por UI/API con Σ > capacidad de un galpón; riesgo inverso (capacidad no acumulada) si N eventos llenan el mismo galpón.

## 5 · Comportamiento actual

| Escenario | Hoy |
|---|---|
| Galpones 500+500, filas 500/500 (house_id=1) | **400 BR-17** (falso positivo) |
| Galpón 500, un evento de 500 | 201 |
| Dos eventos de 500 al mismo galpón | 201 (exceso real no detectado; E-04) |

## 6 · Comportamiento esperado

1. **Corrección base (C-01)**: BR-17 compara, **por cada `target_house_id` de las filas**, la Σ de cantidades de ese galpón contra su `capacity`; el `house_id` del evento deja de usarse para la Σ.
2. **Acumulación (C-02, decisión del propietario)**: opción A (por defecto propuesto) = validar solo el evento (corrige el falso positivo; el exceso acumulado entre eventos queda como residual documentado); opción B = acumular por galpón (Σ eventos vigentes `≠ CANCELLED` contra `capacity`) — requiere consulta agregada por galpón y pruebas de concurrencia (sin lock nuevo salvo decisión).
3. Mensaje del 400: indica el galpón y la capacidad concreta (`Galpón X capacidad N; recibidas M`).
4. Sin cambio del contrato del payload (mismas filas).

## 7 · Alcance

- `backend/app/operations/validators.py:712-725` + llamada (`service.py:900-902`).
- Tests: `backend/tests/test_r211_house_capacity_rows.py` (nuevo) + regresión `test_house_capacity*`/`test_reception_*`.
- Si C-02=B: consulta agregada por galpón (solo lectura de eventos vigentes) + tests de acumulación.
- Sin migración; sin endpoint; sin permiso.

## 8 · Fuera de alcance

- Ledger por galpón completo (RR-02; solo lo que C-02 decida para BR-17).
- `bird_distribution`/`bird_transfer` (neutros; si su BR-17 por fila se decide, se evalúa en la misma tranche con el mismo helper).
- UI (salvo mensaje si se decide mostrarlo; hoy el 400 se renderiza seguro).

## 9 · Impacto frontend

Ninguno obligatorio; regresión de recepción multi-galpón por UI (fixture).

## 10 · Impacto backend

`validators.py` (reemplazo de la comparación única por agrupación por fila). Sin modelos.

## 11 · Contrato frontend↔backend

Mismo `POST /operations`. Cambia el resultado del caso multi-galpón (400→201) y, si C-02=B, el acumulado entre eventos. Mensaje del 400 más específico.

## 12 · Impacto en datos

Ninguno estructural. Si C-02=B, se consultan eventos vigentes (lectura).

## 13 · Seguridad

Sin cambio (tenencia de galpones por fila ya verificada, `service.py:863-867`).

## 14 · Inquilino · 15 · Unidad de negocio · 16 · RBAC

Sin cambio.

## 17 · Transacciones

La validación corre dentro de la transacción del alta. Si C-02=B, la consulta agregada es de lectura; concurrencia entre dos eventos simultáneos al mismo galpón no bloquea (residual documentado salvo decisión de lock).

## 18 · Auditoría

Sin cambio.

## 19 · i18n

Mensaje 400 en ES (patrón); sin claves frontend nuevas.

## 20 · Escritorio · 21 · Móvil

Sin cambio de UI; regresión de captura multi-galpón en ambos.

## 22 · Manejo de errores

`400 BR-17` solo cuando un galpón concreto excede su capacidad; mensaje con galpón/capacidad; sin nuevos códigos.

## 23 · Impacto de migración

Ninguna.

## 24 · Impacto SAP

Indirecto (población por galpón como dato de origen).

## 25 · Compatibilidad hacia atrás

- Recepción mono-galpón: idéntico.
- Multi-galpón válida: 400→201 (corrección).
- Si C-02=B: eventos que antes pasaban pueden rechazarse (endurecimiento decidido; documentar en el acta).

## 26 · Criterios de aceptación

| AC | Criterio |
|---|---|
| AC-R211-01 | Galpones 500+500, filas 500/500 ⇒ **201** (hoy 400) |
| AC-R211-02 | Una fila excede el galpón de esa fila ⇒ 400 con galpón y capacidad en el mensaje |
| AC-R211-03 | Mono-galpón excedido ⇒ 400 sin cambio (control) |
| AC-R211-04 | (C-02=B) Dos eventos de 500 al galpón 500 ⇒ segundo 400; (C-02=A) 201 y residual documentado |
| AC-R211-05 | `bird_distribution` con filas multi-galpón no se rompe (regresión) |
| AC-R211-06 | API con `house_id` del evento distinto de las filas: la validación usa las filas (documentado) |
| AC-R211-07 | Sin migración/endpoint/permiso |
| AC-R211-08 | Regresión: `test_population_invariant.py`, `test_reception_reconciliation.py`, suites de recepción p03/p06 (tras GA-GOV-03) verdes |

## 27 · Pruebas RED→GREEN

`§1`: `test_r211_01_dos_galpones_cada_uno_en_capacidad_es_201` (rojo), `test_r211_02_fila_excedida_es_400_con_galpon` (rojo por mensaje), `test_r211_03_mono_galpon_control` (verde), `test_r211_04_acumulado` (según C-02).

## 28 · E2E

`§2`: `R211-RT-01…04` (API + UI local). Artefacto `evidence/r211/`.

## 29 · UAT

C-02 (decisión acotada) + verificación técnica de recepción multi-galpón por UI con el propietario/operador (10 min, agrupable con R-205/R-190).

## 30 · Criterios de cierre

RED válida · GREEN local (según C-02) · sensibilidad (S1: restaurar Σ contra `house_id` ⇒ AC-01 roja) · sin migración/endpoint/permiso · R-211 → `CLOSED` con GA-REM asignado.
