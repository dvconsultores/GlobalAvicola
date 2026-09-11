# GA-FE-06 · MATRIZ DE ACTORES (runtime autenticado)

Cuentas sintéticas (se destruyen en higiene §101; jamás se registran credenciales). Datos reales: Empresa A `1` «Avícola Global C.A.» · Empresa B `3` «Avícola Del Sur C.A.» · BUs: breeder/broiler/grandparent/hatchery (todas OFF al inicio).

| Actor | Empresa | Rol | Permisos | BUs concedidas | Uso en certificación |
|---|---|---|---|---|---|
| **A** (admin existente GA_FLOW_USER) | — | Admin | todo | — | Provisionar/limpiar fixtures; NUNCA para los flujos a certificar |
| **C** «Operador GA-FE-06» | A (1) | R35 «Operador Lotes GA-FE-06» (nuevo) | `dashboard:read` · `lots:read` · `lots:create` · `operations:read` · `masters:read` | `broiler` (ON en ventana de prueba) | Titular E2E-01…16: crea lotes por UI con PLD/área; lee fresh GET; recibe/consulta avisos SLA |
| **D** «RBAC-contenido» | A (1) | R36 «Solo-lectura GA-FE-06» (nuevo) | `dashboard:read` · `lots:read` | ninguna | E2E-08 no-bypass RBAC: `/lots/new` guard + API 403 |
| **E** «Sin ventana» | A (1) | R37 «Operador sin BU GA-FE-06» (nuevo) | idénticos a C | **ninguna** | E2E-09 CBU: UI gate `requiresUnits` + API 403 por `_exigir_unidad_operativa` |

Reglas de actores:

- C requiere `masters:read` porque el alta de lote consume `/masters/*` (granjas, galpones, áreas…). Sin ese permiso el formulario no puede poblar selectores — se documenta como dependencia del formulario, no como bypass.
- D y E **no** reciben `lots:create`+BU simultáneamente (D: sin create; E: create sin BU) ⇒ dos vectores independientes de contención.
- B no participa como actor: solo como **inquilino ajeno** (Área X de la empresa B para E2E-06 cruce de empresa).
- Toda cuenta/rol/area/lote/grant creado queda anotado en `GA_FE_06_TEST_DATA_LEDGER.md` con su plan de retirada.
