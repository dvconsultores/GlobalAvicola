# GA-FE-04 · SPEC — CIERRE `R-98`/`P-13`: AUTORIDAD INTRA-PANTALLA

**Tranche**: GA-FE-04 · **Baseline**: `73352d4` · **Runtime**: `index-CElqNz3R.js` (ETag
`6aa37597-13bd2e`) · **Metodología**: Spec Development · **Autorización del propietario**:
GA-FE-04 autorizada (modo autónomo end-to-end).

## 1 · Contexto

`GA-FE-02/03` están `OWNER_ACCEPTED`. `R-119` = CLOSED. `R-98` = PARTIAL con un único residuo
declarado: el **modelo general de permisos del frontend aplicado a acciones dentro de las
pantallas** (P-13). El contrato de sesión (`/me`, `AC-H11…H14`) ya entrega `permissions`,
empresa efectiva y las tres listas de unidades; el evaluador `auth/navigation.ts` (GA-FE-03) ya
existe; el helper de permiso es espejo de `tiene_permiso`. Nada de esto había sido aplicado a
las acciones de pantalla fuera de la frontera GA-FE-02.

## 2 · Historia de `R-98`

Ver `GA_FE_04_R98_CANONICAL_RECONCILIATION.md`: redacción original, `AC-FE16` («quien solo lee
no ve acciones de escritura; el backend sigue siendo la autoridad»), precisión
`R-96-WEIGHT-CURVE-CAPABILITY-CERTIFICATION §5`, verificación ejecutable en
`e2e/proceso-p03-curvas-ui.spec.ts`.

## 3 · Definición canónica de `P-13` (residual)

`P-13` = proceso «Gestión de usuarios, roles y permisos». Su residual en R-98 = **la autoridad
RBAC representada en los controles de escritura de cada pantalla** — no navegación (cerrada en
GA-FE-03), no funcionalidad nueva. **Página ≠ acción**: `users:read` permite ver el listado sin
permitir crear/editar/desactivar.

## 4 · Problema

Las acciones de escritura intra-pantalla se muestran sin comprobar el permiso (§ inventario):
altas/ediciones/borrados de usuarios, roles, maestros, curvas, lotes, operaciones, revisiones,
aprobaciones y mutaciones SAP. Un actor de solo lectura ve «puertas accionables» que el backend
cerrará con 403. No es un agujero de seguridad — es el defecto de producto `R-98`.

## 5 · Alcance

1. Modelo de **autoridad de acción** compartido (reutiliza el vocabulario y evaluador GA-FE-03;
   sin segundo sistema).
2. Aplicación a las **31 acciones de escritura** del inventario + **3 guardas de ruta** de paridad
   (`/lots/new`, `/operations/new`, `/review/:id/correct`).
3. CTAs de estado vacío y botones de alta incluidos.
4. Propagación por contexto (switch, BU, grants, RBAC) y fail-closed de carga.
5. i18n ES/EN de cualquier texto nuevo; paridad desktop/móvil; evidencia runtime autenticada.

## 6 · Fuera de alcance

`R-181` (submit/reenvío — sin UI) · `R-182` (LotForm) · BU-D10 · Wave B/C · SAP-integration ·
nuevos permisos/roles de negocio · nuevos flujos · reverso · notificaciones · refactor amplio.
Acciones masivas de SAP/otros sin UI: N/A documentadas.

## 7 · Modelo de seguridad (intacto)

Tenant → Company BU ON → User BU/global → RBAC → recurso. BU OFF absoluto (global incluido).
`R-163` escritura · `D-1` lectura · `OD-15` self-grant. **Ocultar no autoriza**: la guarda de
ruta y el backend son independientes de la visibilidad del botón (§15/§113).

## 8 · Modelo de actor

`E A B C D Z P R` — ver `GA_FE_04_ACTOR_MATRIX.md`. `R` (solo lectura administrativa) es
**obligatorio** (§72): el modelo canónico lo soporta (`users:read`, `masters:read`).

## 9 · Taxonomía de acciones

§14 del encargo — ver inventario. Clasificación por comportamiento del recurso, no por texto.

## 10 · Distinción página vs acción

Página con permiso `X:read`; acción con el permiso exacto que el router exige. Tabla completa en
`GA_FE_04_ACTION_API_CONTRACT.md`. Casos canónicos señalados: aprobar≠rechazar; batch revisión =
`review:review`; cerrar/añadir fase = `lots:create`.

## 11 · Acciones de plano de control

No exigen BU de usuario. Access Admin (35) conserva su superficie; CBU Admin (36) la suya; cada
una **sin** ganar la otra ni lo productivo (P13-AC15…18).

## 12 · Acciones productivas

Dimensiones completas (permiso ∧ BU efectiva/habilitada ∧ concesión/global ∧ recurso). 3D
obligatoria (§68). BU OFF ⇒ no accionable incluido el global.

## 13 · Reglas BU / tenant / recurso

Igual que navegación (GA-FE-03) para lo productivo; las acciones de control usan solo permiso +
contexto. `resource-state` se conserva tal cual (no se simplifica; P13-AC22/§22).

## 14 · Self / cross-company

Self-grant: se **verifica** la protección existente (UI + 403 + sin persistencia + sin
auditoría de éxito). Cross-company: candidatos no exponen foráneos (ya certificado); el gate no
introduce reglas nuevas.

## 15 · Carga / error

Sin flash: el layout espera a `/me`. Fetches de autoridad fallidos → sin controles optimistas
(el estado de sesión queda con permisos vacíos ⇒ gates cierran). Sin convertir errores de
aplicación en denegaciones permanentes sin UX (se conserva el patrón existente de la página).

## 16 · Desktop / móvil

Misma semántica (única fuente de gates). Sin menús de desborde con mutaciones en 390×844.

## 17 · i18n

`actions.readOnlyViewer` (ES/EN) para el aviso donde una página productiva queda sin acciones;
`common.noPermission` (ya existe) para paridad de rutas. Sin claves crudas.

## 18 · Arquitectura elegida (mínima y coherente)

```
auth/actionAuthority.ts
  canPerformAction(spec, session)      // alias documentado de canAccessCapability (acción)
  useCan(): (spec) => boolean          // hook sobre el user de la sesión
  <ActionGate spec={...}>…</ActionGate>// render condicional declarativo
```
Reutiliza `CapabilitySpec` y `canAccessCapability` de `auth/navigation.ts` (§24/§25 — sin
segundo sistema). Las páginas consumen `useCan()`. Sin refactor amplio.

## 19 · Criterios de aceptación

**Estructura**: `P13-AC01` alcance exacto documentado (reconciliación + inventario) ·
`P13-AC02` inventario por pantalla (§13) · `P13-AC03` acción→contrato backend (matriz) ·
`P13-AC04` 0 gating por nombre de rol · `P13-AC05` 0 gating por username · `P13-AC06` vocabulario
único · `P13-AC07` UI no sustituye backend · `P13-AC08` API directa no autorizada sigue denegada.

**Productivas**: `P13-AC09` BU OFF ⇒ sin acción ni operación · `P13-AC10` ON sin concesión ⇒ sin
acción · `P13-AC11` ON+concesión sin RBAC ⇒ sin acción · `P13-AC12` ON+concesión+RBAC ⇒ acción
(sujeta a recurso) · `P13-AC13` global respeta BU OFF · `P13-AC14` zero-BU sin mutaciones.

**Plano de control**: `P13-AC15` Access Admin solo sus acciones · `P13-AC16` sin productivo ·
`P13-AC17` CBU Admin sus acciones · `P13-AC18` sin User-BU/productivo ajenos · `P13-AC19`
no autorizado sin acciones privilegiadas · `P13-AC20` self-grant imposible · `P13-AC21`
cross-company no disponible/denegado.

**UX/estado**: `P13-AC22` sin flash de acción privilegiada · `P13-AC23` fetch fallido ⇒ fail
closed · `P13-AC24` switch de empresa recalcula · `P13-AC25` CBU ON/OFF recalcula · `P13-AC26`
grant/revoke recalcula según propagación canónica · `P13-AC27` RBAC recalcula tras propagación ·
`P13-AC28` paridad desktop/móvil · `P13-AC29` sin rutas duplicadas con autoridad inconsistente ·
`P13-AC30` CTA de vacío respeta autoridad de alta.

**Calidad**: `P13-AC31/32` ES/EN completos · `P13-AC33` sin claves crudas · `P13-AC34` sin
fatales de consola · `P13-AC35` sin bucles · `P13-AC36` sin falso-éxito · `P13-AC37` regresión
GA-FE-02 · `P13-AC38` regresión GA-FE-03 · `P13-AC39` R-119 sigue CLOSED · `P13-AC40`
R-181/R-182 unchanged.

## 20 · Pruebas

RED automatizado (contra comportamiento actual) + RED runtime mínimo + GREEN dirigido +
gates completos + certificación runtime autenticada (matriz por actor + 3D + deep API
negativas). Sin aserciones vacuas; los casos deben alcanzar la página/actor/acción previstos.

## 21 · Certificación runtime

Actores E/A/B/C/D/Z/P/R por mecanismos oficiales; matriz de acciones por pantalla; 3D 4/4;
self/cross; propagación; móvil 390×844; ES/EN; red/persistencia/auditoría; consola.

## 22 · Regresión

GA-FE-02/03 completas (suite 241+ y spots runtime). La aceptación del propietario se preserva.

## 23 · Despliegue

Pipeline normal (push → Actions → Watchtower). Sin cambios de política. Congelar generación
final para la certificación.

## 24 · Evidencia

`audit/ga-fe-04/`: reconciliación canónica, inventario, contrato, matrices, RED, runtime, red,
capturas, ledger, reconciliación de cierre R-98 por AC, certificación, UAT. Addendum al Master
Frontend Audit (sin reescribir historia).

## 25 · Criterio de cierre de `R-98`

Las 5 condiciones del §6 de la reconciliación + **todas** las P13-AC en verde con evidencia:
solo entonces `R-98 = CLOSED`. `R-181/R-182` fuera, sin contradicción (no son AC de R-98).
