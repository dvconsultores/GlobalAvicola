# GA · T11 CERTIFICATION — Residuales FE (R-213 · R-212 · R-218 · R-220)

Fecha: 2026-09-14 · Programa: GA PRE-SAP · Política: **AOD-29 Clarification 01**
(certificación **local** con gates reproducibles; **GitHub Actions retirado**;
**push requerido** a `origin/main` con verificación de SHA remoto).

## 1 · Paquetes y commits

| Paquete | Contenido | Certificación | Cierre (cert · evidencia) |
|---|---|---|---|
| **R-213** | `/me` y navegación: autoridad de acción + pulido de sesión | `specs/R-213/R-213_CERTIFICATION.md` | `c32d873` |
| **R-212** | Conciencia de permisos en pantallas (gates de acción) | `specs/R-212/R-212_CERTIFICATION.md` | `a7a9087` |
| **R-218** | Serie semanal del lote (`/reports/lot/{id}/weekly`) | `specs/R-218/R-218_CERTIFICATION.md` | `356de95` |
| **R-220** | Residuales P3 (contrato/UX/móvil/i18n/rutas; lotes A+extra/B/C/D) | `specs/R-220/R-220_CERTIFICATION.md` | IMPL final `da31f52` · evidencia `3c3ab3d` |

`HEAD` remoto tras el cierre de R-220: **`3c3ab3d`** · `REMOTE_SHA_MATCH = PASS`
(cada push verificado con `git ls-remote`; fast-forward, sin force).

## 2 · Gates de la tranche (PASS)

| Gate | Resultado |
|---|---|
| Suites BE completas (R-213 · R-218 · R-220 final) | 1381/0/49 · 1384/0/49 · **1389/0/49** (19:51; tras alineación `8604a60`) |
| Guardián de rutas `/api/` | 213 → **214** (R-218 añadió `/reports/lot/{id}/weekly`; R-220 sin cambios) |
| Suites FE completas (por paquete → final) | 448/448 · 450/450 · 472→…→**520/520** |
| `npm run build` (`tsc -b && vite build`) | **EXIT 0** en cada paquete |
| Sensibilidad por paquete | S1-S2 (R-213) · M1-M5 (R-212) · B1-B3/N1-N3 (R-218) · A/B/C/D por lote (R-220) — RED quirúrgica 1:1 y restore desde SHA de implementación |

## 3 · Paquetes y lotes de R-220

R-220 se ejecutó **itemizado por lotes** con gobernanza completa por lote
(A contrato/UX · A-extra nacimiento · B móvil/navegación · C i18n · D código muerto).
Detalle de commits, gates, sensibilidades y notas de honestidad (harness B9/B10, BR-21 en
A16, `locale` por parámetro en export): `specs/R-220/R-220_CERTIFICATION.md`.

La **regresión completa** capturó la deriva de 3 tests de conteo del catálogo de tipos de
evento (25→26 por `water_consumption`, A14/B-24), alineados en `8604a60`; la suite BE se
re-ejecutó completa tras la alineación (ver §2).

## 4 · Política y estado

- `GITHUB_ACTIONS = NOT_APPLICABLE_BY_OWNER_DECISION`; `PUSH = REQUIRED_AFTER_LOCAL_CERTIFICATION`;
  `PUSH != DEPLOY`.
- Diferidos vivos (sin cambio): `R-142` (AOD-17, propietario `SCHEDULED`); gates AOD-17/AOD-18 en cola.
- **Siguiente**: **T14** (GA-REQ-061 · Cutover operacional — `SPEC_READY`) — orden T11 → **T14** → T12 → T13.
