# GA · PRE-SAP — T13 · KIT UAT DEL PROPIETARIO (8 LOTES U1–U8)

Fecha: 2026-09-16 · Base: `GA_PRE_SAP_OWNER_UAT_RECERTIFICATION_PLAN.md` §3/§4
(regla §32) + roadmap T13 · Estado: **preparación entregada** — las sesiones de
decisión pertenecen al propietario.

## 0 · Uso de este kit

1. **Preparación común** (por sesión): entorno arriba, seeds y readiness en verde,
   guía de flujo vigente.
2. **Ejecución por lote**: casos en orden; cada caso con **resultado propio**
   (PASS / FAIL / OBS), nunca un PASS heredado de una «A» global.
3. **Decisión del propietario** por lote: fecha + canal + **texto exacto** +
   lote de casos ejecutado + hash del artefacto de walkthrough del equipo.
   El walkthrough del equipo es evidencia técnica, **nunca** aceptación.
4. **Evidencia primaria admisible**: mensaje del propietario, captura/grabación
   propia, o su `LOGIN` en `audit_logs` dentro de la ventana declarada.
   Capturas del equipo: **discriminantes** (sin md5 duplicado entre casos).
5. **Limpieza**: solo después de la decisión registrada y verificada, con
   artefacto de limpieza (fixtures/usuarios/lotes/credenciales).

### Preparación común (comandos)

```bash
# Backend + frontend (entorno de pruebas)
docker compose -f docker-compose.dev.yml up -d     # o el arranque local del equipo
cd backend && PYTHONPATH=. python3 seeds/live_readiness_check.py   # ⇒ READY
```

Referencia de flujo por proceso y usuarios por rol: `GUIA_PRUEBAS_EN_VIVO.md`
(§1 credenciales por canal seguro; §3 escenarios A-F).
Credenciales UAT-09: `~/ga_uat09_credentials.txt` (canal seguro; no se publican).

## 1 · Lotes (prioridad: U1 y U2 primero)

| # | Lote | Procesos | Prioridad | Casos núcleo | Evidencia mínima |
|---|---|---|---|---|---|
| U1 | Plataforma y seguridad | P-13, X-BU | **1** | login · logout con revocación (AC04) · rol sin wildcard (R-199) · refresh no usable como access · reset en contexto · permisos batch · switch empresa/BU | decisión + capturas discriminantes (admin real) + `LOGIN`/`LOGOUT` en `audit_logs` de la ventana |
| U2 | Progenitoras | P-01, OD-25 | **2** | **GA-UAT-09 retry (R-153/R-189)**: import 121 → recepción 122 → población 100 · ubicación BR-08 · BR-18/BR-20 · decisión sobre casos C1/C2/C3 (ledger GA-R153) | decisión + artefactos de corrida (import/recepción/población) |
| U3 | Reproductoras | P-03 | 3 | curvas · distribución por galpón (BR-17) · recepción BR-20 por navegación natural | decisión + capturas discriminantes |
| U4 | Incubadora | P-04, P-05 | 3 | huevos fértiles · carga · nacimiento (BR-21) · despacho (BR-04) · KPIs incubadora por unidad | ídem |
| U5 | Engorde y cierre | P-06, OD-19 | 3 | pesajes g/kg · alimento · cierre de lote · cierre tras reverso · FCR/peso final (Wave C: `FCR = alimento/ganancia`; sin pesos ⇒ UNKNOWN, nunca 0) | ídem |
| U6 | Revisión y reverso | P-07 | 3 | bandejas `in_review` · reverso interno UI (R-207) · aprobación multinivel (condicionada a AOD-17 — R-142 diferida: **no aplica hoy**) · cancelación con motivo (AOD-18 — **no aplica hoy**) | ídem |
| U7 | Reportes y trazabilidad | P-15, P-10, P-09 | 3 | KPIs corregidos (R-204 + Wave C) · IPE (revalidación R-187: edad congelada en lote cerrado) · trazabilidad 3 generaciones · auditoría visible | ídem |
| U8 | Maestros y usuarios | P-12, P-13, P-11, P-14 | 3 | alta de maestros completa · edición de usuario · activación manual (condicionada a OD-10.c) · notificaciones | ídem |

### Detalle por lote

**U1 · Plataforma y seguridad.** Usar un **usuario admin real**. Verificar:
(1) login ok; (2) logout **revoca** (el access previo deja de servir; `LOGOUT`
visible en `audit_logs`); (3) un rol acotado **no** obtiene wildcard (R-199);
(4) un refresh token **no** se acepta como access; (5) reset de contraseña en
contexto de la empresa correcta; (6) operaciones batch respetan permisos;
(7) switch de empresa/BU aísla datos (X-BU).

**U2 · Progenitoras (GA-UAT-09).** Ejecutar el retry con el usuario
Operador/Aprobador R-153 (credenciales en el canal seguro). Secuencia de oro:
importación **121** → recepción **122** → población **100**; ubicación BR-08;
cierre BR-18/BR-20. La decisión debe incluir expresamente el veredicto sobre los
3 casos **C1/C2/C3** registrados en el ledger GA-R153.

**U3–U8.** Flujos guiados por `GUIA_PRUEBAS_EN_VIVO.md` §3 (escenarios A-F) con
los cambios vigentes (T4–T14 + Wave C). En U7, el IPE de lotes cerrados **no
debe** seguir creciendo (edad congelada) y el FCR sin evidencia de pesos debe
mostrarse como UNKNOWN, no como número.

## 2 · Plantilla de registro de decisión

| Lote | Fecha/hora | Canal | Texto exacto (propietario) | Casos | Resultado por caso | Artefactos (nombre + sha256) | `LOGIN`/`LOGOUT` audit_logs (id/fecha) |
|---|---|---|---|---|---|---|---|
| U1 | | | | | | | |
| U2 | | | | | | | |
| … | | | | | | | |

**Reglas de cierre por lote**: decisión registrada + evidencia primaria adjunta +
resultado por caso + limpieza con artefacto posterior. Si un lote revela un
defecto ⇒ vuelve a su tranche (o micro-tranche correctiva) y el lote se repite;
no se acepta con reservas no escritas.

## 3 · Criterio de cierre T13 (gate final)

`PRE_SAP_FUNCTIONAL_CERTIFICATION = PASS` exige: 17/17 procesos certificables +
suites verdes + **UAT primaria** (U1–U8 con evidencia primaria) + **Pista OPS**
(G-02…G-05 ejecutados con evidencia) + decisiones §25 aplicadas ⇒ veredicto
**GO/NO-GO** del propietario.
