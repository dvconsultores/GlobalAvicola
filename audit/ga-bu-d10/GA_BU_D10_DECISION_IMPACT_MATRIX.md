# GA-BU-D10 · MATRIZ DE IMPACTO DE DECISIÓN (A vs B)

Contexto: solo lectura sobre el producto; la decisión es del propietario. «A» = la concesión histórica vuelve a ser efectiva al re-encender; «B» = no vuelve; hace falta concesión nueva explícita.

## 1 · Comparación (§24)

| Eje | **A · Persistente** | **B · Re-autorización** |
|---|---|---|
| Seguridad | Reingreso automático de quienes ya tenían acceso | Mínimo privilegio; sin resurrección silenciosa |
| Mínimo privilegio | Menor (acceso latente persistente) | **Mayor** |
| Esfuerzo operativo | Ninguno al reabrir | Re-conceder usuario por usuario (flujo existente de candidatos) |
| Claridad de auditoría | El toggle de empresa es la causa del cambio de acceso; sin actos falsos de concesión | **Cada reingreso tiene un acto explícito y auditado** (PERMISSION_CHANGE); el apagado sigue auditado como CONFIG_CHANGE |
| Experiencia de usuario | Continuidad (no nota la reapertura) | Requiere re-autorización del administrador; mensajes «permiso requerido» hasta entonces |
| Flujo del Administrador de Accesos | Ninguno adicional | Regrant por «candidatos» (ya existe; no exige `users:read` — OD-15 §6 intacto). Ojo: con la línea OFF **no** puede conceder; debe encenderse primero (regla actual, se preserva) |
| SuperAdmin / actor global | No evade (OD-16 intacto); tampoco concede acceso productivo propio | Igual; además no hay auto-restauración global |
| Toggle de empresa | Reversible puro (actual) | El toggle gana semántica de ciclo: **apagar termina la efectividad futura** de las concesiones de esa unidad |
| Navegación / deep links | Se restauran al reabrir | Permanecen ocultos/denegados hasta nuevo grant |
| Sesión / refresh | Sin privilegio obsoleto (relectura por petición) | Igual (relectura por petición); no depende de token |
| Concesiones históricas | Viven y reviven | Se conservan para auditoría; **no** reviven |
| Consistencia con transferencia de empresa (OD-09.e) | **Divergente** con la analogía («volver no prueba el mismo cargo») | **Consistente** con la analogía; aun así la decisión es propia (no automática) |
| Migración de datos | Ninguna | **Ninguna obligatoria**: representable con columnas actuales (mecanismo exacto en SPEC); sin borrado masivo |
| Riesgo de esquema | Nulo | Bajo (mecanismo a fijar; p. ej. marcar al apagar o regla de ciclo con `updated_at`) |
| Compatibilidad con conducta actual | = actual (cero producto) | Cambia conducta provisional; actualiza pruebas `AC-A04/AC-A06` y la nota «provisional» del contrato |
| Impacto en tests | Caracterización (las pruebas actuales ya prueban A) | RED necesario (la auto-reactivación actual es el defecto a corregir) + ajustes AC-A04/A06 |
| UAT del propietario | No requerida si no hay cambio de producto (la decisión bastaría; gobernanza) | **Requerida** (cambia comportamiento visible de acceso) |

## 2 · Consecuencia sobre datos actuales (§25)

| Ítem | Valor |
|---|---|
| ¿Las concesiones se persisten con la empresa OFF? | **SÍ**, por diseño (AC-A04). «Apagar no revoca». |
| Población del entorno de prueba (empresa 1) | 91 usuarios; **2** con concesión viva (ambas `broiler`), ambos fixtures de certificación — conteo anonimizado 2026-09-11 (**sin PII**). Las 4 unidades de la empresa 1 están OFF hoy: ninguna concesión es efectiva. |
| ¿B exige distinguir «histórica» de «fresca»? | Sí (por ciclo de habilitación). **Representable sin migración** con las columnas/registros actuales; el mecanismo se especifica post-decisión. En cualquier caso: **sin pérdida de historia, sin borrado masivo, sin migración destructiva**. |
| ¿A exige cambios de datos? | No. |

## 3 · Certificaciones afectadas (§29 del encargo: «CERTIFICATIONS AFFECTED»)

- **Ninguna por elegir A sin brecha** (si A = actual): se preservan OD-16, GA-FE-02..07, R-184/185/186/187, OD-21/22.
- **B toca superficies certificadas**: GA-FE-02 (admin BU/tenant), GA-FE-03 (navegación por acceso efectivo), GA-FE-04 (autoridad por acción) — sus invariantes siguen valiendo (usan acceso efectivo), pero el **comportamiento visible** cambia ⇒ exige recertificación runtime dirigida + UAT del propietario. OD-16 sigue intacto (OFF absoluto) en ambas.
- **Transferencia de empresa**: en ambas opciones **NO se toca** (regla separada OD-09.e; se re-verifica como regresión).
