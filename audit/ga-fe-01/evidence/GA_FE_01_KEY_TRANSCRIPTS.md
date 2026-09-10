# GA-FE-01 · TRANSCRIPCIONES CLAVE (evidencia cruda)

Recopilado durante la ejecución del 2026-09-10. Cada bloque es salida literal de terminal
(tuberías de formato indicadas cuando las hay).

## T-01 · RED vivo en baseline (sin tubería, `frontend/`)

```
$ rm -f node_modules/.tmp/tsconfig.app.tsbuildinfo node_modules/.tmp/tsconfig.node.tsbuildinfo
$ npx tsc -b --noEmit; echo $?
src/pages/audit/AuditPage.tsx(3,18): error TS6133: 'User' is declared but its value is never read.
src/pages/audit/AuditPage.tsx(3,24): error TS6133: 'Database' is declared but its value is never read.
src/pages/lots/LotFormPage.tsx(47,9): error TS6133: 'areas' is declared but its value is never read.
src/pages/lots/LotFormPage.tsx(47,16): error TS6133: 'setAreas' is declared but its value is never read.
src/pages/lots/LotFormPage.tsx(85,47): error TS2493: Tuple type '[…4…]' of length '4' has no element at index '4'.
src/pages/lots/LotFormPage.tsx(85,47): error TS6133: 'areaRes' is declared but its value is never read.
$ echo $?
2

$ npm run build; echo $?
> tsc -b && vite build   ← muere en tsc (exit 2); vite nunca se alcanza

$ npx vite build; echo $?
✓ built in 990ms
exit 0
```

## T-02 · Gates post-fix (sin tubería)

```
$ rm -f node_modules/.tmp/tsconfig.*.tsbuildinfo && npx tsc -b --noEmit; echo $?
0                                    ← SIN SALIDA: 0 errores (6 → 0)

$ npx vite build; echo $?
exit 0   (vite v8.1.0 · 987 módulos)

$ npm run build; echo $?
exit 0

$ rm -rf dist && npm run build; echo $?
exit 0   (reduplicación en limpio; hash idéntico)

$ npx vitest run
Test Files  12 passed (12)
     Tests  108 passed (108)
exit 0
```

## T-03 · Fingerprints

```
ENTRY runtime:
  Last-Modified: Sat, 05 Sep 2026 14:09:27 GMT
  ETag: "6a9c2297-322"
  assets/index-D5dwMXuP.js  sha256 4eb822a5…c64be  1 235 292 bytes

LOCAL build (post-fix):
  dist/assets/index-kzREeQp6.js  sha256 4b6a6a04…4038b9  1 275 424 bytes
  dist/assets/index-CgiG0VY8.css                         86 677 bytes
  dist/index.html                sha256 909ea073…f7bc4
```

## T-04 · Diff de implementación (literal, `git --no-pager diff`)

```
-import { Shield, User, Database, RotateCcw } from 'lucide-react'
+import { Shield, RotateCcw } from 'lucide-react'

- const [areas, setAreas] = useState<SelectOption[]>([])
- const [farmRes, houseRes, lineRes, breedRes, areaRes] = await Promise.allSettled([
+ const [farmRes, houseRes, lineRes, breedRes] = await Promise.allSettled([
```

(2 archivos · +2 −3 · ningún otro archivo tocado; `git diff` de tsconfig*/package*/Dockerfile = 0 líneas.)

## T-05 · Nota de reproducibilidad del replay

`4386f87` y `950bb21` se midieron en worktrees temporales `/tmp` (nodos_modules por enlace
simbólico, sin tocar lockfiles), con `tsconfig.*.tsbuildinfo` eliminado antes de cada corrida, y
los worktrees fueron retirados al finalizar (`git worktree list` → solo el árbol principal).
