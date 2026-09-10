# RUNTIME SCREENSHOT INDEX

**2026-09-10** · runtime `avicola.globaldv.net` · capturas en `evidence/`.

| ID | Archivo | Timestamp (UTC) | URL | Actor | Empresa | BU | Capacidad | Esperado | Real | Status | Finding |
|---|---|---|---|---|---|---|---|---|---|---|---|
| AUDIT_001 | `evidence/AUDIT_001_DEPLOYED_LOGIN.png` | 2026-09-10 21:07 | `/login` (redirigido desde `/`) | anónimo | — | — | CAP-SES-01 | superficie de login del despliegue | renderiza correctamente (es/en, campos, mostrar contraseña) | `BLOCKED_AUTH` (sin credenciales no hay más) | — |

## Capturas no realizadas (con causa)

| Prevista (§65) | Causa |
|---|---|
| Post-login dashboard, navegación, contexto de empresa | `AUTHENTICATED_RUNTIME_BLOCKER` — no hay cuentas autorizadas del shared |
| Administración de empresa / BU / usuarios / roles | ídem + pantallas inexistentes (fase 9) |
| Entradas de las 4 unidades, revisión, corrección, importación | ídem |
| Estados de ruta directa inaccesible | realizado como **sonda de URL** (todas → `/login` sin sesión), no como captura separada — la URL resultante queda registrada en `EVIDENCE §9` |
| Evidencia de versión del runtime | capturada como **headers + hash** (`BUNDLE_HASHES.txt`), más preciso que una foto |

## Artefactos de evidencia sin imagen

| Archivo | Contenido |
|---|---|
| `evidence/BUNDLE_HASHES.txt` | SHA-256 del bundle desplegado, del bundle local y del `index.html` servido |

## Regla

Ninguna captura contiene tokens, contraseñas ni datos personales. Todas las filas tienen contexto; no hay imágenes huérfanas.
