# CUTOVER-INITIAL-BALANCES · 15_RUNTIME_VERIFICATION

Fecha: 2026-10-15 · SPEC 006 · Runtime compartido UAT `https://avicola.globaldv.net` (despliegue por workflows `docker-push-*` + Watchtower tras el push a `origin/main`, AOD-29; ningún workflow modificado)

---

## 1 · Push y verificación remota

```text
PENDIENTE: se completa tras el push del commit de certificación (ver §4).
```

## 2 · Procedencia del runtime tras el despliegue

Sondas sin credenciales (solo prueban que el runtime sirve el código nuevo):

| Sonda | HEAD anterior (`57a421a`) | Esperado con SPEC 006 |
|---|---|---|
| `GET /api/v1/cutover-batches` | 405 (solo existía POST) | 401 (ruta GET nueva protegida) |
| `GET /api/v1/cutover-batches/1/preview` | 404/405 | 401 |
| `GET /api/v1/cutover-templates/breeder?format=csv` | 401 | 401 (sin cambio observable sin sesión) |
| bundle del frontend contiene «Descargar plantilla CSV» / `cutover-file-input` | no | sí |

## 3 · Verificación funcional (descarga + carga por BU)

Requiere un usuario UAT con `cutover:{create,validate,submit,read}` y un aprobador distinto con `cutover:approve`; las credenciales UAT disponibles para esta ejecución (`~/ga_uat09_credentials.txt`: operador/aprobador de reproductoras) **no** tienen permisos `cutover:*` y no existe usuario administrador UAT en el entorno del agente. El ciclo completo por BU queda, por tanto, certificado localmente (E2E 4/4 por UI sobre la pila local con el mismo código) y pendiente en el runtime compartido.

```text
RUNTIME_VERIFICATION = PENDIENTE (ver §4)
```

## 4 · Resultado

PENDIENTE_DE_RELLENAR
