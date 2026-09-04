"""
GA-REM-014 — Gestión del PostgreSQL de pruebas en espacio de usuario.

En esta máquina no hay PostgreSQL del sistema, ni Docker, y `sudo` exige
contraseña. Se resuelve con `pgserver`, que empaqueta binarios oficiales de
PostgreSQL y permite ejecutar una instancia **completamente aislada bajo el
usuario actual**, sin privilegios y sin tocar ninguna configuración global.

    PGDATA:  ~/.local/share/global_avicola_test_pg
    Base:    global_avicola_test
    Rol:     global_avicola_test_user

Nada de esto comparte host, puerto, socket, rol ni base con producción.

Uso:
    python -m scripts.test_db start   # arranca y crea base/rol si faltan
    python -m scripts.test_db dsn     # imprime el DSN asyncpg
    python -m scripts.test_db reset   # recrea la base vacía
    python -m scripts.test_db stop    # detiene la instancia
    python -m scripts.test_db status
"""
from __future__ import annotations

import os
import pathlib
import secrets
import sys

PGDATA = pathlib.Path(
    os.environ.get("GA_TEST_PGDATA", pathlib.Path.home() / ".local/share/global_avicola_test_pg")
)
#: Base para el camino de instalacion NUEVA (`PATH A`).
DB_NAME = "global_avicola_test"
#: Base para el camino de ACTUALIZACION de una instalacion existente (`PATH B`).
#: Vive aparte a proposito: una base recien creada no demuestra que produccion pueda
#: actualizarse, y mezclarlas haria imposible distinguir un camino del otro.
UPGRADE_DB_NAME = "global_avicola_upgrade_test"
DB_ROLE = "global_avicola_test_user"
PWD_FILE = PGDATA / ".test_role_password"

#: Nombres que jamás pueden aparecer aquí. Defensa redundante frente a
#: `tests/environment_guard.py`.
FORBIDDEN = {"avicolav2", "avicola", "globalavicola", "postgres"}


def _server(persistent: bool = True):
    import pgserver

    PGDATA.mkdir(parents=True, exist_ok=True)
    return pgserver.get_server(PGDATA, cleanup_mode=None if persistent else "stop")


def _role_password() -> str:
    if PWD_FILE.exists():
        return PWD_FILE.read_text().strip()
    pwd = secrets.token_urlsafe(24)
    PWD_FILE.write_text(pwd)
    PWD_FILE.chmod(0o600)
    return pwd


def dsn(db_name: str = DB_NAME) -> str:
    """DSN asyncpg contra el socket unix de la instancia de pruebas."""
    assert db_name not in FORBIDDEN, "nombre de base prohibido"
    assert db_name.endswith("_test"), "solo bases de prueba"
    return (
        f"postgresql+asyncpg://{DB_ROLE}:{_role_password()}@/{db_name}"
        f"?host={PGDATA}"
    )


def start() -> str:
    srv = _server()
    pwd = _role_password()
    existe_rol = "1" in srv.psql(
        f"SELECT 1 FROM pg_roles WHERE rolname='{DB_ROLE}';"
    )
    if not existe_rol:
        srv.psql(f"CREATE ROLE {DB_ROLE} LOGIN PASSWORD '{pwd}';")
    else:
        srv.psql(f"ALTER ROLE {DB_ROLE} WITH PASSWORD '{pwd}';")
    for nombre in (DB_NAME, UPGRADE_DB_NAME):
        if nombre not in srv.psql(
            f"SELECT datname FROM pg_database WHERE datname='{nombre}';"
        ):
            srv.psql(f"CREATE DATABASE {nombre} OWNER {DB_ROLE};")
    return dsn()


def reset(db_name: str = DB_NAME) -> str:
    """Recrea la base vacía. Solo afecta a bases de prueba."""
    srv = _server()
    assert db_name not in FORBIDDEN
    assert db_name.endswith("_test"), "solo bases de prueba"
    srv.psql(f"DROP DATABASE IF EXISTS {db_name} WITH (FORCE);")
    srv.psql(f"CREATE DATABASE {db_name} OWNER {DB_ROLE};")
    return dsn(db_name)


def stop() -> None:
    import pgserver

    srv = pgserver.get_server(PGDATA, cleanup_mode=None)
    srv.cleanup()


def status() -> str:
    srv = _server()
    return srv.psql(
        "SELECT current_database(), version();"
    )


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "status"
    # Segundo argumento opcional: `upgrade` selecciona la base del camino de
    # actualizacion en lugar de la de instalacion nueva.
    nombre = UPGRADE_DB_NAME if len(sys.argv) > 2 and sys.argv[2] == "upgrade" else DB_NAME
    if cmd == "start":
        print(start())
    elif cmd == "dsn":
        print(dsn(nombre))
    elif cmd == "reset":
        print(reset(nombre))
    elif cmd == "stop":
        stop()
        print("instancia de pruebas detenida")
    elif cmd == "status":
        print(status())
    else:
        sys.exit(f"comando desconocido: {cmd}")
