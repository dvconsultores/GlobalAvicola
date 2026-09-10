# FRONTEND REMEDIATION DEPENDENCY MAP

**2026-09-10** · grupos por causa raíz (§87), dependencias reales derivadas — no por número de página.

## 1. Grupos por causa raíz

| Grupo | Causa raíz | Capacidades | Backend listo | Decisión del propietario | Naturaleza |
|---|---|---|:--:|---|---|
| **G7 · Paridad de despliegue** | `tsc -b` rojo (R-158) × Dockerfile `npm run build` → artefacto congelado (R-99) | 13 stale + 3 rupturas vigentes (BR-20/21/22) | ✅ | no | código (2 errores) + verificación |
| **G2 · Unidades por empresa** | fase 9 nunca construida (`T-040-21`, `AC-H04`) | CAP-ADM-03 (+ parte de CAP-OPS-09) | ✅ desplegado | **autorización fase 9** (hoy `FROZEN`) | pantalla nueva |
| **G3 · Unidades por usuario** | fase 9 (`T-040-22`, `AC-H05`, `R-129` listo) | CAP-ADM-04 · CAP-ADM-05 | ✅ desplegado | autorización fase 9 | pantalla nueva |
| **G5 · Navegación y RBAC en UI** | frontend sin modelo de permisos (R-98/R-119) + wiring ausente | CAP-ADM-06 · CAP-ADM-07 · CAP-OPS-08 (R-181) | ✅ (sesión fase 8) | no (R-119 lo cubre) | refactor de menú + controles |
| **G6 · Reverso UI** | aplazado a fase 9 por el propio programa | CAP-OPS-09 | ✅ desplegado | autorización fase 9 | pantalla nueva |
| **G4 · Exposición del selector** | render condicionado + fallo silencioso del selector | CAP-SES-05 | ✅ desplegado | BU-D07 (comercial vs operativo) al diseñar fase 9 | ajuste pequeño |
| **G1 · Administración de empresas** | expectativa indefinida (SAP vs local) | CAP-ADM-02 | PARTIAL | **AOD-06 (R-124)** | espera decisión |
| **G0 · Verificación autenticada** | sin cuentas autorizadas del shared | 15 capacidades bloqueadas + cierres de journeys | — | **entregar cuentas** | auditoría (fase 7) |
| **G8 · Guardia de paridad** | nadie verifica el artefacto servido | E2E/CI (hueco de alcance) | — | no | sonda read-only / job |

## 2. Grafo de dependencias

```
G7 (paridad de despliegue)  ──►  hace visible TODO lo entregado y suelda BR-20/21/22
   │
   ├──► G2 (BU por empresa) ─┐
   ├──► G3 (BU por usuario) ─┼──► G5 (navegación dinámica) ──► G6 (reverso UI)
   │                          └──► G4 (selector: ajustes, puede ir con G2)
   │
   ├──► G0 (verificación autenticada)   ← depende de cuentas del propietario, no de G7
   ├──► G8 (guardia de paridad)         ← independiente; evita la recaída
   └──► G1 (empresas)                   ← espera AOD-06; después puede reutilizar G2/G3

SIN dependencia de fase 9: G7 · G8 · G0 · G1(decisión) · R-181 dentro de G5
CON autorización del propietario: G2 · G3 · G4 · G6 (fase 9)
```

## 3. Detalle por grupo

### G7 — Paridad de despliegue (primero)
- **Depende de**: nada.
- **Bloquea a**: visibilidad de 13 capacidades; los tres flujos hoy en 400; la utilidad de construir cualquier cosa nueva (todo lo nuevo quedaría igualmente invisible).
- **Backend**: sin cambios.
- **Trabajo**: eliminar los 6 errores de `R-158` (2 imports sin uso en `AuditPage.tsx`; 4 diagnósticos en `LotFormPage.tsx`), `npm run build` verde, push normal, Watchtower, verificación de fingerprint.
- **E2E**: comparación de hash del artefacto servido vs build de `main`; smoke de BR-20/21/22 con datos de auditoría.
- **Riesgo**: mínimo (cambios de compilación; sin lógica).

### G2/G3/G5/G6 — Fase 9 (tras autorización)
- **Depende de**: autorización del propietario (hoy `FROZEN`) y, por utilidad, de G7.
- **Contratos listos**: `business_units:*` (fase 7), `grant-candidates` (R-129), sesión completa (fase 8), `pending-classification` (fase 6), `reversals` (OD-19).
- **Restricción dura**: el Administrador de Accesos **no** debe usar `/users` (no tiene `users:read`): el selector de concesión usa `grant-candidates` (preflight fase 9 §5).
- **E2E**: J03/J04/J05/J07/J16 + permutaciones OD-16 (BU ON/OFF × grant ON/OFF × RBAC) contra entorno aislado primero; después shared.

### G0 — Verificación autenticada
- **Depende de**: cuentas autorizadas (Super Admin, Adm. de Accesos, Supervisor, Operador, Contraloría, multiempresa, zero-BU).
- **Cierra**: las 15 filas `BLOCKED_AUTH` y los journeys pendientes.

### G8 — Guardia de paridad
- **Propuesta mínima**: sonda read-only que compara `Last-Modified`/hash del `index.html` y del bundle servido contra el esperado de `main`; alerta si divergen > 1 entrega. No toca EX-01 (no modifica despliegue).
- **Evita**: repetir R-99 sin detección durante días.

### G1 — Empresas
- **Bloqueado por** `AOD-06`/`R-124` (¿SAP dueño de empresas/granjas?). No inventar CRUD.

## 4. Lo que NO entra en ningún grupo (deliberadamente)

- Reversos SAP post-SAP (`OD-12`/`AOD-04`), consolidados, huevos del reverso (`OD-19 §18`): `SAP_DEFERRED`.
- `R-141…R-148` (KPI/SAP/deuda): sus olas propias.
- Cualquier re-diseño visual: fuera de alcance (§83).
