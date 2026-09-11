# GA-FRONTEND · RECONCILIACIÓN DE RESIDUALES P3

Fecha: 2026-09-11 · Cierra la reconstrucción de RES-03, RES-04, RES-07, RES-09, RES-10 (§25). Nada se implementa.

| RES | Objeto | Reconstrucción | ¿Defecto? | Clase | Disposición |
|---|---|---|---|---|---|
| RES-03 | **AOD-25 / R-153** (lote automático de abuelas) | Ambigüedad contractual (disparador/código/población); ver `GA_AOD25_OWNER_DECISION_PACKET.md` | NO (requisito no definido) | **Gobernanza — decisión del propietario** | Paquete AOD-25 presentado (tras AOD-06). P3 confirmado («lista Wave B») |
| RES-04 | **CAP-OPS-09 / FVA-28** (pantalla de reverso) | Diferral explícito del programa («frontend → fase 9»); backend interno certificado (GA-REM-041/OD-19); 0 refs en frontend | NO (excluido por diseño) | **OUT_OF_CURRENT_PRODUCT_SCOPE** | Agrupar con CAP-ADM-05 en un **paquete de decisión de diseño fase-9 restante** (autorización de diseño → SPEC/AC/UI) cuando el programa lo abra |
| RES-07 | **Higiene de certificación (19 filas)** | Mapeo exacto: RES-07 = **las 19 filas VNC** de `GA_FRONTEND_RESIDUAL_19_CERTIFICATION_MATRIX.md` (no son avisos de consola, ni copys, ni naming). Overlap = 19/19, sin elementos externos | NO (no hay defecto; falta paquete certificatorio por AC) | **Higiene de certificación** | Gobernado por el plan de batches (S/CP/M/Q/E/R + OPS×3 + UAT-1 agrupada). No bloquea cierre una vez ejecutado y aprobado el plan |
| RES-09 | **AOD-24 / R-177** (tipo de huevo vs ovoscopía) | Ver `GA_AOD24_SCOPE_NOTE.md` | NO (contrato indefinido) | **Gobernanza P3 — Wave B** | Se presenta en la reconciliación de Wave B (o paquete conjunto con AOD-25 si el propietario lo prefiere). No bloquea frontend ni readiness |
| RES-10 | **Notas de consistencia de rutas/acciones** | (a) `/kpi` sin guarda de capacidad → el dato queda acotado por API (fail-closed por datos; home N-1 ya documentada); (b) `/my-pending` solo-sesión → datos propios scoped por backend; (c) exports de reportes sin `can()` → lectura derivada del permiso de la ruta, sin evidencia de fuga; (d) `PermissionRoute` con un solo uso → consistencia interna | NO probado ninguno | **Notas P3 (documentación)** | Quedan documentadas; sin finding. Si un futuro cambio de contrato las convierte en funcionales, reabrir por evidencia |

**Ningún P3 es bloqueante de cierre** (no funcionales o gobernanza ya encaminada). Los tres con decisión del propietario (AOD-25, AOD-24, y AOD-06/P1) tienen paquete o nota; el resto es certificación (RES-07) o documentación (RES-10).
