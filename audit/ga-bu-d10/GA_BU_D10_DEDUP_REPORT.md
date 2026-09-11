# GA-BU-D10 · DEDUP DE GOBERNANZA

Pregunta del dedup (§18): ¿BU-D10 sigue siendo una decisión de propietario genuinamente **irresuelta**, o ya está resuelta en otra decisión/finding canónico?

## 1 · Barrido

| Candidato | Relación | ¿La resuelve? |
|---|---|---|
| `OD-09` (control-plane vs BU; `.d` empresa-scoped; `.e` marca-no-borra; transferencia) | Origen del régimen de concesiones; `.e` resuelve **otro ciclo** (cambio de empresa) | **NO** — no se pronuncia sobre apagar/encender la línea en la misma empresa |
| `OD-10` (handoff entre cadenas) | Traspaso despacho→recepción | **NO** — otro ciclo |
| `OD-14` | (nota de datos/versión; sin relación con concesiones) | **NO** |
| `OD-15` (Administrador de Accesos; `.a` self-grant; §6 permisos exactos) | Control-plane; quién concede | **NO** — regula el acto de conceder, no la vida de la concesión al apagar la línea |
| `OD-16` (+`.e`) | Activación por empresa **absoluta** para acceso productivo; **reserva expresa**: deja BU-D10 separada a propósito | **NO la resuelve; la preserva como pendiente** |
| `GA-REM-040 §6.3` · `AC-A04`/`AC-A05`/`AC-A06` | Comportamiento provisional **documentado como provisional** («razón de que BU-D10 siga abierta») | **NO** — es la conducta actual, no la ratificación |
| `R-98` / `R-113` / `R-121` / `R-128` | Cerrados vía `OD-13`/`OD-15` (rol admin, self-grant, aislamiento) | **NO** — distinta pregunta |
| `R-163` | Guarda de **escritura** productiva (habilitación absoluta al escribir) | **NO** — independiente del re-encendido |
| `R-185`/`OD-21` (referencias inactivas), `R-187`/`OD-22` (escala IPE) | Ajenos | **NO** |
| `BU-D03…BU-D08` (matriz 12 decisiones) | Otras sub-decisiones BU, ninguna toca apagar/encender | **NO** |
| `AUDIT_OWNER_DECISIONS_REQUIRED.md` | Registro: `BU-D10` «no se toca», `PENDING_RATIFICATION` | Confirma la pendencia |

## 2 · Comprobación de que el registro no la renumera

- Registro OD vigente: `OD-01…OD-22` (GA lineage) + familia `AOD-*` (Wave B, registro separado). `BU-D10` **no tiene** OD asignada en ningún registro; es candidata a la **siguiente OD libre de la línea GA tras la decisión** (se inspeccionará el registro en ese momento; no se asume el número aquí).
- `AUDIT_OWNER_DECISIONS_REQUIRED.md` la mantiene como fila propia fuera de `AOD-nn` (instrucción expresa «no se resuelve aquí»).

## 3 · Veredicto del dedup

**GENUINE_OWNER_DECISION_UNRESOLVED.** BU-D10 es la última decisión funcional BU pendiente; no está resuelta por evidencia porque es una **elección de política** (continuidad vs mínimo privilegio) con dos opciones coherentes:

- no hay fuente de nivel 1-4 que se pronuncie por A o B;
- OD-16.e la reservó expresamente;
- el código documenta que su conducta es provisional y reversible precisamente para **no** responder por omisión.

**No procede crear finding ni implementar nada antes de la decisión** (patrón de gobernanza del programa: OBSERVACIÓN → OD → brecha → SPEC). Tras la decisión: si A ⇒ probablemente `IMPLEMENTATION_GAP: NONE` (reconciliación + recertificación sin código); si B ⇒ brecha real (auto-reactivación actual) ⇒ RED + implementación + UAT.
