# GA-BU-D10 · CHECKLIST (AC → tarea → test → evidencia → estado)

Cobertura AC01-AC25. Estados: [x] hecho · [ ] pendiente.

| AC | Tarea | Test | Evidencia runtime | Estado |
|---|---|---|---|---|
| AC01 OD-23 canonizada | T01 | doc | — | [x] |
| AC02 BU OFF sin acceso (nadie) | T10 | suite R-188 L2 + OD-16 | E2E-02 | [ ] |
| AC03 global no evade OFF | T10 | OD-16 suite | E2E-11 | [ ] |
| AC04 concesión ≠ habilitación | T10 | suite (conceder con OFF rechaza) | E2E-08 | [ ] |
| AC05 re-encendido sin efectividad automática | T10 | suite R-188 L5 | E2E-04 (RED→GREEN) | [ ] |
| AC06 zero-BU ⊂ CORE | T11 | suite | E2E-10 | [ ] |
| AC07 RBAC exigido | T11 | suite | E2E-09 | [ ] |
| AC08 cross-company DENY | T11 | suite | E2E-08 | [ ] |
| AC09 self-grant DENY | T11 | suite OD-15 | E2E-07 | [ ] |
| AC10 transferencia PRESERVADA | T12 | suites AC-B08/B12 | regresión runtime (modelo; sin API viva — declarado) | [ ] |
| AC11 /me efectivas coherente | T10 | suite | E2E-03/04 | [ ] |
| AC12 navegación = efectivo | T11 | Vitest GA-FE-03 | E2E UI desktop/móvil | [ ] |
| AC13 API directa = UI | T11 | — | E2E-03/04 (deep link + API) | [ ] |
| AC14 refresh token sin acceso obsoleto | T10 | — | E2E-06 | [ ] |
| AC15 relogin estable | T10 | — | E2E-06 | [ ] |
| AC16 auditoría correcta (§12) | T10 | suite (auditoría ×N causa) | E2E-audit (lectura /audit) | [ ] |
| AC17 sin fuga cross-tenant | T11 | suite | E2E-08/11 | [ ] |
| AC18 GA-FE-02 preservado | T12 | Vitest | spot GA-FE-02 | [ ] |
| AC19 GA-FE-03 preservado | T12 | Vitest | UI nav | [ ] |
| AC20 GA-FE-04 preservado | T12 | Vitest | spot | [ ] |
| AC21 GA-FE-05..07 preservados | T12 | Vitest | spots | [ ] |
| AC22 R-181/182/184/185/186/187·OD-21/22 | T12 | Vitest 280 | sin superficies tocadas | [ ] |
| AC23 históricas consultables | T10 | suite (fila queda, revoked_at) | E2E-ledger/audit | [ ] |
| AC24 idempotencia normalizadora | T10 | suite | E2E-02b | [ ] |
| AC25 sin migración/borrado masivo | T10 | revisión | — | [ ] |

Sin AC huérfano. «Evidencia runtime» se completa en C4 (o se marca N/A con motivo).
