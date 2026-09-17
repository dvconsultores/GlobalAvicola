# GLOBAL AVÍCOLA — GO-LIVE OWNER GATE

Fecha: 2026-09-17 · Baseline: `fef7289` · Estado: **GATE DISEÑADO — decisión exclusiva del Owner**
El agente **no** declara el Go-Live: este documento define qué debe estar completo para que el Owner decida.

---

## 1 · Opciones de decisión (vocabulario fijo)

- `GO_LIVE_READY` — todo completo, sin observaciones abiertas.
- `GO_LIVE_READY_WITH_OBSERVATIONS` — completo con observaciones declaradas y aceptadas por el Owner.
- `NO_GO_LIVE` — falta algo bloqueante; se registra causa y se reprograma.

## 2 · Paquete de gate (debe estar COMPLETO antes de convocar al Owner)

### A · G0 — este pack (COMPLETO ✔)
- [x] Assessment, Master Spec, Gap Matrix, Plan de datos, Plan de limpieza, Infra, Rehearsal, Roadmap, Decisiones requeridas.
- [x] Baseline congelado (`fef7289`); evidencia de inventario de runtime.

### B · Decisiones del Owner (`GO_LIVE_OWNER_DECISIONS_REQUIRED.md`) — **pendiente**
- [ ] GL-OD-01 topología · GL-OD-02 despliegue prod · GL-OD-03 observabilidad · GL-OD-04 correo · GL-OD-05 backups off-site · GL-OD-06 acceso a datos reales · GL-OD-07 limpieza/retención · GL-OD-08 OD-19 · GL-OD-09 secretos · GL-OD-10 dominio · GL-OD-11 usuarios/admin ▼ MFA · GL-OD-12 responsables · GL-OD-13 AOD-13.

### C · Ingeniería G2 (extensiones del cutover) — **pendiente**
- [ ] CUT-GL-01 acta de firma · CUT-GL-02 guarda de fecha · CUT-GL-03 secuencia multi-BU · CUT-06 auditoría fina incubadora · (según decisión) CUT-04/CUT-05.
- [ ] Cada AC con su cadena completa (SPEC→AC→RED→IMPL→GREEN→regresión→sensibilidad→evidencia→push→REMOTE_SHA).

### D · Rehearsal (G3) — **pendiente**
- [ ] R1 sintético PASS (10/10 pasos) + acta de ensayo.
- [ ] R2 sanitizado PASS (si autorizado).
- [ ] Restore drill con RTO medido ≤ objetivo.
- [ ] 0 incidentes BLOQ abiertos.

### E · Infra/Operaciones (G3) — **pendiente**
- [ ] Instancia productiva lista (según GL-OD-01/02); imágenes fijadas por digest.
- [ ] Observabilidad y alertas activas; correo resuelto o alcance declarado; secretos rotados; SSL/DNS productivos.
- [ ] Backup inicial off-site + procedimiento de rollback y contingencia manual aprobados.
- [ ] Usuarios/roles/BUs reales cargados y probados (incl. admins); responsables funcional y técnico designados.

### F · Cutover real planificado — **pendiente**
- [ ] Fuentes reales transformadas (plantillas por BU) con responsable por dominio.
- [ ] Ventana de freeze acordada; fecha/hora de corte por empresa/BU.
- [ ] Acta de cutover preparada (firmas previstas).

## 3 · Criterios de bloqueo automático

Cualquiera de estos ⇒ **no convocar** el gate: paso del rehearsal en FAIL · gap `BLOQ` sin cerrar o sin observación aceptada · decisión GL-OD pendiente que afecte al alcance · regresión del baseline `fef7289` sin cadena completa · intento de usar SAP real o datos ficticios en el runtime real.

## 4 · Plantilla de decisión (a completar por el Owner)

| Campo | Valor |
|---|---|
| Fecha | |
| Revisó | Owner (nombre) |
| Resultado | `GO_LIVE_READY` / `GO_LIVE_READY_WITH_OBSERVATIONS` / `NO_GO_LIVE` |
| Observaciones aceptadas | |
| Condiciones / plazos | |
| Próxima revisión | |

> Registro del resultado: se anexa a este documento como sección «Decisión registrada» citando el texto exacto del Owner (sin parafrasear), y se refleja en el roadmap G4.
