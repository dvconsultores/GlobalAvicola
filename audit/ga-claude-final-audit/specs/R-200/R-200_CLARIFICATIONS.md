# R-200 · CLARIFICACIONES

Fecha: 2026-09-13 · Ninguna requiere decisión del propietario; todas resueltas por defecto.

| # | Pregunta | Resolución / valor por defecto | Fuente | Estado |
|---|---|---|---|---|
| C-01 | ¿Qué valores de `type` acepta la autenticación? | Exactamente `"access"`. Ausente, `"refresh"` o cualquier otro → `401`. No hay tokens legítimos sin `type` (`security.py:44,55`). | `security.py:34-56` | RESUELTA |
| C-02 | ¿Dónde vive la comprobación: `get_current_user` o `decode_token`? | Por defecto en `get_current_user`, inmediatamente después de `decode_token` y **antes** de leer `sub` (mínimo diff, sin tocar la firma de `decode_token`). Alternativa equivalente: `decode_token(token, tipo_esperado=...)` reutilizada por `refresh_token`. Cualquiera de las dos satisface AC01…AC08. | `GAP-03` | RESUELTA |
| C-03 | ¿Se audita o se registra el intento? | No se audita en `P-09` (es un `401`, como los tokens inválidos; `R-83`: sin empresa fiable no hay asiento). Se emite `logger.warning("token de tipo %r rechazado como acceso", tipo)` sin el token ni el `sub`. | `R-83` · informe D §D.1 | RESUELTA |
| C-04 | ¿Se reduce la vida del refresh o se cambia su almacenamiento? | No en esta spec. 7 días (`config.py:49`) y `sessionStorage`/`localStorage` (`auth.store.ts:60-69`) son decisiones de `GA-REM-003`; se anota en el registro que la ventana de un refresh robado sigue siendo 7 días **para renovar** hasta que `GA-REM-003 AC04` se implemente. | `GA-REM-003` | RESUELTA (fuera de alcance, referenciada) |
| C-05 | ¿Puede romperse alguna prueba existente que fabrique tokens a mano? | Las pruebas usan `create_access_token(data=...)` (emite `type`), `create_refresh_token` para `/refresh`, o el login real. `test_r43_un_subject_no_numerico_se_rechaza_con_401` fabrica un access con `sub` no numérico vía `create_access_token` → sigue `401` (ahora por `type` correcto y `sub` inválido; el `detail` puede cambiar de orden — la prueba asierta sólo el código). Se verifica en C2. | `tests/test_security_regression.py:99-118` | RESUELTA |
| C-06 | ¿Debe el `401` distinguirse del de «token expirado» para el interceptor? | No: el interceptor renueva ante cualquier `401` no reintentado (`api.ts:55-66`) y hace logout si la renovación falla. Un `detail` distinto es informativo, no contractual. | `api.ts` | RESUELTA |
| C-07 | ¿UAT del propietario? | No: ningún flujo cambia. | §46 | RESUELTA |
