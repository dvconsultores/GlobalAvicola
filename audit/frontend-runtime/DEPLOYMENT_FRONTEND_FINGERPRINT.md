# DEPLOYMENT FRONTEND FINGERPRINT — LOCAL vs DESPLEGADO

**R-99** · medición del **2026-09-10 21:02 UTC** contra `https://avicola.globaldv.net` (ENV-01). Solo lectura.

---

## 1. Artefacto servido (runtime)

| Dato | Valor |
|---|---|
| `GET /` | `200 OK` · `Content-Length: 802` |
| `Last-Modified` | **`Sat, 05 Sep 2026 14:09:27 GMT`** (idéntico al medido el 2026-09-07) |
| `ETag` | `"6a9c2297-322"` |
| Bundle JS principal | **`/assets/index-D5dwMXuP.js`** (idéntico al medido el 2026-09-07) |
| CSS | `/assets/index-CTw07781.css` |
| Runtime chunk | `/assets/rolldown-runtime-QTnfLwEv.js` |
| Server | `openresty` · `X-Served-By: avicola.globaldv.net` |
| SHA-256 del bundle descargado | `4eb822a5…8c64be` (1 235 292 bytes; hashes completos en `evidence/BUNDLE_HASHES.txt`) |

Conclusión de artefacto: **el frontend servido está congelado desde el 2026-09-05 14:09:27 GMT** — cinco días y **15 entregas de frontend** después. La re-medición de hoy confirma que R-99 sigue activo en la fecha de esta auditoría.

## 2. Build local (HEAD `3808ed5`)

| Dato | Valor |
|---|---|
| Comando de producto | `npm run build` = `tsc -b && vite build` → **FALLA en `tsc -b` (6 errores, R-158)** |
| Bundle real (sin la puerta TS) | `npx vite build` → **PASS** → `/assets/index-Cl0MIg8E.js` |
| CSS local | `/assets/index-CgiG0VY8.css` |
| Runtime chunk local | `/assets/rolldown-runtime-QTnfLwEv.js` (**mismo hash que el desplegado** — misma familia de toolchain) |
| Árbol git tras build | limpio (`dist/` ignorado) |

`local index-Cl0MIg8E.js` ≠ `deployed index-D5dwMXuP.js` → **generaciones distintas demostradas**.

## 3. Causa raíz de la congelación (demostrada, no inferida)

Cadena de evidencia:

1. `frontend/Dockerfile` → `RUN npm run build`; `package.json` → `"build": "tsc -b && vite build"`.
2. El artefacto servido se construyó el **2026-09-05 16:09:27 +0200** — un minuto después del commit **`f46cb13`** ("fix(proxy)", 16:08:25), único commit de `frontend/**` en esa ventana (publica `nginx.conf`).
3. **Verificación en worktree temporal del commit `f46cb13`**: `npx tsc -b --noEmit` → **exit 0 (GREEN)** → el build del artefacto era posible.
4. **Primer commit de frontend posterior**: `4386f87` (2026-09-06 03:36, "fix(audit)") retiró las pestañas «por lote / por usuario» de `AuditPage.tsx` **dejando los imports `User, Database` sin uso** → 2 × `TS6133` con `noUnusedLocals: true` → `tsc -b` **RED**.
5. `950bb21` (2026-09-07, áreas) añadió 4 errores más en `LotFormPage.tsx` (`areas`, `setAreas`, `areaRes`, índice de tupla) → **6 errores**.
6. **Los 15 commits de frontend posteriores al congelamiento fueron verificados uno a uno**: `tsc -b` **RED en todos** (2 errores desde `4386f87`; 6 desde `950bb21`).
7. ⇒ Cada build de la imagen de frontend en CI falla en `RUN npm run build` → no hay push de imagen → Watchtower no recibe nada nuevo → **el artefacto servido no cambia**.

```
LÍNEA:  artefacto 09-05 (build GREEN) → 4386f87 rompe tsc → toda entrega posterior RED → frontend congelado
NO ES:  caché del cliente · PWA · Watchtower (el backend sí se despliega en cada entrega) · tsc "preexistente" del build (los 6 errores SON el bloqueo)
```

Nota de precisión: el síntoma de R-99 («frontend no sigue a main») queda **acotado a un mecanismo reproducible localmente** — la puerta `tsc` rota (R-158) sobre el paso `npm run build` del Dockerfile. Los registros de ejecución del workflow no son accesibles desde esta estación (`gh` no disponible); la cadena anterior no depende de ellos: es reproducible con los mismos comandos del pipeline.

## 4. Comparación por marcadores (evidencia por capacidad)

Marcadores = literales de cadena que sobreviven a la minificación (rutas de API, claves de campos, claves i18n).

| Marcador | Deployed (`index-D5dwMXuP.js`) | Local (`index-Cl0MIg8E.js`) | Lectura |
|---|:--:|:--:|---|
| `/weight-curves` | **0** | **6** | curvas de peso: local sí, runtime no |
| `/notifications` | **0** | **3** | notificaciones: local sí, runtime no |
| `/roles` (ruta de página) | **1** (solo `GET /roles` de UsersPage) | **7** (ruta + catálogo + PUT/POST) | página de roles ausente del runtime |
| `import_plan` | **0** | **1** | plan de abuelas: local sí, runtime no |
| `chicks_healthy` | **0** | **1** | B13: local sí, runtime no |
| `dead_on_arrival` | **0** | **1** | B01: local sí, runtime no |
| `/masters` | 30 | 39 | 7 maestros + ediciones no desplegados |
| `/poultry` | 30 | 30 | hub de las 4 unidades presente en ambos |
| `/business-units` | **0** | **0** | **nunca existió en el frontend (fase 9)** |
| `/grant-candidates` | **0** | **0** | ídem |
| `/submit` | **0** | **0** | el envío a revisión no tiene control UI en ninguna generación |
| `/switch-company` | 1 | 1 | selector de empresa presente en ambos (jun-2026) |

## 5. Backend desplegado vs frontend desplegado (§93 del encargo)

Sondas sin autenticar (401/405 = ruta existe en el código desplegado; 404 = no existe):

| Ruta | Código | Generación |
|---|:--:|---|
| `GET /api/v1/business-units` | **401** | fase 7 (2026-09-08) |
| `GET /api/v1/users/{id}/business-units` (POST) | **401** | fase 7 |
| `GET /api/v1/operations/pending-classification` | **401** | fase 6 |
| `GET /api/v1/reversals` | **401** | tranche 5 (2026-09-09) |
| `GET /api/v1/notifications/unread-count` | **401** | 2026-09-07 |
| `GET /api/v1/operations/alerts` | **401** | — |
| `GET /api/v1/masters/weight-curves` | **405** | existe (otro método) |
| `GET /api/v1/switch-company` | **405** | existe (POST) |

```
DEPLOYED BACKEND  = NUEVO (incluye tranches 1–14)
DEPLOYED FRONTEND = GENERACIÓN 2026-09-05
```

## 6. ¿Por qué no es un problema de caché? (§92)

- El `Last-Modified` y el hash del asset los sirve **el origen** (openresty) — un cliente con caché lo único que haría es reusar el mismo artefacto que el origen ya sirve.
- La medición del 2026-09-07 y la de hoy (09-10) coinciden byte a byte (`index-D5dwMXuP.js`): **el origen no ha cambiado**.
- Un navegador limpio seguiría recibiendo el mismo `index.html`. Caché del cliente descartada como causa; no se probó hard-reload diferenciado porque el origen es concluyente.

## 7. Clasificación

```
R-99 = DEPLOYMENT_STALE  (demostrado; cinco condiciones de §113 del encargo satisfechas)
  A. capacidad requerida ....................... sí (15 entregas)
  B. frontend repo lo implementa ............... sí (comprobado por archivo)
  C. build local lo contiene ................... sí (vite build OK; marcadores presentes)
  D. runtime sirve versión anterior ............ sí (fingerprint + marcadores ausentes)
  E. no es rol/empresa/unidad .................. n/a (la diferencia es de artefacto, no de sesión)
  F. no es caché del cliente ................... sí (§6)
CAUSA RAÍZ = tsc -b rojo desde 4386f87 (R-158) × Dockerfile con npm run build
```
