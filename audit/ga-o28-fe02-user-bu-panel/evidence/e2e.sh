#!/usr/bin/env bash
# O-28 · E2E relevantes (usuarios/roles/unidades) y E2E completa --workers=1, con saneo.
RAIZ=/home/maria/Proyectos/GlobalAvicola; EV="$RAIZ/audit/ga-o28-fe02-user-bu-panel/evidence"; ST="$EV/e2e_status.txt"
sanea() { sed -E 's#postgres(ql)?(\+[a-z]+)?://[^ "]+#<DSN>#g; s#(password|PASSWORD|token|TOKEN)=[^ ]+#\1=<REDACTED>#g; s/Bearer eyJ[A-Za-z0-9._-]*/Bearer [REDACTADO]/g'; }
cd "$RAIZ"
echo "HEAD=$(git rev-parse --short HEAD) $(date -Iseconds)" > "$ST"
bash scripts_e2e.sh --workers=1 e2e/proceso-p17-admin-rbac-permisos-y-unidades.spec.ts e2e/proceso-p17b-admin-rbac-usuario-y-clave.spec.ts e2e/proceso-p17c-admin-rbac-sesion-y-consistencia.spec.ts e2e/proceso-p17d-admin-rbac-consistencia-ui-api.spec.ts e2e/proceso-p17e-usuarios-s2-rol-sin-clave.spec.ts e2e/proceso-p18c-uat-s1-bu-e-identidad.spec.ts 2>&1 | sanea > "$EV/e2e_relevantes.log"; echo "relevantes rc=${PIPESTATUS[0]}" >> "$ST"
bash scripts_e2e.sh --workers=1 2>&1 | sanea > "$EV/e2e_full.log"; echo "full rc=${PIPESTATUS[0]}" >> "$ST"
echo "FIN $(date -Iseconds)" >> "$ST"
