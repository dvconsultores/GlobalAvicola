# CUTOVER-INITIAL-BALANCES · 15_RUNTIME_VERIFICATION

Fecha: 2026-10-15 · SPEC 006 · Runtime compartido UAT `https://avicola.globaldv.net` (despliegue por workflows `docker-push-*` + Watchtower tras el push a `origin/main`, AOD-29; ningún workflow modificado)

---

## 1 · Push y verificación remota

```text
PUSH              = git push git@github.com:dvconsultores/GlobalAvicola.git main:main  (57a421a..d1770ea)
LOCAL_SHA         = d1770ead73c3785a25ad365196b91104828b205c  (CERTIFICATION_SHA)
REMOTE_SHA        = d1770ead73c3785a25ad365196b91104828b205c  (git ls-remote refs/heads/main)
REMOTE_SHA_MATCH  = PASS
DESPLIEGUE        = workflows + Watchtower sin intervención; el runtime sirvió el código nuevo a las 19:02:53 (≈6 min tras el push)
```

## 2 · Procedencia del runtime tras el despliegue

Sondas sin credenciales (solo prueban que el runtime sirve el código nuevo):

| Sonda | HEAD anterior (`57a421a`) | Esperado con SPEC 006 |
|---|---|---|
| `GET /api/v1/cutover-batches` | **405** observado antes del despliegue | **401** observado tras el despliegue |
| `GET /api/v1/cutover-batches/1/preview` | **404** observado antes | **401** observado |
| `GET /api/v1/cutover-batches/1/errors?format=csv` | 404 | **401** observado |
| `GET /api/v1/cutover-templates/breeder?format=csv` | 401 | 401 |
| bundle del frontend (`/assets/index-J7WerKPh.js`, antes `index-BibpyGLa.js`) contiene `cutover-file-input` y `_v2.` | no | **sí** |
| `/locales/es/translation.json` trae `cutover.downloadTemplateCsv`, `cutover.steps` y «Crear carga» | no | **sí** |

Con el operador UAT disponible (sin `cutover:*`): `login` 200; `GET /cutover-batches`, `GET /cutover-templates/grandparent?format=csv` y `GET /cutover-batches/1/preview` ⇒ **403** (RBAC intacto, rutas nuevas protegidas). Log: `evidence/e2e/runtime_probe_uat.log` (solo códigos HTTP; sin credenciales ni tokens).

## 3 · Verificación funcional (descarga + carga por BU)

Requiere un usuario UAT con `cutover:{create,validate,submit,read}` y un aprobador distinto con `cutover:approve`; las credenciales UAT disponibles para esta ejecución (`~/ga_uat09_credentials.txt`: operador/aprobador de reproductoras) **no** tienen permisos `cutover:*` y no existe usuario administrador UAT en el entorno del agente. El ciclo completo por BU queda, por tanto, certificado localmente (E2E 4/4 por UI sobre la pila local con el mismo código) y pendiente en el runtime compartido.

```text
RUNTIME_DEPLOYMENT_VERIFIED   = PASS (código de SPEC 006 servido por backend y frontend del runtime compartido)
RUNTIME_FUNCTIONAL_CYCLE      = BLOCKED_EXTERNAL (falta usuario UAT con cutover:* y aprobador distinto)
```

## 4 · Resultado

```text
RUNTIME_VERIFICATION = BLOCKED_EXTERNAL
  · despliegue y procedencia del código: PASS (sondas §2)
  · ciclo descarga → carga → aprobación → apply → primer evento por BU en UAT: PENDIENTE de credenciales
  · equivalente certificado localmente: E2E por UI 4/4 BU + 8 navegación sobre la pila local con el MISMO código (pre y post-mutación)
ÚNICA ACCIÓN NECESARIA = Owner: usuario UAT con cutover:{create,validate,submit,apply,read} + aprobador con cutover:approve; con ellos se ejecuta el ciclo (ideal: 4 ciclos, uno por BU) y se actualiza este documento.
```
