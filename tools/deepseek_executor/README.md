# deepseek-executor — MCP ejecutor de DeepSeek

Servidor MCP (stdio) de **Global Avícola** que materializa la regla **CLAUDE ORQUESTA, DEEPSEEK EJECUTA**: recibe una delegación autosuficiente, la resuelve con un agente DeepSeek que dispone de herramientas reales sobre el repositorio y devuelve un informe estructurado con acciones, archivos tocados, pruebas ejecutadas y resumen.

- Código: `tools/deepseek_executor/server.py` · Registro: `.mcp.json`, servidor `deepseek-executor`
- Lanzador: `tools/deepseek_executor/run.sh` (crea `tools/deepseek_executor/.venv` con `mcp>=1.2,<2` y `httpx>=0.27` si falta)

## Registro y prueba

```bash
claude mcp add -s project deepseek-executor -- bash tools/deepseek_executor/run.sh
bash tools/deepseek_executor/run.sh --selftest   # → "key": "present", "api": "HTTP 200"
```

El selftest devuelve una línea JSON con `root`, `model`, `api_url`, `key` (`present` / `absent`, nunca su valor),
`api` (`HTTP 200`) y la lista `models` cuando la API responde.

Herramientas MCP que ve Claude:

- `deepseek_execute(task, context="", max_turns=40)` — ejecuta la delegación y devuelve el informe JSON (`max_turns` se acota a `1..120`).
- `deepseek_executor_status()` — raíz, modelo, endpoint, disponibilidad de la clave y conectividad con la API.

## Variables de entorno

| Variable | Por defecto | Uso |
| --- | --- | --- |
| `DEEPSEEK_API_KEY` | — | Se lee del entorno o de `<repo>/.env`; nunca se escribe en configuración, logs ni respuestas (se redacta `sk-…`). |
| `DEEPSEEK_MODEL` | `deepseek-v4-flash` | Modelo del agente (`deepseek-v4-pro` para tareas difíciles). |
| `DEEPSEEK_MAX_TURNS` | `40` | Turnos máximos por delegación. |
| `DEEPSEEK_CMD_TIMEOUT` | `900` | Segundos máximos por comando de `run_command`. |
| `DEEPSEEK_EXECUTOR_ROOT` | dos niveles sobre `tools/` | Raíz del repositorio donde se acotan archivos y comandos. |
| `DEEPSEEK_API_URL` | `https://api.deepseek.com/chat/completions` | Endpoint de la API. |

## Herramientas internas del agente

`read_file` (líneas numeradas, `offset`/`limit`), `write_file`, `edit_file` (reemplazo exacto, `replace_all`),
`list_dir` (`depth`), `search` (regex con ripgrep, `glob`, `max_results`) y `run_command` (`cwd`, `timeout`).
Toda ruta se resuelve contra la raíz: se rechaza lo de fuera y lo protegido (`.env*`, `.git/config`,
`.github/workflows`); no se escribe dentro de `.venv`.

## Guardas de gobernanza

`run_command` rechaza por patrón: `git push`, ramas nuevas (`checkout -b` / `switch -c`, `git branch <nombre>`),
`reset --hard`, `git clean`, `git rebase`, `git add .` / `-A` / `--all`, `rm -rf` fuera de temporales,
`DROP DATABASE|SCHEMA|TABLE`, `TRUNCATE`, `sudo`, `chmod` peligroso sobre `/`, `curl` a SAP/HANA, `cat *.env`,
`.github/workflows`, `mkfs`, `dd if=` y fork bombs. El comando se lanza sin `DEEPSEEK_API_KEY` en el entorno y la
salida se redacta antes de devolverla. Sin red más allá de la API de DeepSeek. Sin SAP; el **push a `origin/main` lo conserva el orquestador** (AOD-29).

## Informe JSON devuelto

`status` (`DONE` | `FAIL` | `BLOCKED` | `INCOMPLETE` | `ERROR`; `INCOMPLETE` si se agotan los turnos sin informe final, `ERROR` si falla la clave o la API, `DONE_UNSTRUCTURED` si el agente no devuelve JSON), `summary`, `model`, `turns` / `tool_calls`, `files_touched` (archivos escritos/editados con éxito), `files_changed_reported` (lo que declara el agente), `usage` (`prompt_tokens`, `completion_tokens`), `actions` (`turn`, `tool`, `args`, `result_head`, `seconds`), `tests`, `evidence` y `open_issues`.

## Limitaciones conocidas

- **Contenido demasiado largo en `write_file`**: si el modelo no puede emitir todo el contenido en una sola llamada,
  la herramienta puede llegar sin argumentos y el agente recibe un error explicativo (`la llamada a write_file llegó
  sin argumentos…`) en lugar del `TypeError` crudo. La forma de trabajo indicada es crear el archivo con `write_file`
  y un marcador `<!--CHUNK-->` y añadir fragmentos de ≤1800 caracteres con `edit_file` reemplazando el marcador.
- El informe es evidencia declarada, no certificación: la verificación con las suites reales corresponde al orquestador.

## Regla de verificación

El informe es **evidencia declarada, no certificación**: el orquestador verifica siempre con las suites reales (`backend/scripts/run_tests.sh <ruta>`, `npx vitest run`, `npx tsc -b`) y no acepta un `DONE` sin salida real de pruebas. Si el ejecutor no responde, Claude informa del bloqueo una vez.
