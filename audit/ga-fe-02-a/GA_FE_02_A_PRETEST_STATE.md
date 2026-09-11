# GA-FE-02-A · PRETEST STATE (§20)

**Resultado**: snapshot funcional **NO capturado** — la ejecución entró en `MODE_C ·
BLOCKED_AUTH` antes de poder autenticarse (§29/§79 del encargo). No se inventó ningún dato.

## Lo que SÍ quedó registrado (estado del sistema, no del producto)

```
FECHA/HORA          2026-09-10T23:52:28Z – 23:53:23Z
REPO                main · HEAD d120fdd == remoto · worktree limpio
RUNTIME             200 OK · assets/index-C_aR7TJ6.js · sha256 35ea38e2… · LM 23:39:07 GMT
                    ETag "6aa33f9b-322" — generación GA-FE-02 (verificada byte a byte)
GATES               tsc 0 · npm run build exit 0 · Vitest 198/198
SESIÓN              navegador compartido en /login (NO autenticada) — sin cookies de sesión
CREDENCIALES        0 suministradas por mecanismo autorizado (verificación acotada)
MFA / EMAIL CONF    no aplican (no existen en el producto)
```

## Lo que NO se pudo capturar (y por qué)

```
Company de prueba (ID/nombre) .............. requiere sesión
Estado de Company BU (4 unidades) .......... requiere sesión
Usuarios de prueba y sus concesiones ....... requiere sesión
Concesiones efectivas ...................... requiere sesión
Roles/permisos observados .................. requiere sesión
Empresa seleccionada / sesión .............. requiere sesión
Línea base de auditoría .................... requiere sesión
```

## Al reanudar (con cuentas autorizadas)

1. Autenticar al actor bootstrap y verificar identidad + permisos (§80).
2. Elegir/verificar la empresa de prueba segura (§18) y capturar aquí el snapshot completo
   (Company, estados BU, usuarios, concesiones almacenadas/efectivas, roles, permisos,
   contexto de sesión, línea base de auditoría) **antes de cualquier mutación**.
3. Crear el ledger de datos (`GA_FE_02_A_TEST_DATA_LEDGER.md`) con lo observado.

Sin secretos en este documento.

---

## Actualización · resume de self-provisioning (2026-09-11, baseline `fad6463`)

Segunda pasada con autorización de auto-provisioning. Determinación: el provisioning oficial
existe (M1/M2 UI/API admin; M3 seeds; M7 credential store externo) pero **requiere una
credencial bootstrap inyectada** que NO está presente (todas las variables documentadas: 0;
sin sesión autenticada disponible). Modo refinado:
**`BLOCKED_AUTH_BOOTSTRAP_CREDENTIAL_REQUIRED`** (cadena completa en
`GA_FE_02_A_AUTH_PROVISIONING_MAP.md` y `GA_FE_02_A_SELF_PROVISIONED_AUTH_EXECUTION.md`).

Nada cambió en el sistema: sin cuentas creadas, sin mutaciones, runtime intacto
(`index-C_aR7TJ6.js` · `35ea38e2…`), gates verdes (tsc 0 · build 0 · 198/198).

---

## Snapshot PRE-TEST capturado — 2026-09-11 (GA-FE-02-C, autenticado)

Capturado **antes de la primera mutación de la corrida de certificación** (tras el cierre de
F1 y el aprovisionamiento de actores; instrumento: API oficial con sesión del bootstrap +
sesiones propias de cada actor).

```
FECHA/HORA          2026-09-11 ~02:05Z (UTC)
REPO                main · HEAD b4d8c3a (C2) · worktree limpio
RUNTIME             200 OK · assets/index-B2-tZnkI.js · LM 01:09:24 GMT — estable toda la corrida
F1                  CLOSED — catálogo de 4 unidades presente (migración y5z6a7b8c9d0)

EMPRESA DE PRUEBA   Avícola Global C.A. (id 1)
COMPANY BU (id 1)   breeder=false · broiler=false · grandparent=false · hatchery=false
                    (las 4 recién creadas por la migración; ninguna habilitación previa)
C · RBAC            lots:read (rol 37) — fuente de la capacidad productiva representativa
C · CONCESIONES     vivas: 0 (historia: 4 revocadas del sondeo de selección de BU)
C · EFFECTIVE BU    [] (sin concesión viva)
B · PERMISOS        4 exactos (rol 35, plantilla; sin asignaciones a humanos previas a esta corrida)
A · PERMISOS        3 (rol 36: business_units read/update + dashboard:read)
D · PERMISOS        dashboard:read (rol 38)
E (bootstrap)       is_super_admin=true · 9 comodines · sin empresa efectiva al inicio
ROL 35              activo · exactamente business_units:read|update|create|delete · company_id NULL
ROLES               17 totales (14 canónicos + 3 fixtures temporales recién creados)
USUARIOS (c1)       27 (23 históricos + A/B/C/D) · (c3: 24; X incluido)
AUDITORÍA (base)    71 filas totales previas a la corrida (auth/config/users)
```

**BU objetivo seleccionado empíricamente** (sondeo por flujo oficial; restaurado tras el
sondeo): `broiler` (Engorde) — la empresa 1 tiene **2 lotes activos** `L-BO-2026-05/06`
(bird_type `broiler`), lo que permite un ALLOW observable (filas>0) y un DENY observable
(filas=0) con la misma petición representativa `GET /lots`.

```
TARGET_BU           broiler (Engorde)
POR QUÉ             2 lotes activos de la cadena en la empresa 1 → la dimensión «efectiva»
                    es observable; ruta representativa GET /lots (RBAC lots:read + row-scope
                    por unidad), no destructiva, sin depender de R-181/R-182 ni SAP.
```
