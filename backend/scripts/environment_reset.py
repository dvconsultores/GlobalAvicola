#!/usr/bin/env python
"""Inventario y reset reproducible del entorno compartido de desarrollo/certificación.

Entregable de `GA-REM-025` (`AC01`, `AC11`, `AC15`).

    # inventariar, sin tocar nada
    python -m scripts.environment_reset --inventory

    # resetear
    GA_ALLOW_DESTRUCTIVE_RESET=1 \
    GA_RESET_ALLOWED_TARGETS=host/base \
    ENVIRONMENT=development \
    python -m scripts.environment_reset --reset --confirm-database base

Estrategia: **purga controlada**, no reconstrucción.

La reconstrucción (`DROP DATABASE` → `alembic upgrade`) sería más simple, pero exige
desconectar la aplicación y permisos de creación de bases que el usuario de la aplicación
no tiene por qué poseer. La purga se ejecuta en una sola transacción, conserva el esquema
y `alembic_version`, y deja el sistema exactamente donde estaba en cuanto a versión.

Nunca se invoca desde el arranque de la aplicación ni desde el despliegue. Es una orden
que una persona escribe a conciencia.
"""
from __future__ import annotations

import argparse
import asyncio
import os
import pathlib
import sys
from urllib.parse import urlparse

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from sqlalchemy import text  # noqa: E402
from sqlalchemy.ext.asyncio import create_async_engine  # noqa: E402

from scripts.data_classification import Categoria, borrable, clasificar  # noqa: E402
from scripts.reset_guard import ResetBloqueado, verificar  # noqa: E402


def _dsn() -> str:
    for clave in ("GA_RESET_DATABASE_URL", "DATABASE_URL"):
        valor = os.environ.get(clave)
        if valor:
            return valor
    fichero = pathlib.Path(__file__).resolve().parents[1] / ".env"
    if fichero.exists():
        for linea in fichero.read_text().splitlines():
            if linea.startswith("DATABASE_URL="):
                return linea.split("=", 1)[1].strip()
    raise SystemExit("[reset] No hay cadena de conexión. Declare DATABASE_URL.")


async def _tablas_reales(conn) -> list[str]:
    filas = await conn.execute(
        text(
            "SELECT tablename FROM pg_tables "
            "WHERE schemaname = current_schema() ORDER BY tablename"
        )
    )
    return [f[0] for f in filas]


async def _recuentos(conn, tablas: list[str]) -> dict[str, int]:
    salida: dict[str, int] = {}
    for tabla in tablas:
        filas = await conn.execute(text(f'SELECT count(*) FROM "{tabla}"'))
        salida[tabla] = filas.scalar_one()
    return salida


async def _dependencias_cruzadas(conn, a_borrar: set[str]) -> list[tuple[str, str]]:
    """Tablas **conservadas** que apuntan a una tabla que se va a borrar.

    Importa porque el `TRUNCATE` es `CASCADE`: si algo conservado dependiera de algo
    borrado, el `CASCADE` lo vaciaría también, en silencio. Si esta lista no está vacía,
    el reset se detiene antes de tocar nada.
    """
    filas = await conn.execute(
        text(
            """
            SELECT tc.table_name AS origen, ccu.table_name AS destino
            FROM information_schema.table_constraints tc
            JOIN information_schema.constraint_column_usage ccu
              ON tc.constraint_name = ccu.constraint_name
             AND tc.table_schema = ccu.table_schema
            WHERE tc.constraint_type = 'FOREIGN KEY'
              AND tc.table_schema = current_schema()
            """
        )
    )
    return sorted(
        {
            (origen, destino)
            for origen, destino in filas
            if origen not in a_borrar and destino in a_borrar
        }
    )


async def _comentario_base(conn, base: str) -> str | None:
    filas = await conn.execute(
        text("SELECT shobj_description(oid, 'pg_database') FROM pg_database WHERE datname = :d"),
        {"d": base},
    )
    fila = filas.first()
    return fila[0] if fila else None


def _informe(recuentos: dict[str, int]) -> None:
    por_categoria: dict[Categoria, list[tuple[str, int]]] = {}
    for tabla, n in sorted(recuentos.items()):
        por_categoria.setdefault(clasificar(tabla)[0], []).append((tabla, n))
    for categoria in Categoria:
        filas = por_categoria.get(categoria)
        if not filas:
            continue
        total = sum(n for _, n in filas)
        marca = "borrable" if categoria in {c for c in Categoria if borrable_cat(c)} else "conservada"
        print(f"\n  {categoria.value}  ({len(filas)} tablas · {total} filas · {marca})")
        for tabla, n in filas:
            if n:
                print(f"      {tabla:32s} {n:>8,}")
        vacias = [t for t, n in filas if not n]
        if vacias:
            print(f"      (vacías: {len(vacias)})")


def borrable_cat(categoria: Categoria) -> bool:
    from scripts.data_classification import BORRABLES

    return categoria in BORRABLES


async def _retirar_identidades(conn) -> tuple[int, int]:
    """Retira usuarios y empresas que no forman parte del baseline.

    Opt-in, nunca por omisión (§26 del encargo: «no borrar usuarios
    indiscriminadamente»). El reset normal conserva toda identidad, de modo que quien
    esté probando no se queda fuera; esta opción existe para la limpieza deliberada de
    cuentas de campañas antiguas que ya nadie usa.

    Se conserva siempre: el administrador del baseline y las dos empresas de
    certificación. Sin esa reserva, el borrado dejaría el sistema sin acceso posible.
    """
    from seeds.baseline_seeds import ADMIN, EMPRESAS_CERTIFICACION

    nombres = [e["name"] for e in EMPRESAS_CERTIFICACION]
    usuarios = await conn.execute(
        text("DELETE FROM users WHERE username <> :admin"), {"admin": ADMIN["username"]}
    )
    empresas = await conn.execute(
        text("DELETE FROM companies WHERE name <> ALL(:nombres)"), {"nombres": nombres}
    )
    return usuarios.rowcount or 0, empresas.rowcount or 0


async def ejecutar(
    reset: bool, base_confirmada: str | None, sembrar: bool, retirar_identidades: bool
) -> int:
    dsn = _dsn()
    motor = create_async_engine(dsn.replace("postgresql://", "postgresql+asyncpg://"), echo=False)
    try:
        async with motor.begin() as conn:
            reales = await _tablas_reales(conn)
            recuentos = await _recuentos(conn, reales)
            revision = recuentos.get("alembic_version")
            print(f"── Inventario · {len(reales)} tablas · alembic_version filas={revision} ──")
            _informe(recuentos)

            desconocidas = [t for t in reales if clasificar(t)[0] is Categoria.UNKNOWN]
            if desconocidas:
                print(f"\n  ⚠️  Sin clasificar, se conservan: {', '.join(desconocidas)}")

            a_borrar = {t for t in reales if borrable(t)}
            filas_a_borrar = sum(recuentos[t] for t in a_borrar)
            print(f"\n  Filas que el reset eliminaría: {filas_a_borrar:,} en {len(a_borrar)} tablas")

            if not reset:
                print("\n── Modo inventario. No se modificó nada. ──")
                return 0

            # `urlparse`, no un `split`: un DSN por socket unix lleva la ruta del
            # socket en la query y un corte por "/" devolvería ese directorio.
            base = urlparse(dsn).path.lstrip("/")
            comentario = await _comentario_base(conn, base)
            try:
                destino = verificar(dsn, base_confirmada=base_confirmada, comentario_base=comentario)
            except ResetBloqueado as exc:
                print(f"\n❌ RESET BLOQUEADO: {exc}")
                return 2
            print(f"\n  Guarda superada. Destino: {destino.identidad}")

            cruzadas = await _dependencias_cruzadas(conn, a_borrar)
            if cruzadas:
                print("\n❌ RESET ABORTADO. Tablas conservadas dependen de tablas a borrar;")
                print("   el CASCADE las vaciaría en silencio:")
                for origen, dest in cruzadas:
                    print(f"      {origen} → {dest}")
                return 3

            lista = ", ".join(f'"{t}"' for t in sorted(a_borrar))
            await conn.execute(text(f"TRUNCATE {lista} RESTART IDENTITY CASCADE"))
            print(f"\n  ✅ {len(a_borrar)} tablas vaciadas, secuencias reiniciadas")

            if retirar_identidades:
                usuarios, empresas = await _retirar_identidades(conn)
                print(f"  ✅ identidades retiradas: {usuarios} usuarios, {empresas} empresas")

        if sembrar:
            from sqlalchemy.ext.asyncio import async_sessionmaker

            from seeds.baseline_seeds import sembrar_baseline

            fabrica = async_sessionmaker(motor, expire_on_commit=False)
            async with fabrica() as sesion:
                await sembrar_baseline(sesion)

        async with motor.begin() as conn:
            despues = await _recuentos(conn, await _tablas_reales(conn))
            residuo = sum(n for t, n in despues.items() if borrable(t))
            print(f"\n── Verificación posterior: {residuo} filas de negocio ficticias restantes ──")
            _informe(despues)
            return 0 if residuo == 0 else 4
    finally:
        await motor.dispose()


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--inventory", action="store_true", help="solo inventariar, no modificar nada")
    p.add_argument("--reset", action="store_true", help="ejecutar la purga controlada")
    p.add_argument("--confirm-database", dest="confirmar", help="nombre exacto de la base, obligatorio con --reset")
    p.add_argument("--no-seed", action="store_true", help="no sembrar el baseline tras la purga")
    p.add_argument(
        "--purge-identities", dest="identidades", action="store_true",
        help="además, retirar usuarios y empresas ajenos al baseline (opt-in, §26)",
    )
    args = p.parse_args()
    if not (args.inventory or args.reset):
        p.error("indique --inventory o --reset")
    return asyncio.run(ejecutar(args.reset, args.confirmar, not args.no_seed, args.identidades))


if __name__ == "__main__":
    raise SystemExit(main())
