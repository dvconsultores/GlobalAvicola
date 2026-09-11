# GA-BU-D10 · CLARIFICACIONES (post-decisión)

| # | Cuestión | Resolución | Fuente |
|---|---|---|---|
| C01 | Semántica exacta de «termina» | Marcar `revoked_at` de las concesiones **vivas** de esa habilitación al apagar; historia completa | OD-23 §2.1; SPEC §5 |
| C02 | ¿Borrar o marcar? | **Marcar**; nunca borrar; sin cascadas | OD-23 §5; modelo (OD-09.e) |
| C03 | ¿Qué se audita al terminar? | `PERMISSION_CHANGE` por concesión (granted→revoked, `cause=company_business_unit_disabled`) + `CONFIG_CHANGE` del toggle (como hoy) | SPEC §12 |
| C04 | ¿El re-encendido toca concesiones? | NO (solo `is_enabled` + auditoría) | SPEC §6 |
| C05 | ¿Dónde se implementa? | `admin.fijar_habilitacion` (punto único del toggle); resolutor/proyecciones intactos | SPEC §5 |
| C06 | ¿Migración? | NO; prospectivo desde la política; sin retro-clasificación | SPEC §14 |
| C07 | Idempotencia del apagado | Config idempotente; además **normaliza** (marca vivas residuales de estados OFF previos), sin duplicar eventos | SPEC §5.5 |
| C08 | ¿Y las concesiones revocadas manualmente antes? | Ya históricas; el apagado no las toca; sin eventos extra | SPEC §5.4 |
| C09 | ¿Puede concederse con la unidad apagada? | NO (regla vigente: conceder no habilita) — la re-autorización ocurre tras encender | traza GRANT §1; SPEC §7 |
| C10 | ¿Sesiones/token? | Relectura por petición; sin claims de BU; refresh/relogin no cambian semántica | SPEC §8 |
| C11 | Frontend | 0 cambios: navegación/estado derivan de `/me` efectivo | SPEC §9 |
| C12 | Access Admin | Control-plane puro; re-concede vía candidatos; self-grant DENY | SPEC §10 |
| C13 | Actor global | No evade OD-16; sin concesión no opera | SPEC §10 |
| C14 | Transferencia de empresa | Intacta (OD-09.e) — regresión obligatoria, sin cambios | SPEC §14; L11/L12 |
| C15 | Población/entorno | Prospectivo; 2 concesiones vivas sobre unidad OFF en prueba se normalizan en el siguiente apagado | SPEC §14 |
| C16 | ¿Nueva UI? | Ninguna; sin nuevos mensajes (por eso ES/EN: N/A) | SPEC §9/§2 |
| C17 | UAT del propietario | **REQUIRED** (comportamiento visible cambia) | SPEC §17 |
| C18 | Severidad del finding | P2 (política de acceso productivo; sin pérdida de datos ni fuga) | R-188 |
| C19 | Estado final esperado | R-188 CLOSED · OD-23 RATIFIED_IMPLEMENTED · owner acceptance PENDING | §71 del encargo |
| C20 | Criterio de cierre | AC01-AC25 + E2E + limpieza + evidencia + local==remoto | SPEC §15/§16 |
