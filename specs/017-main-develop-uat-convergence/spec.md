# SPEC 017 — Convergencia exacta main / develop / UAT (cierre de O-10 y contrato de imagen)

Mandato: `GA-MAIN-DEVELOP-UAT-EXACT-CONVERGENCE` (2026-11-19). Continúa SPEC 016.
Baseline: `origin/main` = `0363200`, `origin/develop` = `424dda0`, runtime backend/frontend = `424dda0`.
Sin migración (head `g2b3c4d5e6f7`). Fuera de alcance: O-3 (solo regresión), Reproductoras/Cría, Cargas Iniciales, SAP, Usuarios/Roles, O-11 (solo triage).

Decisión Owner: **sin excepciones de SHA** entre la línea certificada y UAT. Meta:

```
origin/main == origin/develop == backend runtime SHA == frontend runtime SHA
```

## A. Topología Git

- `0363200` (main) y `424dda0` (develop) divergen desde `39d8238`: ni `main→develop` ni `develop→main` son fast-forward.
- Sin reescribir historia: **merge de `develop` en `main`** (`fa427c8`, develop pasa a ser ancestro de main); la corrección de O-10 y la certificación quedan en `main`;
  después **`develop` avanza por fast-forward** al SHA final certificado de `main` (sin merge adicional en `develop`).
- El delta de contenido que `develop` trae sobre el ancestro común son dos archivos de Andrés (`7610ece`): `backend/scripts/bootstrap_first_superuser.py` y `create-pr.sh`.

## B. O-10 — contrato y causa raíz

Contrato (GA-REM-043, AC04/AC05, T-043-02): repetir el bootstrap tras el éxito es idempotente (no duplica, no modifica, no rota la contraseña);
si `admin` o su correo existen en estado incompatible, falla sin sobrescribir; nunca se degrada una cuenta existente.

`test_t_043_02` falla con `BootstrapError: El correo reservado … ya pertenece a otro usuario` porque tras `7610ece` el rechazo por correo
también se dispara cuando el correo reservado es el del **propio `admin` canónico**. Clasificación: **PRODUCT_DEFECT** (el test es correcto y coincide con el AC).

Fix mínimo: el rechazo por correo solo aplica si el correo pertenece a **otra** cuenta (`existing_username is None` o `existing_email.id != existing_username.id`).
Tests nuevos T-043-07..12 (repeticiones sin escritura, usuario normal intacto, correo reservado de un tercero, `admin` con rol no global,
contraseña débil sin residuos, admin inactivo nunca reactivado/degradado). No se tocan `validate_password`, la reconciliación de permisos faltantes ni el CLI.

Observación (O-12, sin tocar): `create-pr.sh` de `7610ece` sustituye un script con comprobaciones y confirmación explícita por otro que crea y **fusiona automáticamente** `develop→main`
sin confirmar ni verificar checks. No interviene en producto ni en CI; se documenta como riesgo de gobernanza para decisión del Owner.

## C. Contrato de imágenes (hallazgo de infraestructura)

Evidencia (Docker Hub, `tags` públicos): ambos repositorios publican `latest`, `dev` y `sha-<corto>`; **no existe el tag `develop`**.
`latest` apuntaba a `39d8238`; `dev` a `424dda0` y UAT declaró `424dda0` ⇒ el servidor UAT consume **`:dev`**. `docker-compose.develop.yml` del repo
pedía `:develop` (inexistente) ⇒ contradicción repo↔infraestructura.

- **D-C1 Convención única:** `main → latest` (+ `sha-<corto>`); `develop → dev` (+ `sha-<corto>`). Es la convención que la infraestructura ya consume; cambiar a `develop` rompería UAT
  y exigiría tocar el servidor, fuera del repositorio.
- **D-C2** `docker-compose.develop.yml` pasa a `:dev` (backend, frontend y telegram-bot).
- **D-C3 Cada push construye.** Los cuatro workflows pierden el filtro `paths`: una imagen solo declara el SHA del commit que la construyó, de modo que un commit de documentación
  (p. ej. el de certificación) dejaba al runtime en un SHA anterior (`tree-equal`). Sin filtro, `SHA(HEAD de la rama) == SHA(runtime)` se cumple siempre que el pipeline termina.
- **D-C4** El SHA, no el tag, es la autoridad: `scripts/verify_runtime_sha.sh` sigue siendo el criterio. El digest del contenedor en ejecución no es accesible desde fuera del servidor
  (`OCI_RUNTIME_LABEL = NOT_ACCESSIBLE`); se evidencia el digest del tag `dev` en el registro y su igualdad con `sha-<HEAD>`.

### ACs

| AC | Enunciado |
|---|---|
| AC-C-01 | Los 4 workflows no declaran `paths` en `push`; mantienen `workflow_dispatch`, `build-args` y la guardia de SHA. |
| AC-C-02 | `develop` publica `dev` + `sha`; `main` publica `latest` + `sha`; ningún workflow publica `develop` ni `dev` desde `main`. |
| AC-C-03 | `docker-compose.develop.yml` solo referencia `:dev` (ningún `:develop`). |
| AC-C-04 | Documento del contrato de despliegue (`docs/DEPLOYMENT_CONTRACT.md`) coherente con workflows y compose. |
| AC-O10-01..06 | T-043-02 y T-043-07..12 en verde; el script no contiene contraseña literal ni imprime secretos. |

## D. Gate final

`MAIN_SHA == DEVELOP_SHA == BACKEND_RUNTIME_SHA == FRONTEND_RUNTIME_SHA` (verificado con `scripts/verify_runtime_sha.sh`, PASS sin `tree-equal`).
