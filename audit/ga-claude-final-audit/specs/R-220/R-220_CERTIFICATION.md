# R-220 · CERTIFICATION — Residuales P3 de contrato, UX, móvil, i18n y rutas

Fecha: 2026-09-14 · Programa: GA PRE-SAP · Tranche: **T11** · Política: **AOD-29 Clarification 01**
(certificación **local** con gates reproducibles; **GitHub Actions retirado**; **push requerido**
a `origin/main` con verificación de SHA remoto).

Ejecución **por lotes** A → B → C → D con gobernanza completa por paquete
(SPEC→AC→RED→IMPLEMENTATION→GREEN→SENSIBILIDAD→POST-MUTACIÓN→EVIDENCIA→COMMIT→PUSH).

## 1 · Paquetes y commits (lotes)

### Lote A · Contrato de lectura / UX menor (A1–A18)

| Ítem | Commits (IMPL · evidencia) |
|---|---|
| A14/A9/A4/D4 | `ddc225f` |
| A3/A5 | `aa3e41e` · `72e452f` |
| A18 (`egg_storage` 4xx) | `af8107e` (BE) |
| A1/A2 (fechas civiles · lote dinámico en reportes) | `6f32ffa` · `200a4c8` |
| A6 (detalle de operación completo) | `0df4c35` · `cd5b853` |
| A7 (notificaciones: textos + destinos) | `950425d` · `a8c4539` |
| A8 (`X-Total-Count` + «Cargar más») | `b7cf0ce` · `0c49b3d` |
| A10/A11 (sin `sap_reference`; `farm_id` opcional) | `b2a2c1f` · `575bd01` |
| A15 (`egg_classification` inalcanzable retirado) | `4efa0c0` · `6c84895` |
| A12/A13 | verificados por lectura (día de ovoscopía viaja en `week_number`; `value_numeric` serializado) |

### Tanda A-extra · A16/A17

| Ítem | RED | IMPL | Ajuste | Evidencia |
|---|---|---|---|---|
| A16 (BR-21 en cliente) · A17 (semana/peso anclados a la primera fila viva) | `f11786c` | `30c1660` | `ad9896e` (r194-04a alineado a BR-21) | `2432ce7` |

### Lote B · Móvil / responsive / navegación (B1–B10)

| Ítem | Commit (IMPL) | Notas |
|---|---|---|
| B1/B2 (hamburguesa monta `MobileDrawer`; perfil/logout en cabecera móvil) | `2723b44` | `gaFe02b` envuelto en `MemoryRouter`; evidencia `739ce74` |
| B3/B5 (entradas `/my-pending`, «Historial») | `297e72c` | RED `34ebdd3` |
| B4 (reporte del lote dinámico + enlaces) | `4f54c84` | RED `1e12eee` |
| B6 (gate `operations:create` en tiles/timeline) | `dad386b` | RED 12 enlaces sin autoridad; evidencia `17358bb` |
| B7 (contador de procesos dinámico) | `b2352b0` | evidencia `dcea096` |
| B8 (panel de notificaciones a 390px) | verificado por lectura | — |
| B9 (botón eliminar máquina con ancestro posicionado) | `6c08ee1` | RED por causa exacta (el C1 `4d62859` portaba error de harness — corregido y documentado); evidencia `7c2efc5` |
| B10 (cosméticos R7–R12/R14/R15) | `9451bf5` | RED real 8/8 sobre fuentes originales (primer RED de harness — documentado); evidencia `e51d1fa` |

Housekeeping lote A: `40e9b44` (test A7 sincronizado al DOM real).

### Lote C · I18N (C1–C9)

| Tanda | Commits | Contenido |
|---|---|---|
| C1/C2/C7 | `1d9c131` (evidencia `6ae6d5f`) | status/event_type/sex/egg_type traducidos; `roles.actions`(9)/`roles.modules`(13) ES/EN; claves engañosas corregidas (`common.prev`, `common.viewDetail`, `dashboard.processes`, `operations.stagesGroup`) |
| C3–C9 | `efe6130` (evidencia `32f5d40`) | zod de lote por claves; +33 claves ES/EN; `formatFechaHora` con locale de la app (ReviewDetail/Audit/Sap; export con `locale` por parámetro); ES sin texto EN; `NotificationType.lot_near_close`; mocks i18n de `r219`/`r197`/`gaFe04` alineados |

C5 (errores backend ES para EN): aceptado/documentado. C8 «unidades sueltas»: verificado — ya no existen literales.

### Lote D · Código muerto / contratos obsoletos (D1–D5)

| Ítem | Commit (IMPL) | Contenido |
|---|---|---|
| D1/D2/D5 | `da31f52` (evidencia `3c3ab3d`) | 8 hooks muertos + `types/api.types.ts` retirados; `UserResponse` = `UserRead`; `sap_reference` fuera de `LotResponse`; `action_type` enumerado; `ProtectedRoute.roles` (chequeo muerto) retirado |
| D3 | resuelto en B1 (MobileDrawer **montado**); `SidebarSubmenu` retirado | — |
| D4 | `ddc225f` (lote A) | clases residuales |

## 2 · Gates locales

| Gate | Resultado |
|---|---|
| R-220 BE targeted (lote A/extra) | ver cert por paquete (§ evidences `loteA*/`, `loteA1617/`) |
| **R-220 suite BE completa (final)** | **1389 passed / 0 failed / 49 skipped** (19:51) — corrida final tras la alineación `8604a60`; evidencia `evidence/green/be-full-1389.log` (la corrida previa `1386/3F` — deriva de conteos 25→26 — queda archivada como `be-full-pre-alignment.log`) |
| Guardián de rutas `/api/` | **214** (sin cambios — R-220 no toca el contrato de rutas) |
| **Suite FE completa (final)** | **520/520** (exit 0) |
| `npm run build` (`tsc -b && vite build`) | **EXIT 0** |
| Worktree limpio tras cada cierre | ✔ |

## 3 · Sensibilidad (mutación + restore desde SHA explícito)

- A16/A17: mutación del anclaje (A17) y del validador (A16) → RED quirúrgico 1:1; restore `30c1660`.
- B1/B2: hamburguesa retirada → RED 1:1 (solo B1); restore `2723b44`.
- B6: `readOnly` retirado → RED 1:1 (solo grid); restore `dad386b`.
- B7: contador a `6` fijo → RED 1:1; restore `b2352b0`.
- B9: `relative` retirado → RED de causa exacta; restore `6c08ee1`.
- B10: bloque R15 revertido → RED 1:1; restore `9451bf5`.
- C1/C2/C7: `status.${...}` revertido → RED 1:1; restore `1d9c131`.
- C3–C9: clave C4 retirada → RED 1:1; restore `efe6130`.
- D: `roles` reinsertado → RED 1:1; restore `da31f52`.
- Post-mutación: worktree limpio y suites targeted verdes en cada caso.

## 4 · Notas de honestidad (registradas)

1. **B9**: el primer RED (`4d62859`) fallaba por **harness** (polyfill `matchMedia` + ruta de pasos). RED de causa exacta re-capturado y publicado en la evidencia (reemplazo), y nota en el commit C2.
2. **B10**: idéntico patrón — primer RED con error de harness (`URL` de jsdom resuelve contra `http://localhost:3000`); corregido con resolución `node:url`+`node:path`; RED real 8/8 sobre fuentes originales.
3. **A16**: `r194.hatcheryChain` AC-04a enviaba un cuerpo que BR-21 habría rechazado (sin sanos/débiles); alineado (`ad9896e`).
4. **C-β**: `export.ts` pasó de fijar `es-VE` a recibir `locale` por parámetro (evita acoplar el util al i18n global); 3 suites con mocks parciales de i18n ajustadas.
5. **A14 · regresión capturada en la suite completa (no en targeted)**: el catálogo informativo `/operations/event-types` pasó de 25 a **26** con `water_consumption` (corrección mandatada por B-24). Tres tests con conteo exacto (`test_f10_all_event_types_registered`, `test_ac09_ningun_tipo_de_evento_devuelve_500`, `test_list_event_types`) quedaron alineados a 26 + verificación de presencia del tipo (`8604a60`). **Observado (no corregido en R-220)**: `test_list_event_types` está **duplicado** en `test_operations.py` (dos definiciones idénticas; la primera queda sombreada) — se alinearon ambos sitios para no dejar deriva; la deduplicación queda como deuda menor registrada.

## 5 · Evidencia (índice)

`audit/ga-claude-final-audit/specs/R-220/evidence/{red,green,sensibilidad,post-mutation}/loteA1…loteA8`,
`loteB`, `loteB1B2`, `loteB2`, `loteB3`, `loteB6`, `loteB7`, `loteB10`, `loteA1617`, `loteC1`,
`loteC2`, `loteD` (logs con secretos sanitizados; `git add -f` para `.log`).

## 6 · Estado

`R-220_STATUS = CLOSED_TECHNICALLY` · `HEAD` certificado: ver `GA_T11_CERTIFICATION.md`.
