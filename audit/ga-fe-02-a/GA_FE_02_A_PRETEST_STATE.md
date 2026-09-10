# GA-FE-02-A · PRETEST STATE (§20)

**Resultado**: snapshot funcional **NO capturado** — la ejecución entró en `MODE_C ·
BLOCKED_AUTH` antes de poder autenticarse (§29/§79 del encargo). No se inventó ningún dato.

## Lo que SÍ quedó registrado (estado del sistema, no del producto)

```
FECHA/HORA          2026-09-10T23:52:28Z – 23:53:23Z
REPO                main · HEAD d120fdd == remoto · worktree limpio
RUNTIME             200 OK · assets/index-C_aR7TJ6.js · sha256 35ea38e2… · LM 23:39:07 GMT
                    ETag "6aa33f9b-322" — generación GA-FE-02 (verificada byte a byte)
GATES               tsc 0 · npm run build exit 0 · Vitest 198/198
SESIÓN              navegador compartido en /login (NO autenticada) — sin cookies de sesión
CREDENCIALES        0 suministradas por mecanismo autorizado (verificación acotada)
MFA / EMAIL CONF    no aplican (no existen en el producto)
```

## Lo que NO se pudo capturar (y por qué)

```
Company de prueba (ID/nombre) .............. requiere sesión
Estado de Company BU (4 unidades) .......... requiere sesión
Usuarios de prueba y sus concesiones ....... requiere sesión
Concesiones efectivas ...................... requiere sesión
Roles/permisos observados .................. requiere sesión
Empresa seleccionada / sesión .............. requiere sesión
Línea base de auditoría .................... requiere sesión
```

## Al reanudar (con cuentas autorizadas)

1. Autenticar al actor bootstrap y verificar identidad + permisos (§80).
2. Elegir/verificar la empresa de prueba segura (§18) y capturar aquí el snapshot completo
   (Company, estados BU, usuarios, concesiones almacenadas/efectivas, roles, permisos,
   contexto de sesión, línea base de auditoría) **antes de cualquier mutación**.
3. Crear el ledger de datos (`GA_FE_02_A_TEST_DATA_LEDGER.md`) con lo observado.

Sin secretos en este documento.
