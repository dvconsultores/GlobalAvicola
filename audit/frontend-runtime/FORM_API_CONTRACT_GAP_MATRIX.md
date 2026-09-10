# FORM ↔ API CONTRACT GAP MATRIX

**2026-09-10** · base `3808ed5` · compara los formularios operativos del frontend con el esquema vigente del backend (`operations/schemas.py`, `validators.py`). El caso crítico: el **runtime sirve la generación 2026-09-05** y el **backend desplegado ya está en la 2026-09-10**.

## 1. Diferencias que rompen el flujo EN EL RUNTIME HOY (P1)

| Formulario | Campo/regla | Frontend local (HEAD) | Backend vigente | Runtime 09-05 (lo que un usuario usa hoy) | Impacto |
|---|---|---|---|---|---|
| Recepción de aves — **reproductoras** | `received_total`, `dead_on_arrival`, `rejected_on_arrival` (BR-20) | ✅ los envía (obligatorios condicionados) | **obligatorios**; cuadre exacto; la ausencia no es 0 | ❌ no los envía | **400 BR-20 — no se puede registrar recepción de reproductoras** |
| Nacimiento — **incubadora** | fila «Total» + desglose (BR-21); `chicks_healthy`/`chicks_weak` | ✅ fila total eliminada; sanos/débiles obligatorios | **prohíbe total duplicado; exige sanos/débiles** | ❌ duplica el total; no envía sanos/débiles | **400 BR-21 — no se puede registrar nacimiento** |
| Importación de abuelas — **Progenitoras** | `extra_data.import_plan` (BR-22) | ✅ formulario tipado completo | **obligatorio** y validado (identidades, OC, proveedor) | ❌ enviaba claves sueltas en `extra_data` | **400 BR-22 — no se puede registrar importación** |
| Despacho de huevos | `egg_type` fértil único (BR-02); cantidad > 0 (BR-04) | ✅ fila única fértil | **rechaza tipos no fértiles; 0 rechazado** | ❌ permite tipos/cantidades hoy rechazadas | probable **400 BR-02/BR-04** |
| Muestra de recepción | `sample_size` (R-168) | ✅ como dato del evento | persiste `sample_size` | ❌ por-galpón descartado | pérdida silenciosa (histórica) |
| Tolerancia ±10 % | Aviso en recepción (R-169) | ✅ retirada | sin tal regla (cantidad vs OC gobierna por BR-18) | ❌ inyecta «⚠️ ALERTA…» en `observations` | dato contaminado + veredicto falso |

## 2. Reglas vigentes del backend que el formulario local ya satisface (paridad)

| Regla | Exigencia | Estado local |
|---|---|---|
| `BR-08` ubicación / `BR-06/19` fecha / `BR-11` documento SAP | revalidación en edición y corrección (R-176) | ✅ |
| `BR-17/18` capacidad y acumulado de OC | revalidación sobre estado candidato | ✅ |
| `BR-01/B.2/D.1.4` saldo | guarda central de edición/contrapartida (R-173) | ✅ |
| `BR-14` segregación | backend; UI presenta la negativa | ✅ (backend) |
| `R-177` (`AOD-24`) tipo de huevo ≠ ovoscopía | **sin decidir** | formulario de ovoscopía con etiquetas crudas en algunos casos |

## 3. Campos de sesión/contrato que el formulario NO usa aún

| Campo de sesión (fase 8) | ¿Consumido por el frontend? | Nota |
|---|:--:|---|
| `permissions` | ❌ | T-040-23 (navegación dinámica) |
| `company_business_units` | ❌ | T-040-21 (pantalla) |
| `granted_business_units` | ❌ | T-040-22 |
| `effective_business_units` | ❌ | T-040-23 (menú) |
| `effective_company_id` | ⚠️ sólo vía `company_name` de `/me` | selector |

## 4. Contratos divergentes adicionales (runtime vs backend nuevo)

| Superficie | Runtime 09-05 | Backend nuevo | Efecto |
|---|---|---|---|
| `/audit` filtros | pestañas que no filtraban (R-82) | filtros reales `action`/`module` | UI vieja muestra datos completos con apariencia de filtro |
| `/users` estados | `Promise.all` + `catch{}` (F-E) | fix R-120 local | denegación indistinguible de vacío |
| Despacho | formulario multi-tipo | solo fértil | posible 400 |
| Corrección/rechazo | flujo previo a R-135 | REJECTED corregible/reenviable | la UI vieja no ofrece reenvío tras rechazo |

## 5. Fuentes

`operations/schemas.py` · `operations/validators.py` (BR-20/21/22, R-168/169/170/171/172/174) · `OperationFormPage.tsx` (HEAD) · bundles desplegado/local (`evidence/BUNDLE_HASHES.txt`) · `R135_R143_STATE_CORRECTION_MATRIX.md` · `R176_…PARITY_MATRIX.md` · `GA_REM_021_B01/B02` matrices.
