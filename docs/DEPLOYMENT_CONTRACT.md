# Contrato de despliegue (main / develop)

Este documento fija qué imagen produce cada rama, quién la consume y cómo se
certifica que lo que corre es exactamente el código certificado.

## 1. Rama → workflow → imagen → consumidor

| Rama | Workflow | Imagen y tags (Docker Hub) | Quién la consume |
|------|----------|----------------------------|------------------|
| `main` | `.github/workflows/docker-push-backend.yml` y `docker-push-frontend.yml` | `dvconsultores/globalavicola-backend` y `...-frontend`: `latest` + `sha-<7>` | Producción: `docker-compose.yml` (`:latest`) + Watchtower |
| `develop` | `.github/workflows/docker-push-backend-dev.yml` y `docker-push-frontend-dev.yml` | las mismas imágenes: `dev` + `sha-<7>` | UAT: `docker-compose.yml` + `docker-compose.develop.yml` (`:dev`) |

`sha-<7>` es el prefijo de 7 caracteres del commit que construyó la imagen.
El `telegram-bot` no tiene imagen propia: usa la del backend (`:dev` en UAT).

**`develop` NO es un tag.** El único tag de la rama `develop` es `dev`.
Pedir `:develop` en un compose falla con `manifest unknown`.

## 2. Regla de construcción

Cada push construye, sin filtro de rutas, para que el SHA de la rama sea el SHA
del runtime. Un filtro `paths:` en `on.push` deja commits sin imagen y rompe la
procedencia; por eso los cuatro workflows no lo tienen. `workflow_dispatch`
sigue disponible, pero no sustituye al build por push.

## 3. Procedencia: la evidencia es el SHA

Ambos artefactos se declaran a sí mismos:

- Backend: `GET /api/v1/version` → `{"git_sha", "build_time", "environment"}`.
- Frontend: `GET /version.json` → `{"git_sha", "build_time"}`.

El SHA viaja como `build-arg GIT_SHA` (= `github.sha`) y se publica como etiqueta
OCI `org.opencontainers.image.revision`.

## 4. Criterio de certificación

Un despliegue se certifica cuando **el SHA del runtime es igual al SHA
certificado**. El tag (`latest` / `dev`) es solo el mecanismo de distribución; el
SHA es la evidencia. Un tag que apunta a otro commit no certifica nada.

Verificación (desde la raíz del repo):

```bash
scripts/verify_runtime_sha.sh <base_url> <sha>
# PASS  -> DEPLOYMENT_PARITY=PASS (exit 0)
# FAIL  -> DEPLOYMENT_PARITY=FAIL (unknown exit 2 · resto exit 1)
```

## 5. Digest del contenedor en ejecución

El digest de la imagen que está corriendo **no es accesible desde fuera del
servidor** (`OCI_RUNTIME_LABEL = NOT_ACCESSIBLE`: no hay endpoint que lo
exponga y no se abre uno). Se verifica contra el registro: el digest del tag
`dev` debe ser el de la imagen construida desde `sha-<HEAD>`, y el del tag
`latest` el de `sha-<HEAD>` de `main`.

```bash
docker buildx imagetools inspect dvconsultores/globalavicola-backend:dev
docker buildx imagetools inspect dvconsultores/globalavicola-backend:sha-<7>
```

## 6. Qué no cubre este documento

No hay secretos, tokens ni credenciales aquí: solo nombres de imagen y tags
públicos. La topología de ramas y el procedimiento de convergencia se tratan en
la auditoría `audit/ga-main-develop-uat-convergence/`.
