# GLOBAL AVÍCOLA — GO-LIVE INFRASTRUCTURE READINESS

Fecha: 2026-09-17 · Baseline: `fef7289` · Estado: **EVALUACIÓN (sin cambios de infraestructura)**
Regla: «Pre-SAP certificado ⇏ producción lista». Esta evaluación declara cada área como `OK`, `GAP` o `DEC`.

---

## 1 · Evaluación por área (mandato §6)

| Área | Estado hoy | Objetivo operación real | Clasificación | Acción / Decisión |
|---|---|---|---|---|
| Servidor de aplicación | 1 VPS compartido (`84.247.161.106`), Docker Compose single, openresty frontal | Instancia de operación separada del UAT (recomendado) o endurecimiento del host si se reutiliza | **DEC** | `GL-OD-01` |
| PostgreSQL | Contenedor en el mismo host; backups locales según política | BD de producción + backups off-site + restore probado | **DEC/GAP** | `GL-OD-01`, `GL-OD-05` |
| Backups | `GA_T13_BACKUP_POLICY.md`: diaria + pre-upgrade; RPO ≤24h / RTO ≤4h; verificación trimestral | Añadir: destino off-site, retención probada, restore ensayado sobre copia | **GAP** | `GL-OD-05` (ver clase INF-05) |
| Restore | Procedimiento documentado; sin ensayo reciente sobre copia productiva | Ensayo con evidencia antes del Go-Live | **GAP** | Incluido en rehearsal (`CUTOVER_REHEARSAL_PLAN.md` §6) |
| SSL | Certificado activo para `avicola.globaldv.net` (openresty) | Dominio productivo declarado + renovación automatizada verificada | **DEC** | `GL-OD-01/10` (INF-07) |
| DNS | Dominio UAT resuelto | Dominio definitivo + TTL/plan de cambio | **DEC** | `GL-OD-10` |
| Docker | Compose único; imágenes desde Docker Hub (`sha-<corto>`/`latest`) | Igual pero en instancia separada + imágenes fijadas por digest | **OK/DEC** | Fijar digest en despliegues prod (`GL-OD-02`) |
| Watchtower | Auto-actualización (60 s) — adecuado para UAT compartido | Para producción: **deploy gated** (aprobación por ventana) recomendado | **DEC** | `GL-OD-02` (INF-02) |
| Observabilidad | **Inexistente** (sin métricas, alertas, uptime, error tracking) | Mínimo: uptime + alertas (contenedor caído, disco, backup fallido) + retención de logs | **GAP** | `GL-OD-03` (INF-03) |
| Logs | `docker logs`; rotación limitada | Retención definida (p. ej. 90 días) + agregación simple | **GAP** | `GL-OD-03` |
| Storage | Volumen de media local (`MEDIA_DIR`) | Incluir en backup; capacidad calculada | **OK/GAP** | `GL-OD-05` |
| Correo | **No existe** SMTP saliente; notificaciones solo in-app | Email para notificaciones/restablecimiento **o** declarar alcance v1 sin email (workaround admin) | **DEC** | `GL-OD-04` (INF-04) |
| Secretos | `.env` en host; JWT/DB/medias | Rotación inicial pre-Go-Live + custodios + rotación periódica; sin secretos en git (ya se cumple) | **GAP** | `GL-OD-09` (INF-06) |
| Usuarios técnicos | Cuenta UAT del canal; admins técnicos reales por definir | Cuentas nominales (no compartidas) + política de baja | **GAP** | `GL-OD-11` (INF-10) |
| Rotación de credenciales | Sin rotación formal | Procedimiento + calendario | **GAP** | `GL-OD-09` |
| Disponibilidad | Un nodo, sin HA; ventanas de reinicio breves | Aceptar single-node para v1 (decisión) o HA futuro | **DEC** | `GL-OD-01` (parte) |
| Recuperación | RTO ≤4h declarado | Ensayo real de restore dentro del rehearsal | **GAP** | Rehearsal §6 |
| Mantenimiento | Alembic por entrypoint (canónico GA-REM-024) | Ventanas de mantenimiento acordadas | **OK/POST** | INF-11 |
| Capacidad | Sin métricas de carga real | Sizing tras rehearsal (medir) | **DEC** | INF-08 |
| Seguridad | Rate-limit activo, RBAC fail-closed, X-BU, tenancy; sin WAF/MFA | Aceptar riesgos declarados (sin MFA v1) o añadir controles | **DEC** | `GL-OD-11` |

## 2 · Checklist de preparación operacional (mandato §8)

**Accesos y personas**
- [ ] Usuarios reales creados nominalmente (sin cuentas compartidas) — D14
- [ ] Roles reales mapeados al catálogo de permisos del producto — D15
- [ ] Grants de Business Unit por usuario/empresa verificados (fail-closed) — D16
- [ ] Cuentas admin reales de operación (NBO-01) probadas
- [ ] Responsable funcional designado (valida cutover y opera) — `GL-OD-12`
- [ ] Responsable técnico designado (infra, backups, incidentes) — `GL-OD-12`

**Datos**
- [ ] Empresas/BUs habilitadas reales — D1/D2
- [ ] Maestros reales activos (alimentos, causas, vacunas, medicamentos, proveedores, transportes, fases) — D13
- [ ] Datos iniciales (openings) aplicados, reconciliados y firmados — D17
- [ ] Referencias SAP sintéticas excluidas del runtime real — limpieza clase D

**Infra**
- [ ] Backup inicial completo verificado + copia off-site — `GL-OD-05`
- [ ] **Restore probado** (sobre copia, con evidencia) — rehearsal §6
- [ ] Monitoreo y alertas activos (contenedor, disco, backup, uptime) — `GL-OD-03`
- [ ] Correo resuelto o alcance declarado (`GL-OD-04`)
- [ ] Secretos rotados + custodios — `GL-OD-09`
- [ ] SSL/DNS productivos + renovación — `GL-OD-10`

**Operación**
- [ ] Procedimiento de incidentes (contacto, escalado, severidades)
- [ ] Rollback: restore a pre-cutover + re-apply gobernado (documentado)
- [ ] **Contingencia manual** (qué hacer si el sistema no está disponible en el arranque: registro en papel/minuta con re-captura posterior) — INF-09
- [ ] Ventana de congelación coordinada (freeze) por BU — `CUTOVER_MASTER_SPEC.md` §4
- [ ] Runbook de apertura operacional D+0 (primeros registros reales, verificación de saldos)

## 3 · Resultado

- Áreas **GAP** que bloquean Go-Live: backups/restore (INF-05), observabilidad (INF-03), correo si se exige email (INF-04→DEC), secretos (INF-06), dominio productivo (INF-07), contingencia (INF-09), usuarios técnicos/admin (INF-10).
- No se modifica infraestructura en esta fase. Cada GAP tiene decisión asociada en `GO_LIVE_OWNER_DECISIONS_REQUIRED.md`.
