#!/usr/bin/env bash
# GA-REM-043 — prompt oculto y ejecución única dentro del backend desplegado.
set -Eeuo pipefail

COMPOSE_FILE="${COMPOSE_FILE:-avicola.yml}"
BACKEND_SERVICE="${BACKEND_SERVICE:-backend}"

if (($# != 0)); then
  echo "Uso: COMPOSE_FILE=avicola.yml $0" >&2
  echo "La contraseña nunca se acepta como argumento." >&2
  exit 64
fi

command -v docker >/dev/null 2>&1 || {
  echo "ERROR: docker no está disponible" >&2
  exit 69
}

read -r -s -p "Contraseña temporal fuerte para admin: " first_password
echo
read -r -s -p "Repita la contraseña temporal: " second_password
echo

if [[ -z "$first_password" ]]; then
  echo "ERROR: la contraseña no puede estar vacía" >&2
  exit 65
fi
if [[ "$first_password" != "$second_password" ]]; then
  echo "ERROR: las contraseñas no coinciden" >&2
  exit 65
fi

export GA_FIRST_SUPERUSER_PASSWORD="$first_password"
unset first_password second_password
trap 'unset GA_FIRST_SUPERUSER_PASSWORD' EXIT

docker compose -f "$COMPOSE_FILE" exec -T \
  -e GA_FIRST_SUPERUSER_PASSWORD \
  "$BACKEND_SERVICE" \
  python -m scripts.bootstrap_first_superuser
