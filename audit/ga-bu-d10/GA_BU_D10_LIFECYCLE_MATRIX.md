# GA-BU-D10 · MATRIZ DE CICLO DE VIDA (L1-L16) — OD-23 · B

Columnas: estado → resultado esperado bajo **B** → mecanismo → evidencia.

| # | Escenario | Esperado | Mecanismo | Evidencia |
|---|---|---|---|---|
| L1 | Empresa BU ON + concesión viva | **efectiva: SÍ** | resolutor (4 puertas) | suite R-188 + E2E-01 |
| L2 | Empresa BU OFF + concesión «histórica viva» (ciclo previo) | **efectiva: NO** | apagado la marcó (OD-23 §5) | suite + E2E-02 |
| L3 | Empresa BU OFF + actor global | **productivo NO** | OD-16 (habilitadas) | suite OD-16 + E2E-11 |
| L4 | Empresa BU OFF + Access Admin | administra según control-plane; **productivo NO** | admin.py sin `unidades_efectivas` | E2E-08 |
| L5 | Empresa BU re-encendida + concesión previa | **NO efectiva** (B) | marcada al apagar; enable no revive | suite + E2E-04 (RED→GREEN) |
| L6 | Re-encendida + cero concesiones | **productivo NO** hasta concesión | resolutor | E2E-04 |
| L7 | Concesión nueva explícita tras encender | **efectiva: SÍ** | `POST /users/{id}/business-units` | E2E-05 + auditoría |
| L8 | RBAC ausente (con todo lo demás) | **NO** | guard RBAC posterior | E2E-09 |
| L9 | Sin concesión | **NO** | resolutor | E2E-10 |
| L10 | Usuario zero-BU | CORE por RBAC; **0 productivo** | OD-09.c | E2E-10 |
| L11 | Transferencia A→B | grants de A: **inefectivos** | empresa de la habilitación ≠ actual | suite transfer (preservada) |
| L12 | Regreso B→A | **no reactiva**; concesión nueva requerida | `revocar_concesiones` (OD-09.e) | suite AC-B12 (intacta) |
| L13 | Self-grant del Access Admin | **DENY** | OD-15.a (primera puerta) | E2E-07 |
| L14 | Grant cross-company | **DENY/404** | misma-empresa | E2E-08 |
| L15 | Apagado con sesión activa | **siguiente petición: DENY** | relectura por petición | E2E-06 |
| L16 | Re-encendido con sesión activa | **B: sigue DENY** hasta concesión nueva; sin privilegio de token | relectura + marca de §5 | E2E-06/04 |

Controles positivos obligatorios: L1 y L7 (ALLOW) con API productiva directa; negativos L2/L5/L6 con la misma API.
