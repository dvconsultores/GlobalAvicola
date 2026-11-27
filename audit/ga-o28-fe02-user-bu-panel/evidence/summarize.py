"""Resume las corridas JSON de vitest de un directorio: por corrida y por test fallido."""
import json, sys, re, collections
from pathlib import Path
d = Path(sys.argv[1]); fallos = collections.Counter(); filas = []
for f in sorted(d.glob("run_*.json"), key=lambda p: int(re.findall(r"\d+", p.stem)[0])):
    j = json.loads(f.read_text())
    fail = []
    for tf in j["testResults"]:
        for a in tf["assertionResults"]:
            if a["status"] == "failed":
                msg = (a.get("failureMessages") or [""])[0].splitlines()[0][:110]
                log = (d / f"{f.stem}.log").read_text(errors="ignore")
                cargando = "common.loading" in log
                fail.append(f'{Path(tf["name"]).name} › {a["title"]} [{a.get("duration") or 0:.0f} ms] «{msg}» loading_en_DOM={cargando}')
                fallos[f'{Path(tf["name"]).name} › {a["title"]}'] += 1
    filas.append(f'{f.stem}: total={j["numTotalTests"]} passed={j["numPassedTests"]} failed={j["numFailedTests"]} skipped={j["numPendingTests"]+j.get("numTodoTests",0)}' + ("".join("\n    FAIL " + x for x in fail)))
print("\n".join(filas))
n = len(filas); ok = sum(1 for x in filas if " failed=0 " in x)
print(f"\nRESUMEN: {ok}/{n} corridas sin fallos")
for k, v in fallos.most_common(): print(f"  {v}× {k}")
