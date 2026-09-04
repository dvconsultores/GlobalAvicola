# WAVE 1.5 — EXECUTION REPORT

**Global Avícola** · Resolución de conflictos de requerimiento · Infraestructura de pruebas ·
Certificación de la línea base del backend

**Fecha** 2026-09-03 · **Commit base** `bfccdfb` · **Estado** `COMPLETE`

---

# 1. Resumen

```
Track A · Requirement conflicts ......... COMPLETE
Track B · Base de datos de pruebas ...... COMPLETE  ->  GA-REM-014 CERTIFIED
Track C · Línea base del backend ........ COMPLETE  ->  GA-REM-015 CERTIFIED

RC resueltos por evidencia ..............  4  (RC-01, RC-02, RC-03, RC-05)
RC escalados al propietario .............  1  (RC-07, acotado)
Specs desbloqueadas .....................  5  (005, 006, 007, 012, 018)
Spec nueva creada .......................  1  (GA-REM-023)

Suite backend: primera ejecución de la historia del proyecto
  RUN 01 ....... 29 passed ·  6 failed · 66 errors
  RUN 05 ....... 74 passed · 26 failed ·  1 skipped   <- línea base
Fallos clasificados ..................... 26 / 26 · cero UNKNOWN

Hallazgos nuevos ........................  9  (2 P0, 4 P1, 3 P2)
Cambios en backend/app/** ............... 0
Cambios en alembic/versions/** .......... 0
Cambios en frontend/src/** .............. 0
git push / release / deploy / tag ....... 0
Accesos a producción .................... 0
```

Wave 1.5 no corrigió ningún defecto funcional. **Ese era el encargo.** Lo que hizo fue
convertir suposiciones en hechos: cinco conflictos que se creían decisiones de negocio, una
suite que nadie había ejecutado nunca, y dos P0 que ninguna lectura de código habría
encontrado.

---

# 2. Track A — Resolución de conflictos de requerimiento

## 2.1 Jerarquía aplicada

Decisión del propietario > requerimiento del cliente > documento de proceso operativo >
spec vigente > implementación > legado. **Regla de corte:** decide el nivel más alto que se
pronuncia; el silencio de un nivel hace descender la decisión, no la aprueba.

## 2.2 Resultado

| RC | Tema | Nivel que decidió | Clasificación |
|---|---|---|---|
| `RC-01` | flujo de corrección | 2 · cliente (§17, §18, §26) | `RESOLVED_BY_EVIDENCE` + `SPEC_DEFECT` |
| `RC-02` | semántica de `bird_transfer` | 5 · esquema de datos | `RESOLVED_BY_EVIDENCE` |
| `RC-03` | ¿`BR-14` absoluta o configurable? | 3 · proceso operativo | `RESOLVED_BY_EVIDENCE` |
| `RC-05` | política de contraseñas | 5 · implementación (2–4 en silencio) | `RESOLVED_BY_EVIDENCE` |
| `RC-07` | mortalidad frente a SAP | 2 · cliente — **escala, no resuelve** | `OWNER_DECISION_REQUIRED` |

## 2.3 Reglas vigentes fijadas

`RR-01` la corrección se aplica en el acto; el registro sigue requiriendo aprobación ·
`RR-02` `bird_transfer` es intra-lote y neutro en el balance ·
`RR-03` `BR-14` configurable por paso, `require_segregation` por defecto `True` ·
`RR-05` política única de longitud 8 ·
`RR-07` la captura de mortalidad no depende de `RC-07`.

## 2.4 Lo que reveló el ejercicio

**Cuatro de los cinco conflictos no necesitaban una decisión.** Necesitaban que alguien
leyera las fuentes en orden. Tres ni siquiera eran conflictos:

- `RC-01` era una **omisión de `spec.md §4.10`**. Cliente, `docs/12`, `spec.md` y el código
  dicen exactamente lo mismo. La disyuntiva «inmediata *o* con aprobación» mezclaba dos
  planos: el del dato (se escribe ya) y el del registro (sigue necesitando aprobación).
- `RC-02` era una **imposibilidad estructural**. `BirdMovement` declara galpón origen y
  destino; no existe ningún campo de lote destino en todo el esquema. La alternativa B no
  era una opción de negocio: era inexpresable.
- `RC-05` eran **números aplicados a operaciones distintas** que nunca compitieron. El `6`
  del login restringe un intento de autenticación; el `6` del perfil valida una operación
  que no funciona. La única política del sistema es `min_length=8`.

`RC-07` sí necesita al propietario, y por una razón limpia: **la fuente de nivel 2 se
pronuncia para decir que la decisión no está tomada.** El documento del cliente dedica una
sección —«25. Decisión crítica antes de avanzar»— a las cinco definiciones que la empresa
debe cerrar, y la cuarta es este conflicto. Lo que sí se hizo fue **acotar su radio**: por
`RR-07` deja de bloquear `GA-REM-005` y afecta solo al mapeo SAP dentro de `GA-REM-017`,
que ya estaba detenida por el contrato técnico.

---

# 3. Track B — Base de datos de pruebas aislada

## 3.1 El bloqueo y cómo se resolvió sin bypass

`sudo` exige contraseña en esta máquina. `apt install postgresql` no era posible, y el
encargo prohíbe expresamente intentar un bypass. Tampoco se recurrió a crear una base
dentro del servidor de producción, opción desaconsejada.

La solución fue lateral: **`pgserver`** de PyPI empaqueta binarios de **PostgreSQL 16.2** y
levanta un servidor en espacio de usuario, sobre socket Unix bajo `$HOME`, sin root y sin
tocar la configuración global. Es PostgreSQL real, misma versión mayor que producción.
Ejecutar la suite contra SQLite habría sido más fácil y habría invalidado el resultado.

| Elemento | Valor |
|---|---|
| Motor | PostgreSQL 16.2, espacio de usuario |
| `PGDATA` | `~/.local/share/global_avicola_test_pg` (59 MB) |
| Conexión | socket Unix — **no alcanzable por red** |
| Base · rol | `global_avicola_test` · `global_avicola_test_user` |

## 3.2 Certificación de `GA-REM-014`

| ID | Verificación | Resultado |
|---|---|---|
| `T-014-01` | DSN apuntando a `avicolav2` | **PASS** — abortado, sin conexión |
| `T-014-02` | `ENVIRONMENT=production` | **PASS** |
| `T-014-03` | Sin marcador `GA_TEST_ENV` | **PASS** |
| `T-014-04` | Nombre de base sin patrón de prueba | **PASS** |
| `T-014-05` | `--collect-only` exento | **PASS** — 101 tests recolectados sin conectar |
| `T-014-06` | Ciclo completo reproducible y determinista | **PASS** — dos ejecuciones idénticas |

**PASS 6 · FAIL 0 · BLOCKED 0.** Los 25 tests de la propia guarda pasan.
`AC03` y `AC05`, en `BLOCKED_EXTERNAL` desde Wave 1, quedan verificados.

**`GA-REM-014` → `CERTIFIED`.** Detalle en `TEST_DATABASE_SAFETY_REPORT.md`.

## 3.3 Un falso positivo que merece registrarse

La quinta señal de la guarda comparaba el DSN de pruebas con la **variable** `DATABASE_URL`
—que el propio flujo legítimo sobrescribe tras validar—. La guarda se veía a sí misma y
abortaba. Se corrigió leyendo el DSN del **fichero** `backend/.env`, con test de regresión.

El fallo fue de la guarda **cerrando de más, no de menos**. Una guarda fail-closed que se
equivoca, se equivoca hacia el lado seguro. Es la propiedad que se le pedía.

---

# 4. Track C — Línea base del backend

## 4.1 De RUN 01 a RUN 05

| Run | Cambio | Resultado |
|---|---|---|
| **01** | — | `29 passed · 6 failed · 66 errors` |
| 02 | *fixture* de `dispose()` entre tests | errores 66 → 23 |
| 03 | `admin_client` a `pytest_asyncio.fixture` | errores 23 → 0; 41 fallos nuevos |
| 04 | ámbitos explícitos de *event loop* | sin efecto |
| **05** | **`NullPool`** | `26 failed · 74 passed · 1 skipped` |

Los 66 errores de RUN 01 no eran funcionales: eran `InterfaceError` por reutilización de
conexiones `asyncpg` entre *event loops*. **RUN 01 no midió el backend; midió la
infraestructura de pruebas.** RUN 05 sí mide el producto, y por eso es la línea base.

Cada intervención tocó exclusivamente `backend/tests/**`, `backend/seeds/**`,
`backend/scripts/**` y `[tool.pytest.ini_options]`. Ninguna tocó `backend/app/**`.

## 4.2 Composición de los 26 fallos

```
TEST_DEFECT ................ 14   defectos de los propios tests
OBSOLETE_TEST ..............  4   contratos que cambiaron legítimamente
IMPLEMENTATION_BUG .........  4   defectos reales del producto
FIXTURE_DEFECT .............  2   siembra insuficiente
SPEC_MISMATCH ..............  1   sin árbitro documental
UNKNOWN ....................  0
```

**20 de 26 son problemas de los tests.** Consecuencia previsible de escribir 101 tests y no
ejecutar ninguno: codifican rutas equivocadas (`/operations` sin prefijo `/api/v1`),
*payloads* incompletos (sin `farm_id`, que el frontend sí envía) y credenciales ya
eliminadas. No probaban lo que decían probar.

**`GA-REM-015` → `CERTIFIED`.** Clasificación completa en `BACKEND_TEST_FAILURE_MATRIX.md`.

---

# 5. Hallazgos nuevos

| ID | Hallazgo | Sev. | Cómo se encontró | Destino |
|---|---|---|---|---|
| **`P0-13`** | El cambio de contraseña responde `200` y **no cambia la contraseña** | **P0** | persiguiendo `RC-05`; confirmado en runtime | `GA-REM-012` |
| **`P0-14`** | **14 columnas** de datos operativos descartadas en silencio, incluida `cause_id` (causa de mortalidad) | **P0** | tres tests en rojo que nadie había ejecutado | **`GA-REM-023`** |
| `R-23` | `complete_review` aprueba sin validar `BR-14` con `approval_levels <= 1` | P1 | resolviendo `RC-03` | `GA-REM-007` |
| `R-25` | `PUT /users/{id}` no comprueba autorización más allá de estar autenticado | P1 | resolviendo `RC-05` | `GA-REM-002` |
| `R-26` | **7 reglas de negocio devuelven 500 en lugar de 400** | P1 | 11 fallos de test que apuntaban al mismo sitio | **`GA-REM-023`** |
| `R-28` | **La suite caduca el 2026-09-21** por `BR-19` y fechas literales | P1 | sondeando `P0-1` con una fecha de junio | `GA-REM-015` |
| `R-24` | `bird_transfer` no valida población de origen ni capacidad de destino | P2 | resolviendo `RC-02` | `GA-REM-005` |
| `R-27` | `_get_role_by_name` responde 500 ante configuración ausente | P2 | fallo de `test_review.py` | `GA-REM-023` |
| `R-29` | `test_farm_inspection_without_house_id_still_accepted` contradice a `validators.py:365` sin árbitro | P2 | clasificando fallos | `GA-REM-018` |

## 5.1 `P0-14` — el hallazgo de mayor alcance

`create_event` construye el `OperationalEvent` asignando **11 campos**
(`backend/app/operations/service.py:69-81`). El esquema de entrada declara **14 campos
específicos de operación más** (`schemas.py:92-105`), las columnas existen
(`models.py:104-117`) y la respuesta los devuelve. Ninguno se persiste jamás.

```
supplier_id  cause_id  cull_cause_id  vaccine_id  vaccination_route
vaccine_lot_number  medication_id  dosage_per_bird  treatment_days
destination_farm_id  destination_plant_id  transport_id  sample_size  extra_data
```

La mortalidad **no puede registrar su causa** —exigida literalmente por el cliente («Mortalidad
— Cantidad, causa»)—; la vacunación no registra qué vacuna se aplicó; la salida de aves no
registra destino ni transporte. El frontend sí los envía.

## 5.2 `R-26` — siete reglas gritando 500

El `try/except BusinessRuleViolation → 400` de `_apply_business_rules` abarca solo
`service.py:336-364`. Los validadores de `BR-06`, `BR-07`, `BR-08`, `BR-10`, `BR-19`,
`BR-17`/G-R04 y G-R05 se invocan **antes** y su excepción sale sin manejar. No hay
manejador global: `main.py:54` solo registra `RateLimitExceeded`.

```
bird_reception sin farm_id      -> HTTP 500  Internal Server Error
mortality_recording sobre saldo -> HTTP 400  {"detail":"Mortalidad (999999) excede el saldo..."}
```

El operador que olvida la granja ve «Internal Server Error» en vez del motivo.

## 5.3 `P0-1` — confirmado en runtime

```
app/operations/service.py:244: in _check_and_create_alerts
    balance = await get_current_bird_balance(self.db, event.lot_id, self.company_id)
E   NameError: name 'get_current_bird_balance' is not defined
```

Estático desde la auditoría; ahora reproducido. La función existe en `validators.py:21` con
**dos** parámetros; la llamada pasa **tres** y no la importa.

**Ningún test de los 101 recorre esa ruta.** `test_f8c` pasa porque usa `quantity: 999999`,
que `validate_mortality` rechaza antes de que el generador de alertas se ejecute. Es un
recordatorio de que una suite en verde no es lo mismo que un sistema verificado.

---

# 6. La suite tiene fecha de caducidad — `R-28`

`validate_period_open` (`BR-19`) rechaza eventos de más de 90 días. Los tests fijan fechas
literales:

```
test_full_workflow_audit.py   "2026-06-29"  ->  caduca ~2026-09-27
test_operations.py            "2026-06-23"  ->  caduca ~2026-09-21
```

**A partir del 2026-09-21, decenas de tests hoy en verde fallarán solos** sin que nadie
cambie una línea. Se descubrió al sondear `P0-1` con fecha `2026-06-01`, ya fuera de plazo.

Es el primer trabajo de la Wave 2 porque es el único con fecha límite dura: sin él, la línea
base RUN 05 deja de ser reproducible y `GA-REM-016` heredaría el defecto.

---

# 7. Orden recalculado de la Wave 2

| # | Trabajo | Por qué aquí |
|---|---|---|
| 1 | **`R-28`** fechas relativas en los tests | expira el 2026-09-21; protege la línea base |
| 2 | **`GA-REM-023`** (`P0-14` + `R-26`) | mayor apalancamiento: convierte 11 fallos en aserciones con sentido y restituye `cause_id` |
| 3 | `GA-REM-005` mortalidad | `P0-1` confirmado; depende de `023` |
| 4 | `GA-REM-002` RBAC | absorbe `R-25`; habilita `007` y `012` |
| 5 | `GA-REM-003` contexto de autorización | habilita `012` |
| 6 | `GA-REM-012` contraseña | `P0-13` confirmado |
| 7 | `GA-REM-006` correcciones | `RC-01` resuelto |
| 8 | `GA-REM-007` `BR-14` | `RC-03` resuelto; incorpora `R-23` |
| 9 | `GA-REM-011` 8 contratos restantes | diferidos por alcance |
| 10 | `GA-REM-008` trazabilidad | espera `RC-04` |

Detalle y justificación en `REMEDIATION_BACKLOG.md`.

---

# 8. Cambios de estado

| Elemento | Antes | Después |
|---|---|---|
| `GA-REM-014` | `IMPLEMENTED` ⚠ | **`CERTIFIED`** |
| `GA-REM-015` | `SPEC_DRAFT` / `READY_TO_EXECUTE` | **`CERTIFIED`** |
| `GA-REM-005` | `SPEC_READY` ⚠ `RC-02` | `SPEC_READY` (+dependencia de `023`) |
| `GA-REM-006` | `SPEC_DRAFT` ⚠ `RC-01` | **`SPEC_READY`** |
| `GA-REM-007` | `SPEC_READY` ⚠ `RC-03` | `SPEC_READY` |
| `GA-REM-012` | `SPEC_READY` ⚠ `RC-05` | `SPEC_READY` |
| `GA-REM-018` | `SPEC_READY` ⚠ `RC-02` | `SPEC_READY` |
| `GA-REM-023` | — | **creada · `SPEC_READY`** |

---

# 9. Verificación de regresión

```
1/8  ruff ............................. ✓
2/8  cadena Alembic (1 head) .......... ✓
3/8  deriva ORM vs migraciones ........ ✓  0 deriva
4/8  guarda del entorno de pruebas .... ✓  25 tests
5/8  sin credenciales en seeds ........ ✓
6/8  frontend tsc ..................... ✓
7/8  frontend vitest .................. ✓  61/61
8/8  paridad i18n .................... ✓  ES=865 EN=865
```

**8/8 en verde.** Ninguna regresión introducida por la Wave 1.5.

---

# 10. Verificación de alcance — `EX-01`

| Elemento | Estado |
|---|---|
| `watchtower` en `docker-compose.yml` | **6 referencias, intactas** |
| `pull_policy: always` | **3 referencias, intactas** |
| Etiqueta `:latest` | **3 referencias, intactas** |
| Workflows de despliegue | **5, sin cambios** |
| `git push` / `release` / `deploy` / `tag` | **0** |

El despliegue automático sigue registrado como `KNOWN_ACCEPTED_RISK` y `OUT_OF_SCOPE`.
Ninguna acción de esta Wave lo modificó, ni directa ni indirectamente.

---

# 11. Seguridad de la ejecución

| Restricción del encargo | Cumplimiento |
|---|---|
| No tocar producción | **0 conexiones**; cada intento deliberado fue bloqueado por la guarda antes de conectar |
| No intentar bypass de privilegios | ninguno: `pgserver` en espacio de usuario, sin root |
| Credenciales locales, no reutilizadas, fuera de Git | generadas con `secrets.token_urlsafe(18)` por ejecución; ningún fichero versionado las contiene |
| No imprimir secretos | los informes muestran `<oculta>`; ninguno aparece aquí |
| No corregir los defectos revelados | **0 correcciones**: los 9 hallazgos quedan clasificados y trazados |
| No ejecutar E2E | **0 ejecuciones** |
| No implementar SAP real | `GA-REM-017` sigue `BLOCKED_EXTERNAL` |
| No adaptar código para complacer un test | **0 cambios en `backend/app/**`** |
| No adaptar tests para ocultar código incorrecto | ningún test modificado en sus aserciones de negocio; ningún `skip` ni `xfail` añadido |

Se detectó en la máquina una instancia ajena de PostgreSQL 18 de otro proyecto. **No se
tocó, no se conectó, no se detuvo.**

---

# 12. Ficheros

| Fichero | Acción |
|---|---|
| `audit/remediation/REQUIREMENT_CONFLICT_RESOLUTION.md` | **creado** |
| `audit/remediation/RC_RESOLUTION_REPORT.md` | **creado** |
| `audit/remediation/TEST_DATABASE_SAFETY_REPORT.md` | **creado** |
| `audit/remediation/BACKEND_TEST_BASELINE_RUN_01.md` | **creado y congelado** |
| `audit/remediation/BACKEND_TEST_FAILURE_MATRIX.md` | **creado** |
| `audit/remediation/GA-REM-015-CERTIFICATION-REPORT.md` | **creado** |
| `audit/remediation/GA-REM-014-CERTIFICATION-REPORT.md` | recertificado |
| `specs/remediation/GA-REM-023-…md` | **creada** |
| `specs/remediation/GA-REM-005/006/007/012/018` | estado y `RC` actualizados |
| `audit/remediation/MASTER_REMEDIATION_MATRIX.md` · `DEPENDENCY_MAP.md` · `REMEDIATION_BACKLOG.md` · `REMEDIATION_READINESS_REPORT.md` | actualizados |
| `backend/tests/environment_guard.py` · `conftest.py` · `test_environment_guard.py` | correcciones de infraestructura |
| `backend/seeds/test_seeds.py` · `backend/scripts/test_db.py` · `run_tests.sh` · `verify.sh` | correcciones de infraestructura |
| **`backend/app/**` · `alembic/versions/**` · `frontend/src/**`** | **sin cambios** |

---

# 13. Deuda que esta Wave deja abierta

| Deuda | Por qué se deja | Cuándo |
|---|---|---|
| 26 fallos de test sin corregir | el encargo prohíbe corregir en esta Wave | Wave 2, según el orden de §7 |
| 9 hallazgos nuevos sin corregir | ídem; todos con spec de destino | Wave 2 |
| `RC-04` | corrección de redacción de `spec.md §4.9` | antes de `GA-REM-008` |
| `OD-02` (`RC-07`) | decisión contable del propietario | antes de `GA-REM-017` |
| `OD-01`, `OD-03` | endurecimiento sin urgencia | cuando el propietario quiera |
| 0 procesos certificados E2E | el encargo prohíbe ejecutar E2E aquí | `GA-REM-016` |

---

# 14. Lo que esta Wave costó y lo que compró

**Costó:** ninguna corrección funcional. El recuento de P0 abiertos **subió** de 8 a 10 y el
de P1 de 13 a 16.

**Compró:** una base de datos de pruebas real y aislada que hace imposible tocar producción
por accidente; la primera línea base de la historia del proyecto, reproducible y congelada;
la eliminación de cuatro de los seis conflictos que bloqueaban cinco specs; y dos P0 que
llevaban meses en el producto sin que nadie los viera.

El aumento de defectos conocidos no es un retroceso. Es lo que ocurre cuando un programa
mejora su capacidad de detección. El indicador sano no es «P0 bajando», sino **P0 conocidos,
trazados y con spec de destino: 10 / 10**.

---

# 15. Verdicto funcional

El sistema **no está listo para operación productiva**. La mortalidad no puede registrar su
causa, el cambio de contraseña miente, y siete reglas de negocio se presentan al usuario
como errores del servidor. Ninguno de esos tres defectos era conocido hace 24 horas.

Lo que sí cambió: ahora son **medibles**. Existe una suite que corre, una línea base contra
la que comparar y una guarda que impide que verificar cueste datos reales.

---

# 16. Verdicto de Spec Development

`NO SPEC = NO DEVELOPMENT` se respetó sin excepción: **cero líneas de código de aplicación**
en toda la Wave. Los nueve hallazgos nuevos entraron por spec (`GA-REM-023`) o se anexaron a
una existente, nunca por parche.

`NO TEST = NO COMPLETE` pasa de consigna a hecho comprobable: por primera vez existe una
ejecución real contra la que medir «completo».

La deuda metodológica baja de 14 a 13. Sigue siendo alta. `GA-REM-018` continúa pendiente.

**Nivel de madurez: 3** — sin cambio. Subir a 4 exige procesos certificados E2E, y eso es
`GA-REM-016`.

---

# 17. Estado de salida

```
Track A ......... COMPLETE   4 RC resueltos por evidencia · 1 escalado con alcance acotado
Track B ......... COMPLETE   GA-REM-014 CERTIFIED · 6/6 verificaciones
Track C ......... COMPLETE   GA-REM-015 CERTIFIED · 26/26 clasificados · 0 UNKNOWN

Criterio de salida: "Todos los RC tienen RESOLVED_BY_EVIDENCE u
OWNER_DECISION_REQUIRED con evidencia completa."          ->  CUMPLIDO

Producción intacta ....................... sí
Alcance EX-01 respetado .................. sí
Regresión ................................ ninguna · 8/8 en verde
```

**`WAVE 1.5 · COMPLETE`.** La Wave 2 puede arrancar con el orden de §7.
