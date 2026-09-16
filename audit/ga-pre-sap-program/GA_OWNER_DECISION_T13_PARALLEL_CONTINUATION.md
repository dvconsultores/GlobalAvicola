# GA · OWNER DECISION — **`T13_PARALLEL_CONTINUATION` (continuar T13 sin administrador del host)**

| Campo | Valor |
|---|---|
| **ID** | Owner Decision — T13 · Continuación en paralelo |
| **Fecha de decisión** | **2026-09-16** (canal chat; texto íntegro en el Anexo) |
| **Autoridad** | Propietario de Global Avícola |
| **Estado** | **RESUELTA — POLÍTICA VIGENTE** |

## 1 · Campos registrados

```
T13_PARALLEL_CONTINUATION   = AUTHORIZED
HOST_ADMIN_AVAILABILITY     = UNAVAILABLE_TEMPORARILY
HOST_GATES                  = BLOCKED_EXTERNAL_TEMPORARY

G-02 = BLOCKED_EXTERNAL
G-03 = FAIL_OBSERVED / HOST_FIX_PENDING
G-04 = BLOCKED_EXTERNAL
G-05 = BLOCKED_EXTERNAL

HOST_DEPLOYMENT_EVIDENCE    = INCOMPLETE
DEPLOYMENT_GATE             = PENDING

HOST_GATES_PENDING          = TRUE
U1                          = READY_FOR_OWNER (con limitación)
U1_SECURITY_RATE_LIMIT      = PENDING_HOST_G03
U2                          = READY_FOR_OWNER (completa)
```

**No** se interpreta como PASS de ningún gate de host; **no** se cambian esos
estados hasta existir evidencia real del host.

## 2 · Alcance autorizado en paralelo

Owner UAT U1 · Owner UAT U2 · preparación U3–U8 (tras resultados U1/U2) ·
reconciliación documental · inventario E2E · revisión de P0/P1/P2 · matriz de
procesos · documentación de certificación · todo trabajo técnico que no requiera
host.

**No** se cierra T13; **no** se emite `PRE_SAP_GO` todavía.

## 3 · U1 — autorizada con limitación explícita

- U1 puede ejecutarse **ahora** contra el build certificado desplegado (login,
  logout, back-navigation, relogin, aislamiento entre empresas, usuarios, roles,
  sesión).
- **El control anti-brute-force/rate-limit queda separado**:
  `U1_SECURITY_RATE_LIMIT = PENDING_HOST_G03`. Si la corrección del host es solo
  de configuración (`FEATURE_RATE_LIMIT_ENABLED=false/ausente → true`) y no hay
  cambio de producto, **no** se repite todo U1; se revalida únicamente el subcaso
  de autenticación/rate-limit cuando corresponda.

## 4 · U2 — autorizada completamente

- U2 no depende del rate-limit ni de G-02/G-04/G-05. Ficha vigente:
  P-01 Progenitoras · OD-25 · R-153/R-189, con **C1/C2/C3** y verificación de:
  lote sin aves · mortalidad pre-recepción rechazada · recepción 40♂+60♀ ·
  población final 100 · «Nuevo lote» sigue disponible.

## 5 · UAT humano

El agente **no** puede declarar `U1 = PASS`, `U2 = PASS` ni `OWNER_ACCEPTED`:
presenta las fichas y espera la declaración del propietario (fecha + canal +
texto exacto + evidencia primaria).

## 6 · Si U1/U2 pasan

Con U1 y U2 en PASS (o PASS WITH OBSERVATIONS no bloqueantes): registrar
evidencia primaria → **preparar U3–U8 automáticamente** → continuar Owner UAT,
sin micro-confirmaciones. Mantener `HOST_GATES_PENDING = TRUE`.

## 7 · U3–U8

Se preparan y pueden ejecutarse en paralelo siempre que el caso no dependa
directamente de G-02/G-03/G-04/G-05 ni requiera acceso al host y el runtime
desplegado contenga la funcionalidad certificada. Los UAT que dependan de un gate
de host se marcan `UAT_<ID> = BLOCKED_BY_HOST_GATE` (sin bloquear el resto).

## 8 · G-03 (hallazgo conocido, causa sin confirmar)

`G-03 = FAIL_OBSERVED` (12×401, sin 429). Causa **probable** documentada
(`FEATURE_RATE_LIMIT_ENABLED` ausente/false en runtime) — **no** se declara causa
confirmada hasta inspección real del host. Cuando el administrador esté
disponible: `printenv` → compose/`.env` → activar `true` → recrear solo backend →
retest (esperado `401×5 → 429`); si sigue fallando con `true` efectivo ⇒ hallazgo
técnico gobernado.

## 9 · G-02 / G-04 / G-05

Permanecen `BLOCKED_EXTERNAL_TEMPORARY`. No se inventa evidencia; no se sustituye
host real por rehearsal local; no se marca PASS por código o documentación.

## 10 · Cierre

Aunque U1–U8 terminen en PASS, **T13 no cierra** mientras exista algún gate host
`!= PASS` o `HOST_DEPLOYMENT_EVIDENCE != COMPLETE`. `T13_FINAL_CERTIFICATION` y
`PRE_SAP_GO` deben esperar.

## 11 · Registro

- `GA_T13_RECON_STATUS.md` §5 (estado) · `GA_PRE_SAP_PROGRAM_STATUS.md` (fila T13).
- `GA_AUTONOMOUS_EXECUTION_LEDGER.md` AE-66.
- Fichas U1/U2 liberadas (`GA_T13_UAT_FICHAS_U1_U2.md`, banner actualizado).

---

## Anexo · Texto íntegro de la decisión del propietario (2026-09-16, canal chat)

```text
GLOBAL AVÍCOLA — T13
OWNER DECISION — CONTINUAR EN PARALELO SIN ADMINISTRADOR DEL HOST

============================================================
0. DECISIÓN EXPLÍCITA DEL OWNER
============================================================

El administrador del host no está disponible actualmente.

Como Owner autorizo continuar T13 en paralelo con todo lo que NO dependa del
acceso al host.

Registrar:

T13_PARALLEL_CONTINUATION = AUTHORIZED

HOST_ADMIN_AVAILABILITY = UNAVAILABLE_TEMPORARILY

HOST_GATES =
BLOCKED_EXTERNAL_TEMPORARY

NO interpretar esta decisión como PASS de ningún gate de host.

============================================================
1. ESTADO QUE SE CONSERVA
============================================================

Mantener:

G-02 = BLOCKED_EXTERNAL
G-03 = FAIL_OBSERVED / HOST_FIX_PENDING
G-04 = BLOCKED_EXTERNAL
G-05 = BLOCKED_EXTERNAL

HOST_DEPLOYMENT_EVIDENCE = INCOMPLETE

DEPLOYMENT_GATE = PENDING

No cambiar estos estados hasta existir evidencia real del host.

============================================================
2. NO BLOQUEAR TODO T13
============================================================

Autorizar continuar en paralelo con:

- Owner UAT U1;
- Owner UAT U2;
- preparación U3–U8;
- reconciliación documental;
- inventario E2E;
- revisión de P0/P1/P2;
- matriz de procesos;
- documentación de certificación;
- todo trabajo técnico que no requiera host.

NO cerrar T13 todavía.

NO emitir PRE_SAP_GO todavía.

============================================================
3. U1 — AUTORIZADO CON LIMITACIÓN EXPLÍCITA
============================================================

U1 puede ejecutarse ahora contra el build certificado ya desplegado.

U1 valida:

- login funcional;
- logout;
- back-navigation después de logout;
- relogin;
- aislamiento entre empresas;
- usuarios;
- roles;
- sesión.

IMPORTANTE:

U1 NO certificará todavía el control anti-brute-force/rate-limit.

Ese punto queda separado como:

U1_SECURITY_RATE_LIMIT =
PENDING_HOST_G03

Cuando G-03 sea corregido en el host, únicamente se revalidará el subcaso
afectado de autenticación/rate-limit si corresponde.

No obligar a repetir todo U1 si el cambio del host es exclusivamente:

FEATURE_RATE_LIMIT_ENABLED=false/ausente
→ true

y no existe cambio de producto.

============================================================
4. U2 — AUTORIZADO COMPLETAMENTE
============================================================

U2 puede ejecutarse ahora.

U2 no depende del rate-limit ni de G-02/G-04/G-05.

Mantener la ficha actual:

P-01 Progenitoras
OD-25
R-153/R-189

El Owner debe validar personalmente:

C1
guardar importación sin lote + nota visible

C2
antes de aprobar:
“Se creará al aprobar”
+ no existe lote

C3
aprobación crea lote
+ #N
+ enlace navegable

Además:

- lote creado sin aves;
- mortalidad antes de recepción rechazada;
- recepción 40♂ + 60♀;
- población final = 100;
- “Nuevo lote” sigue disponible.

============================================================
5. OWNER UAT SIGUE SIENDO HUMANO
============================================================

DeepSeek NO puede marcar:

U1 = PASS
U2 = PASS
OWNER_ACCEPTED

por su cuenta.

Debe presentar las fichas al Owner y esperar su declaración.

============================================================
6. SI U1/U2 PASAN
============================================================

Si:

U1 = PASS
o PASS WITH OBSERVATIONS no bloqueantes

y

U2 = PASS
o PASS WITH OBSERVATIONS no bloqueantes

entonces:

registrar evidencia primaria
→ preparar U3–U8 automáticamente
→ continuar Owner UAT
→ no pedir micro-confirmaciones adicionales.

Mantener siempre:

HOST_GATES_PENDING = TRUE

hasta que el administrador esté disponible.

============================================================
7. U3–U8
============================================================

Preparar U3–U8 y permitir al Owner ejecutarlos en paralelo siempre que:

- el caso no dependa directamente de G-02/G-03/G-04/G-05;
- no requiera acceso al host;
- el runtime desplegado ya contenga la funcionalidad certificada.

Si algún UAT depende directamente de un gate host pendiente:

marcar:

UAT_<ID> = BLOCKED_BY_HOST_GATE

y continuar con los demás.

No bloquear innecesariamente todo el paquete.

============================================================
8. G-03
============================================================

Mantener como hallazgo conocido:

G-03 = FAIL_OBSERVED

12×401
sin 429.

Causa probable documentada:

FEATURE_RATE_LIMIT_ENABLED ausente/false en runtime.

NO declarar causa confirmada hasta inspección real del host.

Cuando el administrador esté disponible:

printenv
→ compose/.env
→ activar true
→ recrear solo backend
→ retest
→ esperado 401×5 → 429.

Si sigue fallando con true efectivo:

abrir hallazgo técnico gobernado.

============================================================
9. G-02 / G-04 / G-05
============================================================

Permanecen:

BLOCKED_EXTERNAL_TEMPORARY

No inventar evidencia.

No sustituir host real por rehearsal local.

No marcar PASS por código o documentación.

============================================================
10. PRE-SAP FINAL
============================================================

Aunque U1–U8 terminen en PASS:

T13 NO puede cerrar mientras exista:

G-02 != PASS
o
G-03 != PASS
o
G-04 != PASS
o
G-05 != PASS
o
HOST_DEPLOYMENT_EVIDENCE != COMPLETE

Por tanto:

OWNER_UAT puede avanzar.

T13_FINAL_CERTIFICATION debe esperar.

PRE_SAP_GO debe esperar.

============================================================
11. QUÉ HACER AHORA
============================================================

Ejecutar inmediatamente:

1. Formalizar esta Owner Decision.
2. Quitar U1/U2 del HOLD general.
3. Mantener únicamente:
   U1_SECURITY_RATE_LIMIT = PENDING_HOST_G03.
4. Presentar al Owner las fichas U1 y U2 listas para ejecución.
5. No presentar nuevamente decisiones de deployment.
6. Esperar resultados humanos U1/U2.
7. Si pasan:
   preparar automáticamente U3–U8.
8. Continuar todo T13 que no dependa del host.

============================================================
12. GIT
============================================================

Documentación/evidencia:

stage explícito.

NO:

git add .
git add -A
force push
reset
history rewrite

Commit
→ push origin/main
→ REMOTE_SHA_MATCH = PASS.

No tocar backend/frontend para esta decisión.

============================================================
13. PRÓXIMO MENSAJE AL OWNER
============================================================

Después de formalizar esta decisión:

presentar únicamente:

OWNER UAT — U1
OWNER UAT — U2

con pasos simples para ejecución humana.

No volver a detenerse por el administrador ausente.

El siguiente stop será:

- resultado humano U1/U2;
- un nuevo OWNER_GATE_REAL;
- o un UAT específicamente bloqueado por un gate de host.

EJECUTA AHORA.
```
