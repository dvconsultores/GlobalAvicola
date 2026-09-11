# GA-R184 · EVIDENCIA DE RED

Referencia cruda: `evidence/green/runtime-e2e.json` (`network_sample`) y `evidence/red/runtime-red.json`.

## 1 · Muestreo de cabeceras (post-fix, `GET /reports/kpi/ipe/11` → 200)

| Cabecera | Valor observado |
|---|---|
| Content-Type | `application/json` |
| Server | nginx (frontal del entorno) |
| Resto | Sin cabeceras de caché del KPI (respuesta dinámica autenticada) |

## 2 · Matriz de códigos observada en la tranche

| Situación | Código | Nota |
|---|---|---|
| IPE pre-fix (lotes con `start_date`) | **500** ×2 (`/35`, `/33`) | RED original capturado |
| IPE post-fix | **200** | batería completa |
| Swap de contenedor durante el deploy | **502** puntual | transitorio de infraestructura (Watchtower), no reproducible tras el swap |
| Sin token | 401 (comportamiento estándar del repo) | — |
| Sin `reports:read` | **403** | E2E-12 |
| Lote inexistente / ajeno / fuera de alcance (incl. BU OFF) | **404** «Lote no encontrado» | E2E-08/09/10/11 |
| Hermano G-05 pre-fix (registro separado) | **500** | candidato R-186 |

## 3 · Higiene

Sin credenciales, tokens ni cookies en los artefactos de red (solo códigos, rutas y cuerpos ya presentes en la evidencia primaria).
