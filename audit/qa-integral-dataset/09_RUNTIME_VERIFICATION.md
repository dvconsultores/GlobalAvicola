# 09 · Verificación en el runtime compartido — `BLOCKED_EXTERNAL`

**Estado al cierre de esta misión (2026-10-18): QA_DATA_RUNTIME = NOT_LOADED · motivo: la base del runtime no es alcanzable desde la estación del orquestador.**

## Lo intentado (sin escrituras)

| Intento | Resultado |
|---|---|
| `python -m seeds.qa_integral_dataset --inventory` con el `DATABASE_URL` del `.env` de desarrollo (host redactado, base `avicolav2`) | la guarda de entorno pasó (`development`), pero la conexión fue **restablecida por el servidor durante la negociación SSL** (`ConnectionResetError: [Errno 104] Connection reset by peer`) |
| Sondeo de conectividad TCP y de modos SSL (`disable`/`require`) | **denegado por el clasificador de seguridad de la sesión** («Auto-Mode Bypass»). No se buscó una vía alternativa: la decisión es del Owner |

Conclusión: desde esta estación no hay ruta hacia la base del runtime (cortafuegos/`pg_hba`/proxy). El código del seed está certificado en aislado y listo para ejecutarse **donde la base sí es alcanzable** (el host del backend).

## Runbook para el Owner / operador del servidor (5–10 minutos)

Requisitos: imagen del backend con el SHA certificado desplegada (AOD-29: push ⇒ workflows ⇒ Watchtower) y acceso al contenedor del backend o a un host con `DATABASE_URL` del runtime.

```bash
# dentro del contenedor del backend (o en backend/ con el .venv y el DATABASE_URL del runtime)
python -m seeds.qa_integral_dataset --inventory                      # 1 · estado previo (lectura)
export GA_QA_SEED_PASSWORD='<contraseña temporal elegida por el Owner>'  # 2 · nunca en el repo
python -m seeds.qa_integral_dataset --apply --confirm-target avicolav2 \
       --run-id QA-DEMO-V1-RUNTIME-$(date +%Y%m%d) --fixtures-dir /tmp/qa_fixtures --manifest /tmp/QA_DATA_MANIFEST_runtime.json
python -m seeds.qa_integral_dataset --verify                         # 3 · QA_DATA_VERIFY = PASS esperado
python -m seeds.qa_integral_dataset --apply --confirm-target avicolav2   # 4 · CREATED = 0 esperado
```

Duración observada en aislado: 14 s el `--apply`. No requiere parada del servicio. No modifica datos existentes: solo añade las dos empresas QA y lo que cuelga de ellas.

Tras ejecutar: (a) entregar la contraseña a QA por canal seguro; (b) adjuntar `/tmp/QA_DATA_MANIFEST_runtime.json` y la salida de `--verify` a este directorio como `evidence/09_runtime_apply.log` (saneada); (c) `QA_DATA_READY` pasa a `YES`.

## Verificación funcional posterior (checklist, por la UI o por API)

1. Login de los 12 usuarios `qa.*` (200) y menú acorde a rol/BU (sección 2 de la guía).
2. `qa.isolation`: Progenitoras e Incubadora ausentes; `/lots` solo muestra `QA-ISO-*`.
3. `qa.operator.gp`: `/lots` solo lotes `QA-GP-*`/`QA-CUT-GP-*`; acceso a un lote de engorde ⇒ 404.
4. Dashboard con indicadores; Centro de Revisión con 3 pendientes, 2 en revisión, 3 devueltos; Aprobaciones con 7 validados.
5. Integración SAP: inbound `QA_SYNTHETIC`, 0 envíos; Reportes con datos; Cargas Iniciales con 4 aplicadas; Auditoría con entradas `qa.*`.
6. `--verify` en el runtime: `PASS`.

## Qué no se hizo y por qué

- No se forzó ninguna conexión ni se alteró la configuración de la sesión para rodear la denegación (regla de gobernanza: Claude no se autoconcede permisos).
- No se ejecutó el cleanup (OD-QA-04) ni ninguna llamada SAP (OD-QA-02).
