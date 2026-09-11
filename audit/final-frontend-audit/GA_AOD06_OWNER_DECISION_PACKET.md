# AOD-06 · PAQUETE DE DECISIÓN DEL PROPIETARIO — PROPIEDAD DE EMPRESAS Y GRANJAS

Capacidad: **FVA-07 / CAP-ADM-02 «Administración de empresas (crear/editar metadatos)»** · Finding: **R-124** · Prioridad: **P1** (verificada: «antes de WAVE D; no bloquea fase 9») · Fecha: 2026-09-11 · RFC: reconstrucción completa desde `REMEDIATION_BACKLOG.md:722-730`, `AUDIT_OWNER_DECISIONS_REQUIRED.md:18`, `docs/10 §3.1`, `docs/02 §3.2.1`.

## 1 · Pregunta exacta sin resolver (canónica)

> ¿Las **Empresas** y las **Granjas** «vienen de SAP» (sociedad/centro) — importadas y no editables — o son **maestros locales** con código SAP? — `AUDIT_OWNER_DECISIONS_REQUIRED.md:18`.

Sub-preguntas registradas en R-124 (texto literal):
1. ¿Es SAP el dueño de Empresas? ¿Y de Granjas? ¿Contra qué objeto SAP?
2. ¿Réplica de solo lectura, o copia con extensión local declarada?
3. ¿Qué pasa con las creadas localmente hasta hoy?
4. ¿Y con `sap_config`, hoy campo editable de la empresa?

## 2 · Estado actual del producto (hechos, no opiniones)

- **Empresas y Granjas son catálogos base LOCALES** con campos propios (`docs/02 §3.2.1`); el código cumple la spec: maestros administrables en `/masters/companies` y `/masters/farms` (CREATE/UPDATE gateados `masters:create/update`), tenant-scoped.
- **`sap_config`** es hoy un campo editable de la empresa; backend de la capacidad declarado `PARTIAL` (`sap_config` DEFERRED) en el catálogo histórico.
- **Lo que SAP importa** según `docs/10 §3.1`: Centros, Almacenes, Materiales, Proveedores, Lotes, OC, OT — **«Ni Empresas ni Granjas»**.
- **Arquitectura vigente (declarada por el propietario):** SAP S/4HANA será el *source of record* transaccional (centros/plantas, almacenes, materiales, proveedores, inventario, costos…); Global Avícola es captura/validación/evidencia/aprobación. La integración real (**P-08**) está **BLOCKED_EXTERNAL**; no hay conector, HANA ni credenciales.
- **Existen placeholders declarados** (`SAP_DEFERRED_LOCAL_PLACEHOLDERS PL-05/06`) para la etapa pre-SAP.
- **Conflicto documental nivel 2 vs nivel 3**: el reconocimiento de flujos (Rec. §1/§15) espera propiedad SAP; `docs/02 §3.2.1` define maestros locales. **El código cumple la spec; la spec no cumple la expectativa** — no es defecto de implementación (R-124).
- Efecto visible hoy: el administrador **puede crear/editar** Empresas/Granjas localmente; al llegar SAP, si fueran espejo, esas ediciones quedarían contradiciendo al maestro.

## 3 · Opciones canónicas (las registradas — no se inventan)

**OPCIÓN A — Importadas de SAP, no editables** (SAP soberano).
- Negocio: Empresa≈Sociedad (`company`) y Granja≈Centro/Planta (mapeo a definir en SPEC al integrar); los catálogos se pueblan desde SAP y son read-only. Pre-SAP: se opera con **placeholders locales provisionales declarados** (PL-05/06), sin pretender ser maestro SAP.
- Seguridad: sin cambios de RBAC; se elimina el riesgo de deriva maestro-app.
- Pre-SAP: exige declarar formalmente el régimen provisional (qué se permite crear hoy y cómo migrará).
- Post-SAP: convergencia total; ediciones locales bloqueadas; `sap_config` gobernado por SAP.
- Impacto implementación: **cero código hoy**; SPEC de régimen provisional/mapeo a redactar antes de P-08; R-124 se cierra como **decisión de arquitectura de datos**.

**OPCIÓN B — Locales con `sap_code` obligatorio** (vínculo duro desde ya).
- Negocio: GA sigue siendo el maestro; cada Empresa/Granja exige identificador SAP (sociedad/centro) como llave de futura conciliación.
- Seguridad: igual; introduce dependencia de numeración SAP aún sin integración (códigos manuales → riesgo de error).
- Pre-SAP: operable, con fricción (todo alta exige código SAP que aún no se puede validar contra S/4).
- Post-SAP: conciliación por código; si SAP «manda», habrá que decidir editabilidad caso a caso.
- Impacto implementación: SPEC pequeña (validación/obligatoriedad `sap_code` + UI) — **producto**.

**OPCIÓN C — Locales sin vínculo (estado actual ratificado)**.
- Negocio: GA maestro permanente; SAP no gobierna estos catálogos (docs/02 §3.2.1 ratificada como contrato).
- Seguridad: igual.
- Pre-SAP: cero fricción (hoy).
- Post-SAP: sin llave de conciliación → deuda futura si se quiere enlazar OC/lotes a sociedades/centros.
- Impacto implementación: **cero código**; cierra R-124 como «spec ratificada» (la expectativa nivel-2 queda descartada de forma explícita).

## 4 · Recomendación (ingeniería)

**OPCIÓN A** — es la única coherente con la arquitectura declarada por el propietario (§2, SAP source-of-record, incl. centros/plantas) y con la dirección de gobierno de datos del programa; B es un paso intermedio con fricción pre-SAP; C ratifica el estado actual y traslada toda la conciliación al futuro (riesgo de deriva).

Motivo de la recomendación: A evita que un maestro local edite lo que SAP considerará canónico, sin exigir código hoy (P-08 externo), y reutiliza los placeholders ya declarados para la etapa provisional.

## 5 · Efectos sobre el cierre

- **CURRENT FRONTEND BLOCKED (cierre formal): YES** — la fila FVA-07 permanece `OWNER_DECISION_REQUIRED` mientras no haya decisión (sin gap funcional; la UI opera).
- **WAVE B READINESS BLOCKED: YES** — condición §32 «no pending frontend Owner decision».
- **IMPLEMENTATION STARTED: NO.**

## 6 · Decisión solicitada

**A)** Importadas de SAP, no editables (con régimen provisional local declarado pre-P-08 — `PL-05/06`) · **B)** Locales con `sap_code` obligatorio · **C)** Locales sin vínculo (ratificar estado actual).

**RESPONDA SOLO: A / B / C** — tras la respuesta: formalización canónica (registro de decisiones), determinación de gap de implementación (A/C: sin producto hoy; B: finding→SPEC) y continuación del programa de residuales.
