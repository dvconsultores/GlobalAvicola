#!/usr/bin/env bash
# O-28 · campaña de estabilidad (§16-18). Uso: stability.sh <prefijo: post|post_mut>
EV=/home/maria/Proyectos/GlobalAvicola/audit/ga-o28-fe02-user-bu-panel/evidence
P=$1; ST="$EV/stability_$P.txt"; C="$EV/campaign.sh"
export PATH=$HOME/.nvm/versions/node/v20.20.2/bin:$PATH
echo "HEAD=$(git -C /home/maria/Proyectos/GlobalAvicola rev-parse --short HEAD) dirty=$(git -C /home/maria/Proyectos/GlobalAvicola status --short | grep -vc '^??') $(date -Iseconds) carga=$(cut -d' ' -f1-3 /proc/loadavg)" > "$ST"
bash "$C" "${P}_archivo" 20 file > /dev/null; grep RESUMEN "$EV/runs/${P}_archivo/summary.txt" | sed 's/^/archivo /' >> "$ST"
bash "$C" "${P}_spec013" 10 suite > /dev/null; grep RESUMEN "$EV/runs/${P}_spec013/summary.txt" | sed 's/^/spec013 /' >> "$ST"
bash "$C" "${P}_full" 3 full > /dev/null; grep RESUMEN "$EV/runs/${P}_full/summary.txt" | sed 's/^/full /' >> "$ST"
cd /home/maria/Proyectos/GlobalAvicola/frontend
npx tsc -b > "$EV/frontend_tsc_$P.log" 2>&1; echo "tsc rc=$?" >> "$ST"
npx vite build > "$EV/frontend_build_$P.log" 2>&1; echo "build rc=$?" >> "$ST"
echo "FIN $(date -Iseconds)" >> "$ST"
