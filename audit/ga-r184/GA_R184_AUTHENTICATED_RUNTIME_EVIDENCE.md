# GA-R184 · EVIDENCIA RUNTIME AUTENTICADA (E2E-01…12)

Generación congelada post-deploy: backend con el fix **`3f88f94`** (blip transitorio 502 durante el swap de Watchtower, luego estable), bundle frontend sin cambio `index-BUthrUt9.js`. Actor principal: autoridad global con empresa 1 efectiva y ventana BU `broiler` ON (restaurada a OFF en limpieza). Evidencia cruda: `evidence/green/runtime-e2e.json`.

## 1 · Batería (14/14 PASS)

| Caso | Petición | Resultado | Veredicto |
|---|---|---|---|
| E2E-01 | `ipe/35` (daba 500 pre-fix) | **200** · ipe 0.0 (sin datos), viabilidad 100.0, age 1 | PASS |
| E2E-01b | `ipe/33` (daba 500 pre-fix) | **200** | PASS |
| E2E-02 | `ipe/11` valor determinista | esperado **{pesos_n 17, avg 1500.0, age 110, viab 100.0, fcr 24.5, ganancia 13.64, ipe 556.6}** == actual exacto | PASS |
| E2E-02b | 2ª llamada idéntica | JSON idéntico | PASS |
| E2E-03 | semántica temporal | `start 2026-05-24` · edad real 110 == `age_days` 110 (sin ±1) | PASS |
| E2E-04 | lote abierto (11 `active`) | 200 | PASS |
| E2E-05 | lote **cerrado** (53 `closed`, fixture F3) | esperado 37894.7 == actual 37894.7 (viab 100, avg 1800, age 19, fcr 2.5) | PASS |
| E2E-06 | datos ausentes (35: sin pesajes/alimento) | 200 · ipe 0.0 · fcr 0 — controlado, sin fabricar positivos | PASS |
| E2E-07 | cero/inválidos | sin ZeroDivisionError/NaN/∞ (guarda `fcr > 0`) | PASS |
| E2E-08 | `ipe/999999999` | **404** «Lote no encontrado» | PASS |
| E2E-09 | lote de **empresa ajena** (c3, id 14; ventana BU c3 usada y restaurada OFF) | **404** «Lote no encontrado» (anti-enumeración) | PASS |
| E2E-10 | **BU de empresa OFF** (broiler c1) | **404** · restaurada ON ⇒ 200 | PASS |
| E2E-11 | usuario sin concesión (`r184.lotes`, BU ON, RBAC sí) | **404** | PASS |
| E2E-12 | usuario sin RBAC (`r184.consulta`, BU ON, concesión n/a) | **403** «Permiso requerido: reports:read» | PASS |

**Cálculo independiente de E2E-02/05**: media de pesos desde `bird_movements` del detalle de cada evento de pesaje (datos crudos), mortalidad/feed desde `/reports/kpis`, edad desde `start_date`; la fórmula documentada se evaluó a mano en el script — nunca se derivó del código bajo prueba.

## 2 · UI (consumidor real — `LotDetailPage`)

| Medida | Resultado |
|---|---|
| Tarjeta **IPE 556.6 «Excelente»** visible (desktop 1440×900) | **PASS** (`evidence/green/UI-desktop-detalle-11.png`) |
| Móvil 390×844: valor visible, sin desborde horizontal | **PASS** (`evidence/green/UI-movil-detalle-11.png`) |
| Viabilidad 100 % · FCR 24.5 · Peso prom. 1500g · Edad 110 días en la tarjeta | PASS |
| Texto crudo «500 / Internal Server Error / Lote no encontrado» en la vista | **Ninguno** (falso positivo inicial del check por «1500g»; corregido y documentado en `ui-validation.json`) |
| Consola | 2 entradas = respuestas **403 de widgets sin permiso** (clase N-3 conocida, preexistente; invisible en uso normal) · **fatales 0** |
| ES/EN | No afectado (valor numérico + claves existentes; sin cambio de textos) |

## 3 · Verificaciones transversales

- **Sin efectos de escritura/auditoría** por la lectura del KPI (se observó auditoría solo de las mutaciones de fixture, como corresponde).
- **Rendimiento**: consultas del endpoint sin cambios (misma estructura; el fix no añade consultas, bucles ni N+1).
- **Logs**: el caso de negocio ya no genera traza de error no controlado; ningún 500 de IPE post-deploy en la batería.
- **OD-16**: con BU OFF el actor global ve **0 lotes** de empresa y el IPE responde 404 — fail-closed intacto.
