#!/usr/bin/env bash
# O-28 · reproducción ANTES del fix (§4 A..F). Secuencial: nunca dos vitest en paralelo.
EV=/home/maria/Proyectos/GlobalAvicola/audit/ga-o28-fe02-user-bu-panel/evidence
C="$EV/campaign.sh"
echo "HEAD=$(git -C /home/maria/Proyectos/GlobalAvicola rev-parse --short HEAD) $(date -Iseconds) carga=$(cut -d' ' -f1-3 /proc/loadavg)" > "$EV/repro_status.txt"
i=0
while IFS= read -r t; do i=$((i+1)); bash "$C" "pre_A_individual_$i" 3 tests "$t" > /dev/null; echo "A$i $t" >> "$EV/repro_status.txt"; done <<'LIST'
muestra identidad, y EMPRESA vs USUARIO
conceder llama POST exacto
revocar pide confirmación
sobre uno mismo
fallo al cargar concesiones
sin business_units:read
AC-UI-01
AC-UI-02
AC-UI-03
AC-UI-04
LIST
bash "$C" pre_B_archivo 10 file > /dev/null; echo B >> "$EV/repro_status.txt"
bash "$C" pre_F_shuffle 10 shuffle > /dev/null; echo F >> "$EV/repro_status.txt"
bash "$C" pre_C_spec013 3 suite > /dev/null; echo C >> "$EV/repro_status.txt"
bash "$C" pre_D_full 2 full > /dev/null; echo D >> "$EV/repro_status.txt"
echo "FIN $(date -Iseconds)" >> "$EV/repro_status.txt"
