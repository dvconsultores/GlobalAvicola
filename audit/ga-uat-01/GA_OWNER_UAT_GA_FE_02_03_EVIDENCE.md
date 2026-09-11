# GA-UAT-01 · EVIDENCIA — GA-FE-02 + GA-FE-03

**Separación estricta**: (1) Precondiciones de ingeniería · (2) Observaciones del propietario
· (3) Decisión del propietario. Las secciones (2) y (3) **permanecen vacías** hasta la sesión
del propietario — el agente no las completa por él.

---

## 1 · PRECONDICIONES DE INGENIERÍA (ejecutadas por el agente)

### 1.1 Baseline (preflight §2)
```
Branch: main · HEAD f99421e == remoto · worktree limpio
Runtime: https://avicola.globaldv.net — health 200
Frontend bundle: index-CElqNz3R.js (misma generación certificada en GA-FE-03;
                 sin movimiento de código de producto desde la certificación)
Historial: 524704e (C1) · a3cd7eb (C2) · 5608465 (C3) · f99421e (C4) — solo C2/C3 tocan
           producto y ya están certificados; f99421e es solo evidencia.
```

### 1.2 Smoke de regresión (§3)
```
TypeScript .................. TSC 0
Build ....................... PASS
Vitest (suite completa) ..... 241/241 (26 archivos) — incluye críticos GA-FE-02 y GA-FE-03
Runtime health .............. 200
Login (Super Admin) ......... 200
Selector de empresa ......... switch c1 → 200
Catálogo de unidades ........ 4/4 (breeder · broiler · grandparent · hatchery)
Nav dinámica (básico) ....... PASS (bundle servido contiene el evaluador; smoke por UI en
                              las capturas 01/02 y en los actores de prueba)
UAT_READY = YES
```

### 1.3 Fixtures UAT (18/18 — mecanismos oficiales, §6/§33)
```
UAT_SUPER_ADMIN ....... cuenta admin habitual del propietario (canónica, sin creación)
UAT_CBU_ADMIN ......... usuario UAT id 92 · rol temporal 36 reactivado (unidades: ver/habilitar)
UAT_ACCESS_ADMIN ...... usuario UAT id 93 · rol canónico 35 «Administrador de Accesos»
UAT_PRODUCTIVE_USER ... usuario UAT id 94 · rol temporal 39 (lots:read · operations:read · dashboard:read)
UAT_ZERO_BU_USER ...... usuario UAT id 95 · rol temporal 40 (dashboard:read)
Móvil operativo ....... id 96 (rol 35) · id 97 (rol 39, con Engorde YA concedido para el demo móvil)
Credenciales ........... efímeras, en archivo local FUERA del repo (600); no en evidencia;
                         se destruyen tras la sesión. Ningún usuario humano fue modificado.
Rol canónico 35 ........ intacto y activo. Auditoría: append-only conservada.
```

### 1.4 Estado inicial preparado (§5/§7 — empresa de pruebas «Avícola Global C.A.»)
```
Progenitoras (grandparent) ... INACTIVA   ← el propietario verá el contraste
Reproductoras (breeder) ...... INACTIVA
Incubadora (hatchery) ........ INACTIVA
Engorde (broiler) ............ ACTIVA     ← unidad segura de trabajo del UAT
Concesiones ................... el usuario productivo web SIN concesión (la concede el
                                propietario en UAT-05); el móvil productivo SÍ la tiene
                                (preparada para el caso 13).
Segunda empresa ............... «Avícola Del Sur C.A.» (4 unidades OFF — segura) para UAT-12.
Datos reales de clientes ...... 0 tocados.
```

### 1.5 Preparación de sesión
```
Capturas de referencia ....... 16 (ver GA_OWNER_UAT_GA_FE_02_03_SCREENSHOT_INDEX.md)
Coreografía de estados ....... ejecutada y RESTAURADA: tras capturar el flujo de concesión,
                                el usuario productivo quedó de nuevo SIN concesión (estado
                                inicial intacto verificado: eff=[] y BU broiler=ON, resto OFF)
Credenciales del propietario .. archivo local de este equipo; el Super Administrador usa su
                                cuenta habitual (no se imprime ninguna contraseña en esta
                                evidencia ni en el repositorio)
Móvil — Super Admin .......... N/A por diseño: la cuenta global es de escritorio y el rol de
                                sistema no es asignable (protección de escalada `OD-13`); el
                                recorrido móvil del UAT cubre usuario productivo y
                                administrador de accesos, que son los actores operables.
```

---

## 2 · OBSERVACIONES DEL PROPIETARIO

**PENDIENTE DE SESIÓN.** Se registran en `GA_OWNER_UAT_GA_FE_02_03_OBSERVATIONS.md`.
Ninguna casilla de resultado ha sido rellenada por el agente.

---

## 3 · DECISIÓN DEL PROPIETARIO

```
PENDIENTE — el propietario responde una de:
A) ACEPTO GA-FE-02 Y GA-FE-03
B) ACEPTO CON OBSERVACIONES: <texto>
C) RECHAZO — CORREGIR: <texto>
```

**No se infiere aceptación del silencio.** Tras la respuesta se actualizará
`GA-FE-02/GA-FE-03 OWNER: ACCEPTED / ACCEPTED_WITH_OBSERVATIONS / REJECTED`, se clasificarán
las observaciones y se ejecutará la limpieza de fixtures (§40).

### Notas de estado del programa (sin cambio durante el UAT)
```
R-98: PARTIAL (residuo intra-pantalla P-13 — no se cierra aquí)
R-119: CLOSED (verificar solo regresión — sin reapertura sin evidencia)
R-181 / R-182: UNCHANGED · BU-D10: PENDING_RATIFICATION
Wave B: PAUSED · Wave C: NOT STARTED · SAP: NOT STARTED
```
