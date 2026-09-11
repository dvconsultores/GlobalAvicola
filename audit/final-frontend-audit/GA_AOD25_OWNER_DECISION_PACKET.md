# AOD-25 · PAQUETE DE DECISIÓN DEL PROPIETARIO — CREACIÓN AUTOMÁTICA DEL LOTE DE ABUELAS

Capacidad: **FVA-19 / CAP-BU-04** · Finding: **R-153** (depende de R-152, ya cerrado) · Prioridad: **P3** (verificada; lista Wave B) · Fecha: 2026-09-11 · RFC: `AUDIT_OWNER_DECISIONS_REQUIRED.md:94`, `REMEDIATION_BACKLOG.md:944`, `docs/02 §3.4.2`, `spec.md §4.4`.

## 1 · Qué dice la fuente (canónico)

- `docs/02 §3.4.2`: «Al completar la importación, se crea automáticamente el lote de abuelas». `spec.md §4.4`: «Creación de lote de abuelas vinculado a granja/galpón».
- **Hoy no ocurre**: completar la importación no crea ningún lote; el lote de abuelas se crea manualmente (`POST /lots`) y la importación exige lote existente.
- Ambigüedad registrada: (a) ¿qué es «completar»? (b) ¿código/fecha/sexo del lote? (c) ¿la importación **puebla** el lote con las recibidas? (d) ¿se conserva la vía manual?
- La vía de población certificada es `bird_reception` (P-01 paso 4; BR-17/BR-18) — cualquier opción que «pueble» toca ese contrato y el modelo de saldo.

## 2 · Opciones

**OPCIÓN A — Sin auto-creación (ratificar estado actual).**
- Negocio: la importación no produce lote; el operador crea el lote de abuelas manualmente cuando corresponde.
- Efecto: `docs/02 §3.4.2` queda **descartado explícitamente** como contrato; R-153 se cierra sin código.
- Impacto: cero producto. Riesgo: la frase de la spec queda muerta (deuda documental a anotar).

**OPCIÓN B — Auto-creación al aprobar (P-07), sin poblar; ambas vías.**
- Disparador: **aprobación** de la importación (gate P-07, ya certificado). Código: **secuencia por empresa** derivada (`L-GP-{año}-{nn}`), fecha de inicio = llegada del plan, sexo del plan.
- Población: **no puebla** — el paso 4 (`bird_reception`, certificado) sigue entrando la población; importación y lote quedan vinculados.
- Vía manual conservada para casos sin importación vinculada.
- Impacto: SPEC propia pequeña (disparador/código/vínculo) + tests; sin re-certificar saldos (RR-17 intacto).

**OPCIÓN C — Auto-creación al aprobar y POBLAR con recibidas netas.**
- El paso 4 desaparece o se convierte en distribución; la importación produce saldo directamente.
- Impacto: toca el modelo de saldo certificado (R-130, BR-17/18) → SPEC mayor + re-certificación de P-01; riesgo alto, beneficio marginal (la recepción ya funciona).

## 3 · Recomendación

**OPCIÓN B** — cumple la promesa de `docs/02 §3.4.2` sin duplicar población ni reabrir contratos certificados; usa un disparador ya gobernado (P-07); el código por secuencia evita códigos manuales divergentes.

## 4 · Decisión solicitada

**A)** Sin auto-creación (ratificar manual) · **B)** Auto-crear al aprobar, sin poblar (recomendada) · **C)** Auto-crear y poblar (re-certificación de P-01).

**RESPONDA SOLO: A / B / C** — formalización posterior; si B/C: finding→SPEC→AC (sin implementación en este paso); si A: cierre documental de R-153.
