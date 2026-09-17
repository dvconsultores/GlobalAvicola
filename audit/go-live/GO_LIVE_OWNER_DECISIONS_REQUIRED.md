# GLOBAL AVÍCOLA — GO-LIVE · OWNER DECISIONS REQUIRED

Fecha: 2026-09-17 · Baseline: `fef7289` · Estado: **PROPUESTA — ninguna decisión tomada por el agente**
Reconciliación pre-SAP-0: `GL-OD-06 = PENDING_SAP0_DISCOVERY`; las demás `PENDING_OWNER_DECISION` (**no ejecutar aún**).

> **Dependencia registrada**: `SAP-0 → GL-OD-06 → REAL DATA MIGRATION → CUTOVER G1/G2`.
> SAP **no** se marca como fuente definitiva hasta verificar el landscape actual (SAP-0).
Formato por decisión: contexto · opciones · recomendación técnica · impacto si se difiere.

---

### GL-OD-01 · Topología productiva
- **Contexto**: hoy un solo host Docker compartido (UAT/test/certificación).
- **Opciones**: (A) instancia nueva para operación real (recomendada); (B) reutilizar el host compartido endurecido.
- **Recomendación**: (A) — separa datos reales de fixtures, permite archivado del UAT como evidencia, evita contaminación.
- **Si se difiere**: bloquea G2/G3 (INF-01).

### GL-OD-02 · Mecanismo de despliegue en producción
- **Contexto**: `DEPLOYMENT_MECHANISM = B` (push→Actions→Hub→Watchtower auto) está autorizado **solo** para el entorno compartido.
- **Opciones**: (A) mantener B para prod (auto-rollout); (B) **deploy gated**: mismo build, pero promoción aprobada por ventana (recomendada para datos reales); (C) mixto (backend gated, frontend auto).
- **Recomendación**: (B) — un cambio no aprobado no debe llegar solo a producción con datos reales.
- **Si se difiere**: bloquea INF-02/G2.

### GL-OD-03 · Observabilidad y alertas
- **Contexto**: no existe monitoreo (INF-03). 
- **Opciones**: (A) mínimo viable auto-hospedado (uptime + alertas por webhook/telegram/correo); (B) servicio externo (Sentry/UptimeRobot-like); (C) sin monitoreo en v1.
- **Recomendación**: (A) o (B) — umbral mínimo: contenedor caído, disco >80 %, backup fallido, errores 5xx sostenidos.
- **Si se difiere**: riesgo operacional alto; no bloquea G2 pero sí el gate si se exige.

### GL-OD-04 · Correo saliente
- **Contexto**: no hay SMTP (INF-04). Notificaciones existen solo in-app; restablecimiento de clave es por admin.
- **Opciones**: (A) contratar/configurar SMTP y habilitar email en v1; (B) declarar email **fuera de v1** con workaround documentado (admin resetea claves; notificaciones in-app).
- **Recomendación**: (B) para v1 (menor superficie), (A) como primera mejora post-go-live.
- **Si se difiere**: los usuarios deben consultarse in-app (aceptable); registrar como observación del gate.

### GL-OD-05 · Backups off-site + restore probado
- **Contexto**: política local existe (diaria+pre-upgrade; RPO≤24h/RTO≤4h) pero sin destino off-site ni ensayo reciente.
- **Opciones**: destino (A) otro host propio; (B) almacenamiento de objetos (S3-compatible); cadencia de prueba: trimestral o por release.
- **Recomendación**: (B) + prueba mensual automatizable + evidencia en cada release.
- **Si se difiere**: **BLOQ** para el gate (INF-05).

### GL-OD-06 · Acceso a datos reales — `PENDING_SAP0_DISCOVERY`
- **Estado**: **`PENDING_SAP0_DISCOVERY`** — no se resuelve todavía. Motivo: la identificación de las fuentes reales de datos depende de determinar **qué datos siguen disponibles en el SAP actual y mediante qué mecanismo** (fase SAP-0).
- **Dependencia**: `SAP-0 → GL-OD-06 → REAL DATA MIGRATION → CUTOVER G1/G2`.
- **Contexto**: no hay acceso a fuentes reales (DATA-01).
- **Decisión (cuando SAP-0 concluya)**: designar responsable que entrega las fuentes por dominio (D1–D13), formato y mecanismo (SAP y/o planillas), con autorización de uso; el reparto SAP vs planillas se fijará con el informe de landscape.
- **Si se difiere**: bloquea G1→G3 completos. SAP **no** es fuente definitiva hasta verificar el landscape actual.

### GL-OD-07 · Estrategia de limpieza y retención
- **Contexto**: entorno actual = ficticio (inventario en `DATA_CLEANUP_PLAN.md`).
- **Opciones**: (A) instancia nueva (recomendada con GL-OD-01-A) — sin borrado, el UAT queda como archivo; (B) limpieza en sitio autorizada (plan+backup+ventana).
- **Decisión**: elegir A o B; además: retención de la evidencia de certificación (clase C) — recomendado: conservar 12 meses.
- **Si se difiere**: bloquea la provisión del runtime real.

### GL-OD-08 · OD-19 (NBO-03) — reverso de huevos/incubación
- **Contexto**: diferido declarado; impacta correcciones operativas de planta.
- **Opciones**: (A) aceptar limitación para Go-Live con procedimiento alternativo (corrección vía eventos compensatorios/papel hasta implementación); (B) programar la porción antes de Go-Live (G2 ampliado).
- **Recomendación**: (A) si el volumen real lo permite (validar con responsable funcional); (B) si no hay workaround aceptable.
- **Si se difiere**: observación del gate sin clasificar (no se puede declarar READY).

### GL-OD-09 · Secretos y rotación
- **Contexto**: `.env` en host (INF-06).
- **Decisión**: rotación inicial pre-Go-Live (JWT, BD, claves de servicio), custodios, periodicidad (p. ej. semestral) y registro sin exponer valores.
- **Si se difiere**: **BLOQ** (INF-06).

### GL-OD-10 · Dominio y DNS productivos
- **Decisión**: dominio definitivo (o reutilizar `avicola.globaldv.net`), certificado y renovación, TTL y plan de conmutación.
- **Si se difiere**: **BLOQ** (INF-07).

### GL-OD-11 · Usuarios reales, admins y MFA
- **Contexto**: NBO-01/INF-10; el producto no tiene MFA.
- **Decisión**: política de cuentas nominales, quién es admin, aceptación explícita de `MFA_NOT_AVAILABLE_IN_V1` (o requisito de MFA como precondición), rotación de claves inicial.
- **Si se difiere**: **BLOQ** para el gate (incluye provisión).

### GL-OD-12 · Responsables funcional y técnico
- **Decisión**: designar formalmente responsable funcional (valida datos, firma acta, opera) y técnico (infra, backups, incidentes, rollback), con suplentes.
- **Si se difiere**: bloquea rehearsal (firmas) y gate.

### GL-OD-13 · AOD-13 (heredado Pre-SAP)
- **Contexto**: registro administrativo pendiente (unidad de `farm_inspection` sin lote).
- **Decisión**: confirmar opción A/B/C ya estudiada y registrarla; no requiere código en esta fase.
- **Si se difiere**: observación administrativa del gate (no técnica).

---

## Resumen de estados (reconciliado pre-SAP-0)

| Decisión | Estado |
|---|---|
| **GL-OD-06** (datos reales) | **`PENDING_SAP0_DISCOVERY`** |
| GL-OD-01, 02, 03, 04, 05, 07, 09, 10, 11, 12, 13 | **`PENDING_OWNER_DECISION`** — no ejecutar aún |
| GL-OD-08 (OD-19, funcional — independiente de SAP) | **`PENDING_OWNER_DECISION`** — no ejecutar aún |
| Cadena de dependencia | `SAP-0 → GL-OD-06 → REAL DATA MIGRATION → CUTOVER G1/G2` |

> Ninguna de estas decisiones fue tomada por el agente. SAP no se marca como fuente definitiva hasta verificar el landscape actual. Cuando se registren, cada una se anexa aquí con el **texto exacto** del Owner y se refleja en el roadmap (G1→G2).
