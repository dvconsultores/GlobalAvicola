# GA-F01 · EVIDENCIA RED (R-189)

Fecha: 2026-09-12 · Pre-implementación (C1) · Comando: `npx vitest run src/pages/operations/__tests__/f01.payloadContract.test.tsx src/pages/operations/__tests__/f01.errorRendering.test.tsx src/components/__tests__/f01.getErrorMessage.test.ts`.

## 1 · Archivos RED

| Archivo | Qué ejerce | Objetivo |
|---|---|---|
| `f01.payloadContract.test.tsx` | Render del formulario real + Guardar; inspección del payload del POST | `egg_storage_records = []`, `sap_document_ref` = código, filas sin NaN, `lot_id` nulo |
| `f01.errorRendering.test.tsx` | Render + POST rechazado con 422 FastAPI realista | página montada + mensaje humano (sin React #31) |
| `f01.getErrorMessage.test.ts` | Unit del helper compartido | siempre string renderizable |

## 2 · Primera corrida (pesos rellenos → la petición llegaba)

```
× AC03/AC04  AssertionError: expected [ {} ] to deeply equal []          ← S1 ([{}] por omisión)
× AC08-AC11  AssertionError: expected undefined to be 'PO-C001-GPR-0001' ← S2 (OC no llega al campo tipado)
× AC19-AC26  (form desmontado tras el rechazo)                            ← S3 (React #31)
× unit ×2    expected 'object' to be 'string'                             ← S3 (detail crudo)
```

## 3 · Corrida final (viaje real: pesos vacíos, fila ♀ vacía)

```
Tests  6 failed | 3 passed (9)
× unit ×2            detail lista/objeto ⇒ devuelve objeto (rompe render)
× AC03/AC04          post NO llamado — el NaN de campos vacíos bloquea en silencio (C26)
× AC08-AC11          post NO llamado — ídem
× AC15 recepción     post NO llamado — fila vacía + NaN (misma familia)
× AC19-AC26          tras el rechazo la página queda inutilizable (crash)
```

Fallo = comportamiento defectuoso real del formulario (no del arnés: los tres `/` de montaje — `ToastProvider`, rutas, `matchMedia` — quedaron resueltos y los positivos de contexto pasan). **RED válido** (S1/S2/S3 + familia NaN documentados en `GA_F01_*` y controles de contrato).

## 4 · RED v6 — F-01d (`feed_movements`/`hatchery_params` con fila vacía)

Detectado en la repetición del E2E post-C2 (UAT-02 bloqueado). Evidencia:

| Prueba | Resultado | Artefacto |
|---|---|---|
| Nube · `GET` detalles con fila `{}` en alimento (ids 112/115/116/117) | **500** determinista (×2) | `evidence/f01d/RED_cloud_payload_y_500.md` |
| Nube · controles (sin claves / `[]` / hatch-only) | 200 | ídem (nota de exactitud: el disparador es `[{}]`, no la clave) |
| Local · matriz en PostgreSQL de pruebas (`feed[{}]`, `hatchery[{}]`, `egg[{}]`, sin claves) | `feed[{}]` ⇒ POST 201 + GET **500**; `hatchery[{}]` ⇒ 201 + 200 (fila basura persistida); controles 200 | `evidence/f01d/RED_local_matriz.txt` |
| Local · traceback con cliente estricto | `ValidationError: FeedMovementSchema.quantity_kg gt=0 (0.0)` | `evidence/f01d/RED_local_traceback_exception.txt` |

Causa: el default `0.0` de `quantity_kg` no se valida en alta (Pydantic v2) ⇒ la fila vacía se
persiste; en lectura el valor presente viola `gt=0` ⇒ 500. Análisis completo en
`GA_F01D_SUBSANACION_ANNEX.md`. **RED v6 válido** (reproducido localmente y en nube, con controles).
