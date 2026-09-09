# MATRIZ DE ESTADOS OPERATIVOS, CIERRES, CORRECCIÓN Y REVERSO

**Auditoría 360°** · 2026-09-09 · base `7310adb` · **AUDIT ONLY**

Fuentes de autoridad: Recomendación central §17 (reglas), §18 (estados), §21 (división) ·
`docs/12 §4, §6` · `docs/02 §4, §5` · `spec.md §5 BR-01…BR-16` · código `EventStatus`
(`operations/models.py:57-70`), `operations/service.py`, `review/service.py`,
`corrections/service.py`, `lots/service.py`, `operations/validators.py`.

---

## 1. Catálogo de estados: tres fuentes y el código

| Rec. §18 | `docs/12 §4` | `EventStatus` | ¿Se asigna en código? | Semántica real | Hallazgo |
|---|---|---|:--:|---|---|
| BORRADOR | 1 Borrador | `DRAFT` | **nunca** (`create` fija `REGISTERED`, `service.py:107`; ninguna línea asigna `DRAFT`) | estado muerto: `update_event` lo admite (`:893`) pero nada lo produce | `H360-P02` · P3 |
| REGISTRADO_EN_GRANJA | 2 Registrado | `REGISTERED` | `create` `:107` | ✓ | — |
| EN_REVISION_ADMINISTRATIVA | 3 Enviado a revisión · 4 En revisión | `PENDING_REVIEW` (`submit` `:912`; lote de revisión `review/service.py:180`) · `IN_REVIEW` (`start_review` `:220`) | ✓ | ✓ | — |
| OBSERVADO | 5 Devuelto | `RETURNED` (`return_to_operator` `:248`) | ✓ | el operador puede **editar** (`:893`) pero **no reenviar**: `submit` exige `REGISTERED` (`:910`); la única salida es `corrections` → `CORRECTED` | `H360-P03` · P1 |
| CORREGIDO | 6 Corregido | `CORRECTED` | `corrections/service.py:69` **y** `complete_review` cuando `approval_levels > 1` (`review/service.py:292`) | **doble semántica**: «corregido» también significa «revisado, pendiente del aprobador» aunque no haya habido corrección; la auditoría registra `corrected` en registros nunca corregidos | `H360-P06` · P2 |
| APROBADO | 7 Aprobado | `APPROVED` | `approve` `:430`; `complete_review` con 1 nivel `:287` | ✓ `BR-13` | — |
| — | 8 Rechazado → «Operador reenvía (corregido)» | `REJECTED` (`reject` `:456`) | ✓ | **terminal**: no editable (`:893`), no corregible (`corrections/service.py:34`), no reenviable (`:910`) | `H360-P03` · `AOD-09` |
| — | 9 Consolidado | `CONSOLIDATED` | `consolidate_approved` `sap/service.py:224` | ✓ `R6` solo desde `APPROVED` | — |
| ENVIADO_A_SAP | 10 | `SENT_TO_SAP` | **nunca** (regla absoluta `GA-REM-010`: sin entrega verificada no hay `sent_to_sap`) | inalcanzable hasta `GA-REM-017` | coherente |
| CONTABILIZADO_EN_SAP | 11 | `SAP_CONFIRMED` | **nunca** | inalcanzable | coherente |
| RECHAZADO_POR_SAP | 12 | `SAP_ERROR` | **nunca** | inalcanzable; el error vive en `PayloadStatus.FAILED` | coherente |
| REPROCESADO | — | — | — | **no existe** (`PayloadStatus.RETRYING` es del payload, no del registro) | G-R13 vigente · P2 |
| ANULADO / REVERSADO | 13 Anulado «solo administrador, requiere motivo» | `CANCELLED` (`cancel_event` `:921`) | ✓ | **sin motivo obligatorio** (la ruta no recibe cuerpo; comentario fijo «Evento cancelado») · permiso `operations:create`, no administrador · guarda omite `SAP_CONFIRMED` y `SAP_ERROR` | `H360-P04` · P2 (latente P1) |

## 2. Transiciones implementadas (grafo real)

```
create ─────────────► REGISTERED ──submit──► PENDING_REVIEW ──start──► IN_REVIEW
                          ▲  │                                            │
                 update ──┘  │                    return ◄────────────────┤
                             │                       │                    ├─ complete (1 nivel) ──► APPROVED
                             │                    RETURNED ──correct──► CORRECTED ◄─ complete (≥2 niveles)
                             │                                            │            │
                             │                                  approve ──┘   reject ──► REJECTED (terminal)
                             │                                            ▼
                             └─ cancel (no desde APPROVED/CONSOLIDATED/SENT_TO_SAP) ──► CANCELLED
APPROVED ──consolidate──► CONSOLIDATED ──export──► [SapPayload PREPARED|CONFIRMED|FAILED]   (el evento no cambia)
```

Guardas verificadas: `BR-13` (solo `APPROVED` consolida, `sap/service.py:160`) · `BR-14` segregación
configurable por paso (`review/service.py:27-60`, `RC-03`) · `BR-15` `validate_sap_edit_lock` en
`update_event` (`:889`) · corrección solo en `REGISTERED, PENDING_REVIEW, IN_REVIEW, RETURNED`
(`corrections/service.py:34`, `RR-01`).

## 3. Cierre de lote

| Aspecto | Fuente | Implementación | Estado |
|---|---|---|---|
| Quién cierra | Rec. §21: SAP «cerrar lotes»; Rec. §13: app captura «datos de cierre del lote» | `POST /lots/{id}/close` (`lots:create`) fija `status=closed`, `end_date` (`lots/service.py:220-329`) | **cierre operativo local**; su relación con la liquidación SAP no está declarada → `AOD-08` |
| Precondiciones | `BR-05` resumen final · `docs/12 R7` sin registros sin aprobar | `validate_lot_closure` (≥1 pesaje y ≥1 alimento) · `validate_lot_records_approved` · solo `ACTIVE` | ✓ (`GA-REM-029`, `GA-REM-036`) |
| Resumen | Rec. §13: mortalidad, consumo, FCR final, salida | `total_mortality`, `total_feed_kg`, `total_eggs`, `total_events`, `approved_events`, `age_days` | **sin FCR ni peso final** aunque `BR-05` exige pesaje precisamente para el FCR (comentario `:236-238`) → `H360-P08` · P2 |
| Evento `LOT_CLOSURE` | `EventType.LOT_CLOSURE` | valida `BR-05` pero **no cierra** (comentario `lots/service.py:233-237`) | dos artefactos llamados «cierre»: un evento aprobable y un endpoint que cambia estado; `docs/12` no distingue → `H360-P09` · P3 |
| Después del cierre | `BR-07` | `validate_lot_active` rechaza eventos sobre lote no `active` | ✓ |
| Reapertura / `LotStatus.CANCELLED` | — | ninguna ruta asigna `cancelled`; no hay reapertura | estado declarado sin productor · P3 |

## 4. Invariante de población y reglas de validación (Rec. §17 + `spec §5`)

Saldo (`validators.py:21-78`): `OpeningBalance` + Σ(`bird_reception`, `birth_registration`) −
Σ(`mortality_recording`, `cull_recording`, `bird_exit`, `chick_dispatch`); `bird_transfer` y
`bird_distribution` neutros (`RC-02`). **Qué lo protege:**

| Salida del lote | ¿Validada contra el saldo? | Dónde | Consecuencia |
|---|:--:|---|---|
| `mortality_recording` | **sí** `BR-01` | `service.py:687` → `validate_mortality` | ✓ |
| `chick_dispatch` | sí `BR-04` (contra nacidos viables) | `:704` | ✓ |
| `cull_recording` (descarte) | **no** | ningún validador por tipo (`:680-708`) | **saldo negativo posible** |
| `bird_exit` (salida a planta / venta) | **no** | ídem | **saldo negativo posible**; es la salida principal del engorde |
| `grandparent_import` | no está en `in_types` | `validators.py:36` | si el evento lleva `BirdMovement`, las abuelas importadas **no entran** al saldo (verificar con `P-01`: su E2E pasa, luego usa `bird_reception` o activación manual) |

→ **`H360-P01` · P1 · `MODEL/RULE DEFECT`**: la regla del encargo «la población nunca es
negativa» está implementada para una sola de las tres salidas humanas. Ningún test la cubre
para `cull_recording` ni `bird_exit` (`grep validate_cull\|validate_exit backend/tests` → 0).

Las 17 reglas de la Recomendación §17, estado en `7310adb`:

| Regla | Implementación | Estado |
|---|---|---|
| Cantidad recibida > OC sin autorización | `BR-18` acumulado (`OD-04`) | ✓ |
| Capacidad de galpón excedida | `BR-17` | ✓ (recepción y distribución) |
| Galpón / material / almacén / centro inexistente en SAP | FK local | placeholder (`SAP_DEFERRED`) |
| Lote inexistente o cerrado | `BR-07` | ✓ |
| Unidad de medida inválida | — | ✗ `H360-B06` |
| Consumo > stock · consumo sanitario sin stock | — | `SAP_DEFERRED` |
| Mortalidad > población actual | `BR-01` | ✓ (**descarte y salida no**, `H360-P01`) |
| Vacuna sin material válido | FK `vaccine_id` | placeholder |
| Fecha en período SAP cerrado | `BR-19` 90 días fijos | placeholder `HARD_CODED` (`H360-S06`) |
| Registro sin usuario responsable | `registered_by_id` NOT NULL | ✓ |
| Registro sin aprobación | `BR-13` | ✓ |
| Duplicidad de envío | `BR-12` SHA-256 + `external_transaction_id` | ✓ (preparación) |
| Corrección sobre aprobado sin versión/reverso | `corrections:34` prohíbe; **reverso inexistente** | ✓ prohibición · ✗ mecanismo → `H360-P05` |

Validaciones administrativas de recepción (Rec. §6): OC existe ✓ · cantidad ≤ OC ✓ · distribución
≤ capacidad ✓ · **hembras + machos + mortalidad + rechazo cuadran contra recibido ✗** (0 referencias
a cuadre/rechazo en `operations/*.py`) → `H360-B01` · lote definido ✓ · **pesos en rango ✗** (la
alerta de curva solo evalúa `weight_recording`, `service.py:520-575`) → `H360-B02` · **evidencia
existe ✗** (no es precondición de aprobación) → `H360-B04` · responsable aprueba ✓.

## 5. Corrección, anulación y reverso

| Capacidad | Fuente | Implementación | Estado |
|---|---|---|---|
| Corrección auditada (`BR-09`, `RR-01`) | `docs/12 §8` | escribe el valor, conserva original en `correction_logs`, campos acotados (`campos_corregibles`), estado → `CORRECTED` | ✓ |
| Segregación corrector ≠ aprobador (`docs/12 R2`) | `docs/12 §6` | `_exigir_segregacion` compara con `registered_by_id`, **no con `corrected_by_id`** | **✗** `H360-P10` · P2 |
| Anulación con motivo, solo administrador (`docs/12 §4` fila 13) | `docs/12` | `cancel` sin motivo, permiso `operations:create` | ✗ `H360-P04` |
| Reverso con registro compensatorio (`BR-16`, Rec. §24 «Reverso: cómo se anula») | `spec §5` | tabla `reversals` sin servicio/ruta | ✗ `H360-P05` · P1 antes de `GA-REM-017` |
| Versión (`OperationalEvent.version`) | `docs/13` «versión aprobada» | columna existe; `grep "version +=\|version=" operations/service.py` → no se incrementa | ✗ `H360-P11` · P3 |

## 6. Aprobación

`approval_steps` por empresa y rol (`seed-defaults` crea 1–3 pasos por nombre de rol, `H360-B08`),
`companies.approval_levels` (default 2) decide si `complete_review` aprueba o deja en
`CORRECTED`; `approvals/*` aprueba/rechaza desde `CORRECTED` o `IN_REVIEW`; lotes
(`review/batches`, `batch-approve`, `batch-reject`); rechazo con motivo obligatorio ✓
(`observations: str` requerido en `reject`). Lo que `docs/12 §5` llama «nivel 3» no tiene un
estado intermedio propio: dos aprobadores sucesivos no dejan huella de estado distinta entre
el primero y el segundo (solo `approval_actions`). Aceptable; se registra como observación.

## 7. Resumen de hallazgos de esta matriz

| ID | Sev. | Clase | Título | Evidencia |
|---|:--:|---|---|---|
| `H360-P01` | **P1** | RULE DEFECT | descarte y salida de aves no validan contra el saldo → población negativa posible | `service.py:680-708`, `validators.py:36-60` |
| `H360-P03` | P1 | CONTRACT DEFECT + `REQUIREMENT_CONFLICT` | `RETURNED` no se reenvía; `REJECTED` es terminal; `docs/12 §4` dice lo contrario | `service.py:893,910`, `corrections:34` |
| `H360-P04` | P2 (P1 con SAP real) | CONTRACT DEFECT | `cancel` sin motivo, sin restricción de rol, y no bloquea `SAP_CONFIRMED`/`SAP_ERROR` | `service.py:921-925` |
| `H360-P05` | P1 (SAP) | MODEL DEFECT | `reversals` sin servicio ni ruta; `BR-16` sin mecanismo | `models.py:328`, 0 usos |
| `H360-P06` | P2 | SEMANTIC DEFECT | `CORRECTED` usado como «pendiente de aprobador» | `review/service.py:292` |
| `H360-P08` | P2 | CONTRACT GAP | resumen de cierre sin FCR ni peso final | `lots/service.py:310-320` |
| `H360-P10` | P2 | RULE GAP | `docs/12 R2` (corrector no aprueba) no implementada | `review/service.py:45` |
| `H360-P02`, `P09`, `P11` | P3 | — | `DRAFT` muerto · dos «cierres» · `version` no incrementa | — |
