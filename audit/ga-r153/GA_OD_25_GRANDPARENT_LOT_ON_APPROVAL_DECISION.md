# GA-OD-25 · DECISIÓN DEL PROPIETARIO — LOTE DE ABUELAS AL APROBAR LA IMPORTACIÓN

**ID canónico: `OD-25`** (GA/OD; siguiente libre tras OD-24) · Fecha: 2026-09-12 · Tranche: GA-R153 · Estado: **RATIFIED** (implementación en curso; certificación técnica pendiente)

Decisión explícita del propietario: **B — AUTO-CREAR AL APROBAR, SIN POBLAR.**

## 1 · La pregunta resuelta

«Al completar la importación se crea automáticamente el lote de abuelas» (`docs/02 §3.4.2`; `spec.md §4.4`): ¿qué es «completar», con qué código/fecha/sexo nace, puebla o no, y convivencia con la vía manual?

## 2 · Regla de negocio canónica (ratificada)

1. **Disparador = aprobación de la importación** (gate P-07). No el registro, ni la llegada, ni el fin de cuarentena.
2. **Resultado:** exactamente **un** lote de Progenitoras por importación aprobada, creado **en la misma transacción** de la aprobación.
3. **Código:** automático `L-GP-{año}-{nn}` — año = fecha de llegada del plan; secuencia por empresa; unicidad salvaguardada (ver análisis de secuencia).
4. **Fecha de inicio:** fecha de llegada del plan. **Sexo:** del plan (♂/♀; ambos ⇒ `mixed`).
5. **Población: CERO** por la aprobación. La población sigue entrando **solo** por la recepción (`P-01` paso 4; BR-17/BR-18). La importación es documental (AC-R152-08 se preserva).
6. **Vía manual preservada** (`POST /lots`), ya no prerequisito de la importación nueva.
7. **Legado:** importaciones con lote preasignado no generan un segundo lote.
8. **Sin migración** (esquema actual suficiente: `lot_id` del evento nullable; campos del lote nullables).

## 3 · Impacto

- Finding dueño: **R-153** (no se crea R nuevo). Dependencia **R-152** (CLOSED) satisfecha.
- FVA-19 (38 filas): `OWNER_DECISION_REQUIRED` → `DECIDED_IMPLEMENTATION_PENDING` → (tras certificar) `FUNCTIONALLY_CERTIFIED_OWNER_ACCEPTANCE_PENDING` → (tras UAT) `FUNCTIONALLY_CERTIFIED_OWNER_ACCEPTED`.
- P-01: **no** se re-certifica por transitividad; regresión focalizada del paso afectado.
- P-07: intacto; la aprobación **agrega** la consecuencia del lote.

## 4 · Registro

- Paquete de decisión previo: `audit/final-frontend-audit/GA_AOD25_OWNER_DECISION_PACKET.md` (recomendación B).
- Respuesta del propietario: **B** (2026-09-12; autorización de formalizar + remediar + certificar).
- Paquete de implementación/certificación: `audit/ga-r153/`.
