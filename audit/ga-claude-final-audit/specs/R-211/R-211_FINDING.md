# R-211 · FINDING — BR-17 VALIDA LA SUMA CONTRA UN SOLO GALPÓN MIENTRAS LA UI DISTRIBUYE POR GALPÓN

| Campo | Valor |
|---|---|
| **ID canónico** | **R-211** (asignado en `GA_CLAUDE_DISCOVERED_GAP_SPEC_REGISTER.md §0`; máximo previo R-189) |
| **Título** | La recepción captura filas por galpón (`target_house_id` por fila) y el evento declara **un** `house_id` (primera fila, F-01e); `validate_house_capacity` compara la **Σ total** contra la capacidad de ese único galpón ⇒ recepciones válidas multi-galpón rechazadas (400 BR-17) |
| **Severidad** | **P2** (§49: regla de capacidad mal aplicada; bloquea recepción multi-galpón, patrón legítimo de P-03/P-06) |
| **Clase** | `REQUEST_CONTRACT` (regla BE vs estructura UI) / `DATA_INTEGRITY` |
| **Proceso** | P-03 (recepción reproductoras), P-06 (recepción engorde), P-01 |
| **Fecha · HEAD** | 2026-09-13 · `c0b4afc` (== `origin/main`) |
| **Familia** | B-16 (informe B); E-04 (informe E); vecino `R-176` («capacidad estática», BACKLOG) |
| **Paquete** | `audit/ga-claude-final-audit/specs/R-211/` (completo, 6 ficheros) |
| **GA-REM** | a asignar al autorizar; siguiente libre GA-REM-043 |
| **Bloquea SAP** | **SÍ** (recepción multi-galpón bloqueada; datos de población por galpón) |
| **UAT del propietario** | sí, para C-02 (¿capacidad acumulada por galpón o por evento?) — decisión acotada |

## 1 · Evidencia

### 1.1 Código (verificado en HEAD)

- `frontend/src/pages/operations/OperationFormPage.tsx:725-772` — filas de recepción con `target_house_id` por galpón; `:392-393` — `house_id` del evento = primer `target_house_id` (F-01e).
- `backend/app/operations/validators.py:712-725` — `validate_house_capacity`: compara **Σ cantidades del evento** contra `House.capacity` del único `house_id` del evento; no acumula por galpón ni por evento previo (`service.py:900-902` la invoca).
- `E_domain_ledger.md §1.3` (E-04): N recepciones al mismo galpón pueden superar la capacidad (no hay ledger por galpón; RR-02 «distribución/traslado neutros»).

### 1.2 Evidencia de defecto

Dos galpones de 500: filas `[{target_house_id:1, quantity:500},{target_house_id:2, quantity:500}]` ⇒ `house_id=1`, Σ=1000 ⇒ **400 BR-17** «excede la capacidad del galpón (500)» — aunque cada galpón recibe 500 (válido).

## 2 · Causa raíz

BR-17 se implementó cuando el evento declaraba un único galpón; al añadir filas por galpón (distribución/recepción multi-galpon) la validación no se actualizó para comprobar **por galpón de fila** (ni para acumular por galpón si el dominio lo decide).

## 3 · Impacto

- Recepciones multi-galpón legítimas rechazadas (operación real de granjas con varios galpones).
- Capacidad inherentemente no acumulada (E-04): N eventos pueden sobrepasar el galpón (hueco separado, decisión C-02).
- Fixtures de suites (p03) dependen del patrón.

## 4 · Dedup realizada (§48)

| Registro | Resultado |
|---|---|
| R-001…R-189 | `R-176` cita «capacidad estática» como observación; sin hallazgo propio. |
| Informes B/E | B-16 + E-04 coinciden; sin registro en backlog. |

Conclusión: **nuevo**; ID asignado **R-211**.

## 5 · Propietario sugerido

Backend (`validators`) + dominio (decisión C-02). Frontend sin cambio salvo mensajes si aplica.

## 6 · Bloquea SAP y por qué

**SÍ**: la capacidad es regla de población/fiabilidad del dato; y sin ella la recepción multi-galpón no puede registrarse por UI.

## 7 · Interdependencias

- **R-190** (galpón del evento): comparten el modelo de filas/`house_id`; tranche contigua.
- **C-02** (acumulado): si el dominio decide acumular, requiere contabilidad por galpón (nueva consulta agregada); por defecto, la spec corrige el error de comparación y deja la acumulación como decisión.
- **RR-02**: neutralidad de distribución/traslado (intacta).
