# `P-09` · COBERTURA DE ACCIONES DE AUDITORÍA

Fase de análisis · 2026-09-06 · sin desarrollo

---

## 1. Una corrección de partida sobre `AC13`

El encargo trata `AC13` como si definiera qué debe auditarse. **No es eso.** `AC13` es la
enmienda F de `GA-REM-016`, escrita ayer, y dice:

> Toda prueba invocada como evidencia de un `AC` demuestra que **puede fallar**.

Es la puerta de validez de la evidencia, no un catálogo de auditoría. Se aplicará —a las
pruebas de este tramo— pero no responde «qué debe auditarse».

Quien lo responde es `docs/02 §3.11` y `spec.md §4.11`.

## 2. Qué exige la norma

**`docs/02 §3.11.1`** — prioridad **Crítica**:

> **Cada acción en el sistema** genera un registro de auditoría inmutable.
> Datos: usuario · acción (creó, editó, corrigió, revisó, aprobó, rechazó, envió a SAP) ·
> fecha y hora · **módulo**, lote, granja, galpón · tipo de operación · estado anterior →
> nuevo · valor anterior → nuevo · motivo · observaciones · documento SAP · IP o dispositivo.

**`spec.md §4.11`** — «Registro inmutable de cada acción».

El alcance normativo es **toda acción del sistema**; el paréntesis enumera los *valores* del
campo «acción», no un límite de alcance. Que `Módulo` sea un dato registrado y que el enum
`AuditModule` declare **once** módulos confirma la intención.

## 3. Lo medido, no lo supuesto

El encargo daba «6 de 21 emitidas». **La medición actual dice 12.** Solo hay dos escritores
—`audit/listeners.py` y `audit/helpers.py`— y se enumeraron los valores de cada uno; las
restantes nueve **no aparecen fuera de la definición del enum**, comprobado una por una.

| `AuditAction` | Declarada | Productor | Emitida | Módulo | ¿Exigida por `§3.11`? | Hueco |
|---|:--:|---|:--:|---|:--:|---|
| `CREATED` | sí | listener + helper | **sí** | operations | sí — «creó» | — |
| `UPDATED` | sí | listener + helper | **sí** | operations | sí — «editó» | — |
| `CORRECTED` | sí | listener + helper | **sí** | corrections | sí — «corrigió» | — |
| `REVIEW_STARTED` | sí | helper | **sí** | review | sí — «revisó» | — |
| `RETURNED` | sí | helper | **sí** | review | sí — «revisó» | — |
| `APPROVED` | sí | listener + helper | **sí** | approvals | sí — «aprobó» | — |
| `REJECTED` | sí | listener + helper | **sí** | approvals | sí — «rechazó» | — |
| `CONSOLIDATED` | sí | helper | **sí** | sap | sí | — |
| `SENT_TO_SAP` | sí | helper | **sí** | sap | sí — «envió a SAP» | — |
| `SAP_CONFIRMED` | sí | helper | **sí** | sap | sí | — |
| `SAP_ERROR` | sí | helper | **sí** | sap | sí | — |
| `CANCELLED` | sí | helper | **sí** | operations | sí | — |
| `REVIEW_COMPLETED` | sí | **ninguno** | **no** | review | sí — «revisó» | **emisión ausente** |
| `LOGIN` | sí | **ninguno** | **no** | auth | sí — es una acción del sistema | **emisión ausente** |
| `LOGOUT` | sí | **ninguno** | **no** | auth | sí | **emisión ausente** |
| `LOGIN_FAILED` | sí | **ninguno** | **no** | auth | sí — y con valor de seguridad | **emisión ausente** |
| `PERMISSION_CHANGE` | sí | **ninguno** | **no** | users | sí | **emisión ausente** |
| `CONFIG_CHANGE` | sí | **ninguno** | **no** | config | sí | **emisión ausente** |
| `IMPORT` | sí | **ninguno** | **no** | sap | sí | **emisión ausente** |
| `EXPORT` | sí | **ninguno** | **no** | reports | sí | **emisión ausente** |
| `DELETED` | sí | **ninguno** | **no** | masters · lots | sí | **emisión ausente** |

```
Declaradas 21 · emitidas 12 · nunca escritas 9
```

## 4. El alcance real, por modelo vigilado

Los listeners observan **tres** tipos: `OperationalEvent`, `CorrectionLog`, `ApprovalAction`.

| Módulo declarado | ¿Produce registros? |
|---|:--:|
| `operations` · `corrections` · `approvals` · `review` · `sap` | **sí** |
| `auth` · `masters` · `lots` · `users` · `config` · `reports` | **no** |

Seis de los once módulos declarados **no producen ni un solo registro**. Crear una granja,
editar un lote, cambiar los permisos de un rol o exportar un informe no deja rastro.

Frente a «cada acción en el sistema», eso es el hueco.

## 5. Qué es obligatorio para certificar `P-09`

No se toman las 21 por estética (§47 del encargo). Se toma lo que la norma exige y el audit
del proyecto ya había enumerado como cadena del proceso (`audit/06 §P-09`):

| # | Exigencia | Estado |
|:--:|---|---|
| 1 | registro automático de creación de evento | **cubierto** |
| 2 | transiciones de estado | **cubierto** |
| 3 | correcciones | **cubierto** |
| 4 | acciones de aprobación | **cubierto** |
| 5 | **login / logout / login fallido** | **ausente** |
| 6 | **cambios de maestros y lotes** | **ausente** |
| 7 | **cambios de permisos** | **ausente** |
| 8 | **importación / exportación** | **ausente** |
| 9 | inmutabilidad | **cubierto** — no hay `UPDATE` ni `DELETE` sobre `audit_logs` |
| 10 | visor y línea de tiempo con filtros | **parcial** — ver `P09_AUDIT_QUERY_CONTRACT_MATRIX.md` |

```
Acciones obligatorias por P-09 ......... 20 de 21
No exigida ............................. 1  (CONFIG_CHANGE, ver abajo)
Emitidas correctamente ................. 12
Emisiones obligatorias ausentes ........  8
```

**`CONFIG_CHANGE` queda fuera**: no existe hoy módulo de configuración que pueda cambiarse
—`AuditModule.CONFIG` está declarado sin superficie asociada—, así que auditarlo sería
auditar algo que no ocurre. Se documenta, no se implementa. Si algún día hay configuración,
vuelve a la lista.

`REVIEW_COMPLETED` sí es obligatoria: `complete_review` existe y es un paso de `P-07`.

## 6. Hallazgo

```
R-81 · P1 · seis de los once módulos declarados no producen ningún registro de auditoría.
            Ocho acciones obligatorias por `docs/02 §3.11.1` nunca se escriben, entre ellas
            el inicio de sesión fallido y el cambio de permisos, que son precisamente las
            que un auditor busca primero.
```

**Severidad P1 y no P2**: es un hueco de rendición de cuentas, no de comodidad. Un cambio de
permisos sin rastro deja sin respuesta la pregunta «quién concedió esto y cuándo».


---

# ESTADO FINAL · tras `GA-REM-032` (2026-09-06)

```
Obligatorias 19 · IMPLEMENTADAS 19 · PROBADAS 19 · CERTIFICADAS 19
Fuera de alcance 2 · sin superficie que auditar
```

| Acción | Antes | Ahora | Cómo |
|---|:--:|:--:|---|
| `LOGIN` `LOGIN_FAILED` | no | **sí** | `AuthService.login` |
| `CREATED` `UPDATED` `DELETED` en `masters` | no | **sí** | `MasterService._auditar` |
| `CREATED` en `lots` | no | **sí** | `LotService.create_lot` — no pasa por `MasterService` |
| `PERMISSION_CHANGE` | no | **sí** | `AuthService.create_role` · `update_role` |
| `IMPORT` `EXPORT` | no | **sí** | `SapService` |
| `REVIEW_COMPLETED` | no | **sí** | `ReviewService.complete_review` |
| las 12 anteriores | sí | sí | sin cambios |

## Las dos exclusiones, justificadas

| Acción | Por qué no |
|---|---|
| `CONFIG_CHANGE` | `AuditModule.CONFIG` está declarado sin ninguna superficie de configuración detrás |
| `LOGOUT` | no existe endpoint de cierre de sesión: el cliente descarta el token |

Auditar algo que no ocurre no es cobertura. Ambas vuelven a la lista el día que exista la
superficie correspondiente.

## Limitación registrada

`R-83` — `AuditLog.company_id` no es nulable, así que una acción no atribuible a ninguna
empresa no puede auditarse. Detalle en `PROCESS-09-CERTIFICATION.md §8`.
