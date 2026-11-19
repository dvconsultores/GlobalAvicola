#!/usr/bin/env bash
#
# SPEC 016 §B (D-B5) — Guardia de paridad de despliegue.
#
# Uso: verify_runtime_sha.sh <base_url> <sha_esperado>
#
# Consulta lo que el despliegue dice de sí mismo:
#   GET <base>/api/v1/version   -> {"git_sha","build_time","environment"}  (backend)
#   GET <base>/version.json     -> {"git_sha","build_time"}                (frontend)
#
# Reglas (AC-VP-07):
#   - Cualquier SHA `unknown`/vacío            => DEPLOYMENT_PARITY=FAIL (unknown), exit 2.
#     No se puede certificar lo que no se sabe.
#   - Ambos SHA == esperado                    => DEPLOYMENT_PARITY=PASS, exit 0.
#   - SHA distinto pero los árboles coinciden  => DEPLOYMENT_PARITY=PASS (tree-equal), exit 0.
#     Las imágenes solo se reconstruyen si el push toca `backend/**` o `frontend/**`; un
#     commit de docs/tests no republica imagen, de modo que el runtime puede quedarse en un
#     commit anterior y seguir siendo el mismo código. Cada artefacto se compara contra SU
#     propio árbol.
#   - Cualquier otro caso                     => DEPLOYMENT_PARITY=FAIL, exit 1.
#
# La comparación por árboles exige estar dentro de un repositorio git con AMBOS commits
# presentes; si no lo están, no hay paridad que demostrar y el resultado es FAIL.
# Sin secretos, sin token, sin escrituras.

set -euo pipefail

usage() {
    cat >&2 <<'EOF'
uso: verify_runtime_sha.sh <base_url> <sha_esperado>

  <base_url>      URL base del despliegue, p. ej. https://avicola.example.com
                  (se ignora una barra final)
  <sha_esperado>  SHA (hex, 7..40 caracteres) del commit que se cree desplegado,
                  normalmente `git rev-parse HEAD`.
EOF
}

if [ "$#" -ne 2 ]; then
    usage
    exit 2
fi

BASE_URL="${1%/}"
RAW_EXPECTED="$2"
EXPECTED_SHA="$(printf '%s' "$RAW_EXPECTED" | tr '[:upper:]' '[:lower:]')"

if ! [[ "$EXPECTED_SHA" =~ ^[0-9a-f]{7,40}$ ]]; then
    echo "ERROR: sha_esperado no tiene forma hex de 7..40 caracteres: '${RAW_EXPECTED}'" >&2
    usage
    exit 2
fi

if [ -z "$BASE_URL" ]; then
    echo "ERROR: base_url vacía" >&2
    usage
    exit 2
fi

# Campo de un JSON ya descargado. No usa jq (no está garantizado en el host) y no falla
# si el cuerpo no es JSON: devuelve cadena vacía y la guardia lo trata como `unknown`.
json_field() {
    local json="$1" key="$2"
    GA_JSON="$json" python3 - "$key" <<'PY'
import json, os, sys

try:
    data = json.loads(os.environ.get("GA_JSON", ""))
except Exception:
    data = {}

if isinstance(data, dict):
    value = data.get(sys.argv[1])
else:
    value = None

print("" if value is None else str(value))
PY
}

fetch_json() {
    local url="$1"
    curl -fsS --max-time 15 "$url"
}

BACKEND_URL="${BASE_URL}/api/v1/version"
FRONTEND_URL="${BASE_URL}/version.json"

if ! BACKEND_JSON="$(fetch_json "$BACKEND_URL")"; then
    echo "ERROR: no se pudo leer ${BACKEND_URL}" >&2
    echo "DEPLOYMENT_PARITY=FAIL"
    exit 1
fi

if ! FRONTEND_JSON="$(fetch_json "$FRONTEND_URL")"; then
    echo "ERROR: no se pudo leer ${FRONTEND_URL}" >&2
    echo "DEPLOYMENT_PARITY=FAIL"
    exit 1
fi

BACKEND_SHA="$(json_field "$BACKEND_JSON" git_sha | tr '[:upper:]' '[:lower:]')"
FRONTEND_SHA="$(json_field "$FRONTEND_JSON" git_sha | tr '[:upper:]' '[:lower:]')"
BACKEND_TIME="$(json_field "$BACKEND_JSON" build_time)"
FRONTEND_TIME="$(json_field "$FRONTEND_JSON" build_time)"

echo "SOURCE_SHA=${EXPECTED_SHA}"
echo "BACKEND_RUNTIME_SHA=${BACKEND_SHA}"
echo "FRONTEND_RUNTIME_SHA=${FRONTEND_SHA}"
echo "BACKEND_BUILD_TIME=${BACKEND_TIME}"
echo "FRONTEND_BUILD_TIME=${FRONTEND_TIME}"

is_unknown() {
    local sha="$1"
    [ -z "$sha" ] || [ "$sha" = "unknown" ]
}

if is_unknown "$BACKEND_SHA" || is_unknown "$FRONTEND_SHA"; then
    echo "DEPLOYMENT_PARITY=FAIL (unknown)"
    exit 2
fi

if [ "$BACKEND_SHA" = "$EXPECTED_SHA" ] && [ "$FRONTEND_SHA" = "$EXPECTED_SHA" ]; then
    echo "DEPLOYMENT_PARITY=PASS"
    exit 0
fi

# Paridad por árbol: ¿el artefacto del runtime es el mismo código que <sha_esperado> en la
# carpeta que lo construye? Solo aplica dentro de un repo git con ambos commits presentes.
tree_equal() {
    local runtime_sha="$1" tree_path="$2"

    [[ "$runtime_sha" =~ ^[0-9a-f]{7,40}$ ]] || return 1

    git rev-parse --git-dir >/dev/null 2>&1 || return 1
    git rev-parse --verify --quiet "${runtime_sha}^{commit}" >/dev/null 2>&1 || return 1
    git rev-parse --verify --quiet "${EXPECTED_SHA}^{commit}" >/dev/null 2>&1 || return 1

    git diff --quiet "$runtime_sha" "$EXPECTED_SHA" -- "$tree_path" >/dev/null 2>&1
}

PARITY_NOTE=""

BACKEND_PARITY=0
if [ "$BACKEND_SHA" = "$EXPECTED_SHA" ]; then
    BACKEND_PARITY=1
elif tree_equal "$BACKEND_SHA" "backend/"; then
    BACKEND_PARITY=1
    PARITY_NOTE="backend/"
fi

FRONTEND_PARITY=0
if [ "$FRONTEND_SHA" = "$EXPECTED_SHA" ]; then
    FRONTEND_PARITY=1
elif tree_equal "$FRONTEND_SHA" "frontend/"; then
    FRONTEND_PARITY=1
    if [ -n "$PARITY_NOTE" ]; then
        PARITY_NOTE="${PARITY_NOTE} y frontend/"
    else
        PARITY_NOTE="frontend/"
    fi
fi

if [ "$BACKEND_PARITY" -eq 1 ] && [ "$FRONTEND_PARITY" -eq 1 ]; then
    echo "DEPLOYMENT_PARITY=PASS (tree-equal: commits posteriores no tocan ${PARITY_NOTE})"
    exit 0
fi

if [ "$BACKEND_PARITY" -eq 0 ]; then
    echo "  backend: ${BACKEND_SHA} no es ${EXPECTED_SHA} y su árbol backend/ difiere" >&2
fi
if [ "$FRONTEND_PARITY" -eq 0 ]; then
    echo "  frontend: ${FRONTEND_SHA} no es ${EXPECTED_SHA} y su árbol frontend/ difiere" >&2
fi

echo "DEPLOYMENT_PARITY=FAIL"
exit 1
