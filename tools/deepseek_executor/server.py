"""DeepSeek EXECUTOR — servidor MCP (stdio) para Claude Code · Global Avícola.

Claude orquesta; DeepSeek ejecuta. Este servidor expone a Claude la herramienta `deepseek_execute`:
recibe una delegación autosuficiente y la resuelve con un agente DeepSeek que dispone de herramientas
reales sobre el repositorio (leer/escribir/editar archivos, listar, buscar, ejecutar comandos) y devuelve
un informe estructurado (acciones, archivos tocados, comandos y su salida, resumen final).

Seguridad:
  * La clave se lee de `<repo>/.env` (`DEEPSEEK_API_KEY`) o del entorno; jamás se escribe en configuración,
    logs ni respuestas.
  * Todo acceso a archivos y todo comando se acota a la raíz del repositorio (`DEEPSEEK_EXECUTOR_ROOT`
    o el directorio padre de `tools/`). Se rechazan rutas fuera y comandos destructivos/prohibidos por la
    gobernanza (`CLAUDE.md §5, §9`): ramas nuevas, push, reset --hard, DROP/TRUNCATE, rm -rf fuera de
    directorios temporales, edición de `.github/workflows`, lectura de `.env`.
  * Sin red más allá de la API de DeepSeek. Sin SAP.

Presupuesto de turnos: al 75 % del presupuesto se inyecta un aviso para que el modelo cierre el informe y en el
último turno se fuerza respuesta textual (`tool_choice="none"`); si aun así no hay informe final, se conserva el
último texto del asistente en `last_assistant_content`.

Entrega de informes: el informe completo se persiste siempre (también en INCOMPLETE/DONE_UNSTRUCTURED) en
`~/.cache/deepseek_executor/runs/<timestamp>-<hash>.json` y su ruta se devuelve en `report_path`, de modo que un
JSON mal formado o recortado en la respuesta nunca suponga perder la evidencia detallada.

Uso manual:  .venv/bin/python server.py            (stdio MCP)
             .venv/bin/python server.py --selftest  (comprueba clave y modelo sin ejecutar nada)
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import shlex
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

import httpx
from mcp.server.fastmcp import FastMCP

AQUI = Path(__file__).resolve().parent
ROOT = Path(os.environ.get("DEEPSEEK_EXECUTOR_ROOT") or AQUI.parents[1]).resolve()
API_URL = os.environ.get("DEEPSEEK_API_URL", "https://api.deepseek.com/chat/completions")
MODEL = os.environ.get("DEEPSEEK_MODEL", "deepseek-v4-flash")  # `deepseek-chat` es alias obsoleto; `deepseek-v4-pro` para tareas difíciles
MAX_TURNS_DEFAULT = int(os.environ.get("DEEPSEEK_MAX_TURNS", "40"))
CMD_TIMEOUT = int(os.environ.get("DEEPSEEK_CMD_TIMEOUT", "900"))
MAX_TOOL_OUTPUT = 12_000
MAX_FILE_CHARS = 60_000

#: Nunca legibles ni escribibles por el ejecutor.
RUTAS_PROHIBIDAS = (".env", ".git/config", ".github/workflows")
#: Comandos que la gobernanza reserva al Owner/orquestador.
PATRONES_PROHIBIDOS = [
    r"\bgit\s+(checkout|switch)\s+(-b|-c)\b", r"\bgit\s+branch\s+(?!--show-current|-a\b|-r\b|--list|-v)\S",
    r"\bgit\s+push\b", r"\bgit\s+reset\s+--hard\b", r"\bgit\s+clean\b", r"\bgit\s+rebase\b", r"\bgit\s+add\s+(\.|-A|--all)(\s|$)",
    r"\brm\s+-[a-zA-Z]*r[a-zA-Z]*f?\s+(/|~|\$HOME|\.\.|\*)", r"\brm\s+-[a-zA-Z]*r[a-zA-Z]*\s+(?!/tmp/|\./?(node_modules|dist|\.pytest_cache|__pycache__))\S*\s*$",
    r"\bDROP\s+(DATABASE|SCHEMA|TABLE)\b", r"\bTRUNCATE\b", r"\bsudo\b", r"\bchmod\s+[0-7]*7[0-7]*\s+/", r"\bcurl\b.*\b(sap|hana)\b",
    r"\bcat\s+\S*\.env\b", r"\.github/workflows", r"\bmkfs\b", r"\bdd\s+if=", r":\(\)\s*\{",
]
SYSTEM_PROMPT = """Eres el EJECUTOR técnico del proyecto Global Avícola (FastAPI + SQLAlchemy async + Alembic + React/TS).
Recibes delegaciones autosuficientes del ORQUESTADOR y las ejecutas con las herramientas disponibles, trabajando
exclusivamente dentro de la raíz del repositorio indicada.

Reglas invariables:
- Lee antes de editar. Edita con reemplazos exactos (edit_file) y conserva el estilo del código circundante.
- Verifica tu trabajo con los comandos de prueba que indique la delegación (p. ej. `backend/scripts/run_tests.sh <ruta>`,
  `npx vitest run`, `npx tsc -b`). No declares éxito sin salida real de pruebas.
- No crees ramas, no hagas push, no toques `.github/workflows`, no leas `.env`, no ejecutes DROP/TRUNCATE ni llamadas a SAP.
- No reduzcas ni elimines tests para obtener verde. No introduzcas secretos.
- Si algo te bloquea, detente y repórtalo con precisión en lugar de inventar.

Al terminar responde SOLO con un JSON con esta forma:
{"status": "DONE"|"FAIL"|"BLOCKED", "summary": "<qué hiciste>", "files_changed": ["..."], "tests": "<comando y resultado real>",
 "evidence": "<salidas clave, breves>", "open_issues": ["..."]}
"""

mcp = FastMCP("deepseek-executor")


# ── clave ────────────────────────────────────────────────────────────────────

def api_key() -> str:
    k = os.environ.get("DEEPSEEK_API_KEY")
    if not k:
        env = ROOT / ".env"
        if env.exists():
            for linea in env.read_text(encoding="utf-8", errors="ignore").splitlines():
                m = re.match(r"^\s*(?:export\s+)?DEEPSEEK_API_KEY\s*=\s*['\"]?([^'\"\s#]+)", linea)
                if m:
                    k = m.group(1)
                    break
    if not k:
        raise RuntimeError("DEEPSEEK_API_KEY no disponible (ni en el entorno ni en <repo>/.env)")
    return k


def redactar(texto: str) -> str:
    return re.sub(r"sk-[A-Za-z0-9]{8,}", "sk-…REDACTED", texto)


# ── herramientas del agente (acotadas a ROOT) ────────────────────────────────

def _ruta(p: str, *, escribir: bool = False) -> Path:
    r = (ROOT / p).resolve() if not os.path.isabs(p) else Path(p).resolve()
    if ROOT != r and ROOT not in r.parents:
        raise PermissionError(f"ruta fuera del repositorio: {p}")
    rel = r.relative_to(ROOT).as_posix()
    if any(rel == x or rel.startswith(x + "/") or rel.endswith("/" + x) for x in RUTAS_PROHIBIDAS) or rel.split("/")[-1].startswith(".env"):
        raise PermissionError(f"ruta protegida por gobernanza: {rel}")
    if escribir and "/.venv/" in f"/{rel}/":
        raise PermissionError("no se escribe dentro de entornos virtuales")
    return r


def t_read_file(path: str, offset: int = 1, limit: int = 400) -> str:
    r = _ruta(path)
    if not r.is_file():
        return f"ERROR: no existe el archivo {path}"
    lineas = r.read_text(encoding="utf-8", errors="replace").splitlines()
    sel = lineas[max(offset - 1, 0): max(offset - 1, 0) + limit]
    cuerpo = "\n".join(f"{i}\t{l}" for i, l in enumerate(sel, start=max(offset, 1)))
    return f"[{path} · {len(lineas)} líneas · mostrando {max(offset,1)}-{max(offset,1)+len(sel)-1}]\n{cuerpo[:MAX_FILE_CHARS]}"


def t_write_file(path: str, content: str) -> str:
    r = _ruta(path, escribir=True)
    r.parent.mkdir(parents=True, exist_ok=True)
    nuevo = not r.exists()
    r.write_text(content, encoding="utf-8")
    return f"OK: {'creado' if nuevo else 'sobrescrito'} {path} ({len(content)} caracteres)"


def t_edit_file(path: str, old_string: str, new_string: str, replace_all: bool = False) -> str:
    r = _ruta(path, escribir=True)
    if not r.is_file():
        return f"ERROR: no existe {path}"
    texto = r.read_text(encoding="utf-8")
    n = texto.count(old_string)
    if n == 0:
        return "ERROR: old_string no aparece en el archivo (copia el texto exacto, con su indentación)"
    if n > 1 and not replace_all:
        return f"ERROR: old_string aparece {n} veces; amplía el contexto o usa replace_all=true"
    r.write_text(texto.replace(old_string, new_string) if replace_all else texto.replace(old_string, new_string, 1), encoding="utf-8")
    return f"OK: {path} editado ({n if replace_all else 1} reemplazo(s))"


def t_list_dir(path: str = ".", depth: int = 1) -> str:
    base = _ruta(path)
    salida = []
    for p in sorted(base.rglob("*") if depth > 1 else base.glob("*")):
        rel = p.relative_to(base)
        if any(part in {".git", "node_modules", ".venv", "__pycache__", "dist", ".pytest_cache"} for part in rel.parts):
            continue
        if len(rel.parts) > depth:
            continue
        salida.append(f"{rel.as_posix()}{'/' if p.is_dir() else ''}")
        if len(salida) >= 400:
            salida.append("… (truncado)"); break
    return "\n".join(salida) or "(vacío)"


def t_search(pattern: str, path: str = ".", glob: str = "", max_results: int = 200) -> str:
    base = _ruta(path)
    cmd = ["rg", "-n", "--no-heading", "--color", "never", "-m", "50", "--glob", "!.env*", "--glob", "!.git/*", "--glob", "!node_modules/*", "--glob", "!.venv/*"]
    if glob:
        cmd += ["--glob", glob]
    cmd += ["-e", pattern, str(base)]
    try:
        out = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    except FileNotFoundError:
        out = subprocess.run(["grep", "-rn", "--exclude-dir=.git", "--exclude-dir=node_modules", "--exclude-dir=.venv", "--exclude=.env*", "-e", pattern, str(base)],
                             capture_output=True, text=True, timeout=60)
    lineas = out.stdout.replace(str(ROOT) + "/", "").splitlines()[:max_results]
    return "\n".join(lineas) or "(sin coincidencias)"


def _comando_permitido(cmd: str) -> Optional[str]:
    for pat in PATRONES_PROHIBIDOS:
        if re.search(pat, cmd, flags=re.IGNORECASE):
            return f"comando bloqueado por gobernanza (patrón: {pat})"
    return None


def t_run_command(command: str, cwd: str = ".", timeout: int = CMD_TIMEOUT) -> str:
    motivo = _comando_permitido(command)
    if motivo:
        return f"ERROR: {motivo}"
    base = _ruta(cwd)
    env = {k: v for k, v in os.environ.items() if k not in {"DEEPSEEK_API_KEY"}}
    env.setdefault("PATH", "/usr/local/bin:/usr/bin:/bin")
    nvm = Path.home() / ".nvm/versions/node"
    if nvm.exists():
        versiones = sorted(nvm.glob("v*"), reverse=True)
        if versiones:
            env["PATH"] = f"{versiones[0]}/bin:" + env["PATH"]
    t0 = time.time()
    try:
        out = subprocess.run(["bash", "-lc", command], cwd=str(base), capture_output=True, text=True, timeout=min(timeout, CMD_TIMEOUT), env=env)
    except subprocess.TimeoutExpired:
        return f"ERROR: tiempo excedido ({min(timeout, CMD_TIMEOUT)} s) ejecutando: {command}"
    texto = (out.stdout + ("\n[stderr]\n" + out.stderr if out.stderr.strip() else "")).strip()
    texto = redactar(texto.replace(str(ROOT), "<repo>"))
    if len(texto) > MAX_TOOL_OUTPUT:
        texto = texto[:MAX_TOOL_OUTPUT // 2] + "\n… [salida truncada] …\n" + texto[-MAX_TOOL_OUTPUT // 2:]
    return f"[rc={out.returncode} · {time.time()-t0:.1f}s]\n{texto}"


def _error_herramienta(nombre: str, e: Exception) -> str:
    """Traduce la excepción del despacho a un texto accionable. Un `TypeError` con «missing … required positional
    argument» significa que la llamada llegó sin argumentos (típico cuando el contenido excede lo que el modelo puede
    emitir en una sola llamada): se le indica cómo trocear el archivo en lugar de dejar que reintente igual."""
    mensaje = str(e)
    if isinstance(e, TypeError) and "missing" in mensaje and "required positional argument" in mensaje:
        return (f"ERROR: la llamada a {nombre} llegó sin argumentos (suele ocurrir cuando el contenido supera el tamaño "
                "que el modelo puede emitir en una sola llamada). Divide el contenido: crea el archivo con write_file y un "
                "marcador <!--CHUNK--> y añade fragmentos de ≤1800 caracteres con edit_file reemplazando el marcador.")
    return f"ERROR: {type(e).__name__}: {mensaje}"


HERRAMIENTAS = {
    "read_file": (t_read_file, {"type": "object", "properties": {"path": {"type": "string"}, "offset": {"type": "integer"}, "limit": {"type": "integer"}}, "required": ["path"]},
                  "Lee un archivo del repositorio (líneas numeradas)."),
    "write_file": (t_write_file, {"type": "object", "properties": {"path": {"type": "string"}, "content": {"type": "string"}}, "required": ["path", "content"]},
                   "Crea o sobrescribe un archivo completo."),
    "edit_file": (t_edit_file, {"type": "object", "properties": {"path": {"type": "string"}, "old_string": {"type": "string"}, "new_string": {"type": "string"}, "replace_all": {"type": "boolean"}}, "required": ["path", "old_string", "new_string"]},
                  "Reemplazo exacto de texto en un archivo (old_string debe ser único salvo replace_all)."),
    "list_dir": (t_list_dir, {"type": "object", "properties": {"path": {"type": "string"}, "depth": {"type": "integer"}}}, "Lista un directorio."),
    "search": (t_search, {"type": "object", "properties": {"pattern": {"type": "string"}, "path": {"type": "string"}, "glob": {"type": "string"}, "max_results": {"type": "integer"}}, "required": ["pattern"]},
               "Busca una expresión regular en el repositorio (ripgrep)."),
    "run_command": (t_run_command, {"type": "object", "properties": {"command": {"type": "string"}, "cwd": {"type": "string"}, "timeout": {"type": "integer"}}, "required": ["command"]},
                    "Ejecuta un comando bash dentro del repositorio (tests, build, git de solo lectura/stage/commit). Sin push, sin ramas, sin DROP."),
}
TOOLS_SPEC = [{"type": "function", "function": {"name": n, "description": d, "parameters": s}} for n, (_, s, d) in HERRAMIENTAS.items()]


# ── bucle del agente ─────────────────────────────────────────────────────────

def _llamar(mensajes: list[dict], *, key: str, timeout: float = 300.0, tool_choice: str = "auto") -> dict:
    cuerpo = {"model": MODEL, "messages": mensajes, "tools": TOOLS_SPEC, "tool_choice": tool_choice, "temperature": 0.1, "max_tokens": 8192}
    with httpx.Client(timeout=timeout) as c:
        for intento in range(3):
            r = c.post(API_URL, headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"}, json=cuerpo)
            if r.status_code in (429, 500, 502, 503, 504) and intento < 2:
                time.sleep(3 * (intento + 1)); continue
            if r.status_code != 200:
                raise RuntimeError(f"DeepSeek API {r.status_code}: {redactar(r.text[:500])}")
            return r.json()
    raise RuntimeError("DeepSeek API: sin respuesta tras reintentos")


def _parsear_informe(final: str) -> dict[str, Any]:
    """Extrae el informe JSON del texto final del modelo aunque venga con fences ```json, texto alrededor o
    saltos de línea sin escapar dentro de las cadenas. Devuelve {} si no hay JSON recuperable."""
    texto = re.sub(r"^```[a-zA-Z]*\s*", "", final.strip())  # fence de apertura
    texto = re.sub(r"\s*```\s*$", "", texto)                # fence de cierre
    bloque = re.search(r"\{.*\}", texto, flags=re.S)
    if not bloque:
        return {}
    candidato = bloque.group(0)
    try:
        return json.loads(candidato, strict=False)  # strict=False tolera caracteres de control dentro de cadenas
    except json.JSONDecodeError:
        pass
    # Segundo intento: escapar los saltos de línea literales que el modelo dejó dentro del JSON.
    try:
        return json.loads(re.sub(r"(?<!\\)\n", r"\\n", candidato), strict=False)
    except json.JSONDecodeError:
        return {}


def _persistir_informe(informe: dict[str, Any], task: str, final_raw: str) -> dict[str, Any]:
    """Guarda el informe íntegro (sin recortes) en ~/.cache/deepseek_executor/runs/ y anota su ruta en `report_path`.
    La persistencia nunca debe tumbar la ejecución: ante cualquier error se informa en `report_error`."""
    try:
        carpeta = Path.home() / ".cache" / "deepseek_executor" / "runs"
        carpeta.mkdir(parents=True, exist_ok=True)
        ruta = carpeta / f"{datetime.now():%Y%m%dT%H%M%S}-{hashlib.sha1(task.encode('utf-8')).hexdigest()[:8]}.json"
        volcado = {**informe, "task": redactar(task)[:2000], "final_raw": redactar(final_raw)}
        ruta.write_text(json.dumps(volcado, ensure_ascii=False, indent=1), encoding="utf-8")
        informe["report_path"] = str(ruta)
    except Exception as e:  # noqa: BLE001
        informe["report_path"] = None
        informe["report_error"] = redactar(f"{type(e).__name__}: {e}")
    return informe


def ejecutar(task: str, *, max_turns: int, contexto: str = "") -> dict[str, Any]:
    key = api_key()
    mensajes = [{"role": "system", "content": SYSTEM_PROMPT + f"\nRaíz del repositorio: {ROOT}\n"},
                {"role": "user", "content": (f"CONTEXTO ADICIONAL:\n{contexto}\n\n" if contexto else "") + f"DELEGACIÓN:\n{task}"}]
    acciones: list[dict] = []
    tocados: set[str] = set()
    uso = {"prompt_tokens": 0, "completion_tokens": 0}
    final = None
    ultimo_contenido = ""  # último `content` no vacío del asistente, para no perder el trabajo si no hay informe
    aviso_enviado = False
    for turno in range(max_turns):
        # Presupuesto de turnos: al 75 % se apremia al modelo a cerrar y en el último turno se le impide usar herramientas.
        if max_turns >= 4 and not aviso_enviado and turno == int(max_turns * 0.75):
            mensajes.append({"role": "user", "content": "AVISO DEL ORQUESTADOR: has consumido el 75 % de los turnos. Deja de investigar y entrega AHORA el informe final en el JSON acordado, indicando en open_issues lo que quede pendiente."})
            aviso_enviado = True
        ultimo = turno == max_turns - 1
        resp = _llamar(mensajes, key=key, tool_choice="none" if ultimo else "auto")
        u = resp.get("usage") or {}
        uso["prompt_tokens"] += u.get("prompt_tokens", 0); uso["completion_tokens"] += u.get("completion_tokens", 0)
        msg = resp["choices"][0]["message"]
        if msg.get("content"):
            ultimo_contenido = msg["content"]
        mensajes.append({k: v for k, v in msg.items() if k in ("role", "content", "tool_calls") and v is not None})
        llamadas = msg.get("tool_calls") or []
        if not llamadas:
            final = msg.get("content") or ""
            break
        for tc in llamadas:
            nombre = tc["function"]["name"]
            try:
                args = json.loads(tc["function"].get("arguments") or "{}")
            except json.JSONDecodeError:
                args = {}
            fn = HERRAMIENTAS.get(nombre, (None,))[0]
            t0 = time.time()
            try:
                resultado = fn(**args) if fn else f"ERROR: herramienta desconocida {nombre}"
            except Exception as e:  # noqa: BLE001
                resultado = _error_herramienta(nombre, e)
            if nombre in ("write_file", "edit_file") and str(resultado).startswith("OK"):
                tocados.add(args.get("path", "?"))
            acciones.append({"turn": turno + 1, "tool": nombre, "args": {k: (v if len(str(v)) < 300 else str(v)[:300] + "…") for k, v in args.items()},
                             "result_head": redactar(str(resultado))[:400], "seconds": round(time.time() - t0, 1)})
            mensajes.append({"role": "tool", "tool_call_id": tc["id"], "content": redactar(str(resultado))})
    informe: dict[str, Any] = {"model": MODEL, "turns": len([a for a in acciones]), "tool_calls": len(acciones), "files_touched": sorted(tocados), "usage": uso, "actions": acciones}
    if final is None:
        informe["status"] = "INCOMPLETE"; informe["summary"] = f"se alcanzó el máximo de turnos ({max_turns}) sin informe final"
        if ultimo_contenido:
            informe["last_assistant_content"] = redactar(ultimo_contenido)[:4000]
        return _persistir_informe(informe, task, ultimo_contenido)
    parsed = _parsear_informe(final)
    informe["status"] = parsed.get("status", "DONE_UNSTRUCTURED")
    # Si el informe no es JSON recuperable se conserva el texto completo (hasta 60000 caracteres), nunca un recorte corto.
    informe["summary"] = parsed.get("summary", redactar(final)[:60000])
    for k in ("tests", "evidence", "open_issues"):
        if k in parsed:
            informe[k] = parsed[k]
    if "files_changed" in parsed:
        informe["files_changed_reported"] = parsed["files_changed"]
    return _persistir_informe(informe, task, final)


# ── herramientas MCP (lo que ve Claude) ──────────────────────────────────────

@mcp.tool()
def deepseek_execute(task: str, context: str = "", max_turns: int = MAX_TURNS_DEFAULT) -> str:
    """EJECUTOR DeepSeek: resuelve una delegación autosuficiente (objetivo, archivos, restricciones, AC, pruebas,
    salida esperada) con herramientas reales sobre el repositorio y devuelve un informe JSON con acciones, archivos
    tocados, pruebas ejecutadas y resumen. El orquestador debe verificar el resultado con las suites reales."""
    try:
        informe = ejecutar(task, max_turns=max(1, min(max_turns, 120)), contexto=context)
        salida = json.dumps(informe, ensure_ascii=False, indent=1)
        if len(salida) > 45000:
            # El informe completo queda en `report_path`: se recortan solo las acciones para no desbordar el contexto.
            informe["actions"] = informe.get("actions", [])[:10]
            informe["actions_truncated"] = True
            salida = json.dumps(informe, ensure_ascii=False, indent=1)
        return salida
    except Exception as e:  # noqa: BLE001
        return json.dumps({"status": "ERROR", "error": redactar(f"{type(e).__name__}: {e}")}, ensure_ascii=False)


@mcp.tool()
def deepseek_executor_status() -> str:
    """Estado del ejecutor: raíz del repositorio, modelo, disponibilidad de la clave (sin revelarla) y conectividad con la API."""
    estado = {"root": str(ROOT), "model": MODEL, "api_url": API_URL, "key": "absent", "api": "unknown"}
    try:
        key = api_key(); estado["key"] = "present"
        with httpx.Client(timeout=20) as c:
            r = c.get(API_URL.replace("/chat/completions", "/models"), headers={"Authorization": f"Bearer {key}"})
        estado["api"] = f"HTTP {r.status_code}"
        if r.status_code == 200:
            estado["models"] = [m.get("id") for m in r.json().get("data", [])][:10]
    except Exception as e:  # noqa: BLE001
        estado["api"] = redactar(f"{type(e).__name__}: {e}")
    return json.dumps(estado, ensure_ascii=False)


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        print(deepseek_executor_status()); sys.exit(0)
    mcp.run(transport="stdio")
