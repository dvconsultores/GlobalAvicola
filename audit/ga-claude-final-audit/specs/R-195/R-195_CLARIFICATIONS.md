# R-195 · CLARIFICACIONES

Fecha: 2026-09-13 · HEAD `c0b4afc` · Resolver antes de C2.

| # | Pregunta | Supuesto por defecto | Fuente | Decisión |
|---|---|---|---|---|
| C-01 | ¿`username` editable? | No (inmutable; `UserUpdate` no lo admite). Se muestra como solo lectura. | `auth/schemas.py:65-85` | técnica |
| C-02 | ¿Se eliminan los `alert/confirm/prompt` del flujo usuarios? | Sí: `ConfirmDialog`/toast existentes (patrón del resto de la app); si algún diálogo queda fuera de alcance inmediato, se documenta. | C#31 (informe C) | técnica |
| C-03 | Selector de empresa en alta/edición | Para actores acotados: oculto (R-118 resuelve); para autoridad global sin contexto: se mantiene solo si el flujo lo soporta (hoy no necesario) — evaluar en C2 y documentar. | R-118; `UsersPage.tsx` | técnica |
| C-04 | `last_name` obligatorio en cliente | Sí (min 1) en alta y edición. | B-28 | técnica |
| C-05 | ¿Reset de contraseña? | Fuera (R-202); el botón existente se mantiene tal cual hasta que su paquete decida. | registro G-13 | técnica |

Sin decisiones abiertas que bloqueen.
