# GA-FE-06 · CHECKLIST DE EJECUCIÓN

- [x] Preflight verde y bundle de entrada congelado
- [x] Baselines (frontend 273/273 · tsc 0 · build · backend PG-libre 7/7)
- [x] Lecturas canónicas completas (modelo/esquema/servicio/SLA/form/i18n/migración/dedup)
- [x] Reconciliación R-182 (defecto = pérdida silenciosa en payload del alta)
- [x] Trazas (modelo, SLA) y matrices (alta, edición, SLA, actores, fixtures)
- [x] Especificación R182-AC01…52 + clarificaciones C01–C25
- [x] Plan P1–P37 · checklist · tareas
- [ ] RED vitest: PLD capturada→enviada; selector área desde `/masters/areas`; área→`area_id`
- [ ] RED runtime pre-fix con captura de payload real (evidencia)
- [ ] Commit C1 (gobernanza + RED)
- [ ] Implementación mínima (selector + payload + i18n `lots.area` + fila «Cierre previsto»)
- [ ] GREEN dirigido (nuevos verdes; controles: nulls, no-ID-crudo)
- [ ] Gates: tsc 0 · build · Vitest completo · backend PG-libre · (CI: suite canónica SLA)
- [ ] Commit C2 + push + despliegue observado
- [ ] Bundle nuevo congelado (hash/ETag/Last-Modified)
- [ ] E2E-01…16 autenticados (UI real como operador C; D/E para RBAC/CBU)
- [ ] Cross-company: selector filtrado + API deny + sin persistencia + sin fuga
- [x] SLA: fresh GET de PLD exactos · relectura de avisos al cierre (resultado real: PENDING_SCAN_WINDOW, dos intentos)
- [x] Fechas sin ±1 (día natural; valores de borde +3/+1/0/−1/+10)
- [x] Móvil 390×844 · desktop 1440×900 · ES/EN
- [x] Red: capturas sanitizadas sin tokens ni PII
- [x] Consola: 0 errores propios (ruido preexistente identificado: N-2/N-3)
- [x] Regresiones GA-FE-02/03/04/05
- [x] Higiene §101 completada y verificada (BUs 4 OFF · grants revocados · credenciales destruidas)
- [x] Evidencia: runtime, red, capturas, ledger, reconciliación R-182
- [x] Certificación GA-FE-06 + addendum auditoría + catálogo + paquete UAT
- [x] Commit C4 + local==remoto · worktree limpio · informe final · STOP

## GA-FE-06-A · seguridad de área ajena (remediación R-182)

- [x] Preflight + lecturas canónicas + dedup R-183 (ABSORBED_IN_R182)
- [x] Corrección de estado (R-182 SECURITY_REMEDIATION_REQUIRED · GA-FE-06 PARTIAL · OWNER_UAT_READY NO)
- [x] Enmienda de spec (SEC-AC01…08) + checklist + tareas
- [x] RED: suite PG escrita + captura runtime pre-fix (201 alta / 200 edición / 500 inexistente)
- [ ] C5 gobernanza + push
- [ ] Implementación validador canónico (`verificar_catalogo_de_empresa`) en alta y edición
- [ ] GREEN local (gates) + C6 + despliegue + generación congelada
- [ ] E2E runtime: DENY alta · DENY edición · sin persistencia · sin auditoría de éxito · sin fuga · ALLOW misma-empresa · NULL · inexistente 400/BR-07
- [ ] Matriz tenant/BU/RBAC (incl. global con ventana OFF) + selector desktop/móvil + SLA datos/regla + regresiones GA-FE-02/03/04/05
- [ ] Higiene §101 + credenciales destruidas
- [ ] Recertificación R-182 completa + evidencias + addendum + C7 + informe §41 + STOP
