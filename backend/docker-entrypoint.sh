#!/bin/sh
# ============================================================
# GA-REM-024 — las migraciones se aplican antes de servir.
#
# El arranque era `uvicorn` directo: un contenedor nuevo empezaba a atender peticiones con
# el codigo nuevo contra el esquema viejo. La auditoria lo habia registrado como
# `GA-TD-013`; la Wave 2 lo convirtio en bloqueante al producir dos migraciones de esquema
# y una de datos que de otro modo nunca llegarian a produccion.
#
# Esto NO altera la estrategia de despliegue (`EX-01`): Watchtower sigue vigilando
# `:latest` con `pull_policy: always` y recreando el contenedor igual que antes. Lo unico
# que cambia es lo que el contenedor hace en su primer segundo de vida, que es
# responsabilidad de la imagen.
# ============================================================
set -e

# Propietario de las migraciones: este entrypoint, y solo este. Ni los workflows de CI ni
# un operador por consola deben aplicarlas en el flujo normal. Ver
# `audit/remediation/PRODUCTION_ACTIVATION_RUNBOOK.md`.
echo "[entrypoint] Starting database migrations"

# El DSN no se imprime: contiene credenciales. Solo el destino, para poder diagnosticar
# un arranque contra la base equivocada sin filtrar el secreto.
echo "[entrypoint] target: $(python -c "
import os, urllib.parse as u
p = u.urlsplit(os.environ.get('DATABASE_URL', ''))
print(f'{p.hostname or \"local\"}/{(p.path or \"/?\").lstrip(\"/\")}')
" 2>/dev/null || echo 'desconocido')"

# `set -e` hace que un fallo aqui termine el script sin alcanzar el `exec`: si la
# migracion falla, el contenedor **no sirve**. Servir con el esquema equivocado corrompe
# datos; caerse ruidosamente y dejar que `restart: unless-stopped` reintente es preferible
# y visible.
alembic upgrade head

echo "[entrypoint] Migration completed"
echo "[entrypoint] Starting application: $*"

# `exec` reemplaza al shell: el proceso servidor hereda el PID 1 y recibe SIGTERM
# directamente, de modo que `docker stop` sigue siendo un apagado limpio.
exec "$@"
