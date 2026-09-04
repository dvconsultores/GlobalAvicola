# RC RESOLUTION REPORT — Wave 1.5 · Track A

**Fecha** 2026-09-03 · **Alcance** `RC-01`, `RC-02`, `RC-03`, `RC-05`, `RC-07`
**Matriz completa y evidencia** → `audit/remediation/REQUIREMENT_CONFLICT_RESOLUTION.md`

---

## 1. Resultado

```
RC en alcance ....................... 5
RESOLVED_BY_EVIDENCE ................ 4   (RC-01, RC-02, RC-03, RC-05)
OWNER_DECISION_REQUIRED ............. 1   (RC-07)
OBSOLETE_CONFLICT ................... 0
Specs desbloqueadas ................. 5   (005, 006, 007, 012, 018)
Decisiones abiertas del propietario . 3   (OD-01, OD-02, OD-03) — ninguna bloquea Wave 2
Hallazgos nuevos .................... 4   (1 P0, 2 P1, 1 P2)
Código modificado ................... 0
```

**Cuatro de los cinco conflictos no requerían una decisión de negocio.** Requerían leer
las fuentes en orden y comprobar qué dice cada una. Tres de ellos ni siquiera eran
conflictos: eran omisiones de la spec (`RC-01`), imposibilidades estructurales del esquema
(`RC-02`) o números aplicados a operaciones distintas que nunca compitieron entre sí
(`RC-05`).

---

## 2. Reglas vigentes fijadas

| Regla | Enunciado abreviado |
|---|---|
| `RR-01` | La corrección escribe el valor en el acto y deja el registro en `CORRECTED`; `CORRECTED` **no** es aprobado y sigue requiriendo aprobación. Sobre `APPROVED` y posteriores: reverso o nueva versión, nunca edición directa. |
| `RR-02` | `bird_transfer` y `bird_distribution` son intra-lote entre galpones y **neutros** en el balance. El movimiento entre lotes se expresa con `bird_exit` + `bird_reception`. |
| `RR-03` | `BR-14` es configurable por paso mediante `ApprovalStep.require_segregation`, **por defecto `True`**. Toda ruta de aprobación debe consultarla; ninguna puede eludirla. |
| `RR-05` | Política única de longitud mínima **8**, idéntica en alta, cambio y restablecimiento. El *login* no impone longitud. Un cambio que no cambia nada debe fallar, no responder `200`. |
| `RR-07` | La captura, validación e indicador de mortalidad son firmes y **no dependen de `RC-07`**. Solo el mapeo a documento SAP queda supeditado a la decisión del propietario. |

---

## 3. Por qué `RC-07` sí necesita al propietario

Los otros cuatro se resolvieron porque alguna fuente por encima de la implementación se
pronunciaba. `RC-07` es distinto: **la fuente de nivel 2 se pronuncia para decir que la
decisión no está tomada.** El documento del cliente dedica una sección entera —«25.
Decisión crítica antes de avanzar»— a enumerar cinco definiciones que la empresa debe
cerrar, y la cuarta es exactamente este conflicto. Resolverlo por criterio técnico sería
sustituir una decisión contable de la empresa por una preferencia de ingeniería.

Lo que sí se hizo fue **acotar su radio**: `RC-07` bloqueaba `GA-REM-005` entera; ahora
bloquea únicamente el mapeo de mortalidad dentro de `GA-REM-017`, que ya estaba detenida
por el contrato técnico SAP. La decisión pendiente dejó de estar en el camino crítico.

---

## 4. Cambios de estado de las specs

| Spec | Antes | Después | Motivo |
|---|---|---|---|
| `GA-REM-005` Mortalidad y balance de aves | `SPEC_READY` ⚠ `RC-02` | **`SPEC_READY`** | `RR-02` fija la semántica; `RR-07` desliga la captura del mapeo SAP |
| `GA-REM-006` Correcciones e integridad | `SPEC_DRAFT` ⚠ `RC-01` | **`SPEC_READY`** | `RR-01` fija el momento de aplicación y los estados corregibles |
| `GA-REM-007` Centralización de `BR-14` | `SPEC_READY` ⚠ `RC-03` | **`SPEC_READY`** | `RR-03` fija el mecanismo y el valor por defecto |
| `GA-REM-012` Cambio de contraseña | `SPEC_READY` ⚠ `RC-05` | **`SPEC_READY`** | `RR-05` fija la política única; `P0-13` fija el defecto a corregir |
| `GA-REM-018` Recuperación de trazabilidad | `SPEC_READY` ⚠ `RC-02` | **`SPEC_READY`** | `RR-02` |
| `GA-REM-017` Integración SAP real | `BLOCKED_EXTERNAL` | `BLOCKED_EXTERNAL` + `OD-02` | sin cambio; se añade la dependencia acotada de `RC-07` |

Ninguna spec pasa a implementación en esta Wave. `NO SPEC = NO DEVELOPMENT` se mantiene:
las specs quedan listas, el código no se toca.

---

## 5. Hallazgos nuevos

| ID | Hallazgo | Sev. | Destino |
|---|---|---|---|
| `P0-13` | El cambio de contraseña responde `200` y **no cambia la contraseña** | **P0** | `GA-REM-012` |
| `R-23` | `complete_review` aprueba sin validar `BR-14` con `approval_levels <= 1` | P1 | `GA-REM-007` |
| `R-25` | `PUT /users/{id}` no comprueba autorización más allá de estar autenticado | P1 | `GA-REM-002` |
| `R-24` | `bird_transfer` no valida población de origen ni capacidad de destino | P2 | `GA-REM-005` |

`P0-13` se descubrió persiguiendo `RC-05` y **se confirmó en ejecución** contra la base de
pruebas aislada, no por lectura de código: la API confirma el cambio, el *login* con la
contraseña original sigue funcionando. Ninguno se corrige aquí — el encargo prohíbe
corregir en esta Wave.

---

## 6. Trazabilidad de la evidencia

| RC | Nivel que decidió | Documento | Localización |
|---|---|---|---|
| `RC-01` | 2 · cliente | `Recomendación central.pdf` | §17, §18, §26 |
| `RC-02` | 5 · esquema de datos | `backend/app/operations/models.py` | `:80`, `:155-156` |
| `RC-03` | 3 · proceso operativo | `docs/02-functional-spec.md` · `docs/12-approval-workflow.md` | `:554` · `:139` |
| `RC-05` | 5 · implementación (niveles 2–4 en silencio) | `backend/app/auth/schemas.py` | `:39` |
| `RC-07` | 2 · cliente — **escala, no resuelve** | `Recomendación central.pdf` | §5 `:324-327`, §25 |

---

## 7. Estado de salida de Track A

**`COMPLETE`.** Los cinco RC del alcance tienen clasificación terminal con evidencia
completa. Cinco specs quedan desbloqueadas. Las tres decisiones que siguen abiertas están
formuladas de modo que el propietario pueda cerrarlas sin trabajo técnico previo, y
ninguna bloquea la Wave 2.
