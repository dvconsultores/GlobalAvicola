"""Guarda FAIL-CLOSED para el driver de sensibilidad (`MUTATION CHECKPOINT`).

Entregable de `GA-REM-002` enmienda E `T-002-E4` (WAVE B tranche 14).

Hermana de `scripts/reset_guard.py` y de `tests/environment_guard.py`: aquéllas protegen el
borrado de datos y la ejecución de la suite; ésta protege el **código de producción** durante la
sensibilidad.

Por qué existe. El driver de mutaciones instala un cambio deliberado en un archivo productivo,
corre la prueba que debería enrojecer y **restaura con `git checkout -- <archivo>`**. Esa
restauración devuelve el archivo al estado de `HEAD`. Si la implementación aún no está
confirmada, `HEAD` es el commit **anterior** y la restauración **borra la implementación**, en
silencio y sin error. Ocurrió en el tranche 10 y volvió a ocurrir en el 13.

    UNA INSTRUCCIÓN ESCRITA NO ES UNA GARANTÍA. LA GARANTÍA ES UNA PRECONDICIÓN EJECUTABLE.

Siete señales independientes; **todas** deben ser favorables:

    1. `IMPLEMENTATION_COMMIT` está declarado.
    2. Ese commit existe y es resoluble en el repositorio.
    3. `git rev-parse HEAD` es exactamente ese commit.
    4. El árbol de trabajo **productivo** está limpio (sin cambios sin confirmar).
    5. Cada archivo que se va a mutar existe en ese commit (el objetivo de restauración es válido).
    6. El objetivo de restauración se declara explícitamente, no se hereda de `HEAD`.
    7. Tras restaurar, el archivo vuelve a ser byte a byte el del commit de implementación.

Ante cualquier fallo: `ABORTAR`. Nunca avisar y continuar; nunca `--force`.

Uso desde el driver:

    from scripts.mutation_guard import GuardaDeMutacion
    guarda = GuardaDeMutacion(raiz, implementation_commit, rutas_a_mutar)
    guarda.exigir()                     # antes de instalar la primera mutación
    ...
    guarda.exigir_restauracion(ruta)    # después de restaurar cada una
"""
from __future__ import annotations

import subprocess
from dataclasses import dataclass, field
from pathlib import Path

#: Prefijos cuyo contenido es **código de producción**: lo que una restauración equivocada destruye.
RUTAS_PRODUCTIVAS: tuple[str, ...] = ("backend/app/", "frontend/src/", "backend/alembic/")


class MutacionNoPermitida(RuntimeError):
    """El driver de sensibilidad no puede ejecutarse. Abortar; no degradar a aviso."""


@dataclass
class GuardaDeMutacion:
    raiz: Path
    implementation_commit: str
    rutas: tuple[str, ...] = ()
    _motivos: list[str] = field(default_factory=list)

    def _git(self, *args: str) -> tuple[int, str]:
        p = subprocess.run(["git", "-C", str(self.raiz), *args], capture_output=True, text=True)
        return p.returncode, (p.stdout or p.stderr).strip()

    def _git_bruto(self, *args: str) -> str:
        """Salida **sin recortar**: `git status --porcelain` codifica el estado en las dos primeras
        columnas, y recortar la primera línea desplazaría la ruta."""
        p = subprocess.run(["git", "-C", str(self.raiz), *args], capture_output=True, text=True)
        return p.stdout

    # ── las siete señales ──────────────────────────────────────────────────

    def evaluar(self) -> list[str]:
        """Devuelve la lista de motivos por los que **no** se puede mutar. Vacía = permitido."""
        self._motivos = []
        sha = (self.implementation_commit or "").strip()
        if not sha:
            self._motivos.append("1. IMPLEMENTATION_COMMIT no está declarado")
            return self._motivos  # sin commit declarado, las demás señales no son evaluables

        codigo, resuelto = self._git("rev-parse", "--verify", f"{sha}^{{commit}}")
        if codigo != 0:
            self._motivos.append(f"2. IMPLEMENTATION_COMMIT no existe en el repositorio: {sha}")
            return self._motivos

        _, cabeza = self._git("rev-parse", "HEAD")
        if cabeza != resuelto:
            self._motivos.append(f"3. HEAD ({cabeza[:7]}) no es el commit de implementación ({resuelto[:7]}): "
                                 "restaurar devolvería el código a otro estado")

        estado = self._git_bruto("status", "--porcelain")
        sucios = []
        for linea in estado.splitlines():
            if not linea or linea.startswith("??"):
                continue  # lo no versionado no puede ser destruido por una restauración
            ruta = linea[3:].strip().split(" -> ")[-1].strip('"')
            if ruta.startswith(RUTAS_PRODUCTIVAS):
                sucios.append(ruta)
        if sucios:
            self._motivos.append("4. hay código de producción sin confirmar: " + ", ".join(sorted(sucios)))

        for ruta in self.rutas:
            if self._git("cat-file", "-e", f"{resuelto}:{ruta}")[0] != 0:
                self._motivos.append(f"5. el archivo a mutar no existe en el commit de implementación: {ruta}")
        return self._motivos

    def exigir(self) -> str:
        """Precondición del driver. Devuelve el `sha` resuelto o aborta."""
        motivos = self.evaluar()
        if motivos:
            raise MutacionNoPermitida("MUTACIÓN NO PERMITIDA:\n  - " + "\n  - ".join(motivos))
        return self._git("rev-parse", "HEAD")[1]

    # ── señales 6 y 7: la restauración es explícita y se comprueba ─────────

    def restaurar(self, ruta: str) -> None:
        """Restaura **desde el commit de implementación declarado**, no desde `HEAD`.

        La diferencia es justamente el fallo histórico: `git checkout -- <ruta>` toma `HEAD`, que
        puede no ser lo que el operador cree.
        """
        codigo, salida = self._git("checkout", self.implementation_commit, "--", ruta)
        if codigo != 0:
            raise MutacionNoPermitida(f"6. no se pudo restaurar {ruta} desde {self.implementation_commit}: {salida}")
        self._git("reset", "--quiet", "HEAD", "--", ruta)

    def exigir_restauracion(self, ruta: str) -> None:
        """Comprueba que el archivo es byte a byte el del commit de implementación."""
        codigo, esperado = self._git("show", f"{self.implementation_commit}:{ruta}")
        if codigo != 0:
            raise MutacionNoPermitida(f"7. no hay objetivo de restauración para {ruta}")
        actual = (self.raiz / ruta).read_text()
        if actual.rstrip("\n") != esperado.rstrip("\n"):
            raise MutacionNoPermitida(f"7. {ruta} NO volvió al commit de implementación: residuo tras la mutación")

    def informe(self) -> str:
        motivos = self.evaluar()
        _, cabeza = self._git("rev-parse", "HEAD")
        codigo, resuelto = self._git("rev-parse", "--verify", f"{(self.implementation_commit or '').strip()}^{{commit}}")
        lineas = [f"IMPLEMENTATION_COMMIT ..... {resuelto if codigo == 0 else self.implementation_commit or '(no declarado)'}",
                  f"HEAD ...................... {cabeza}",
                  f"COINCIDEN ................. {'SÍ' if codigo == 0 and cabeza == resuelto else 'NO'}",
                  f"CÓDIGO PRODUCTIVO LIMPIO .. {'SÍ' if not any(m.startswith('4.') for m in motivos) else 'NO'}",
                  f"OBJETIVO DE RESTAURACIÓN .. {'VÁLIDO' if not any(m.startswith('5.') for m in motivos) else 'INVÁLIDO'}",
                  f"MUTACIÓN PERMITIDA ........ {'SÍ' if not motivos else 'NO'}"]
        if motivos:
            lineas += ["MOTIVOS:"] + [f"  - {m}" for m in motivos]
        return "\n".join(lineas)
