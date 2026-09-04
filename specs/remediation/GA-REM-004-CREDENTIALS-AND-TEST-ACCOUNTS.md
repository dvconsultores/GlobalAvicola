# GA-REM-004 — CREDENCIALES Y CUENTAS DE PRUEBA

## Metadata
| Campo | Valor |
|---|---|
| **ID** | `GA-REM-004` · **Tipo** `SECURITY SPEC` · `POST-AUDIT REMEDIATION SPEC` |
| **Prioridad** | **P0** · **Estado** `SPEC_READY` |
| **Dependencias** | `GA-REM-001` |
| **Hallazgos** | P0-8 · S-04 · S-08 · S-09 · `GA-TD-008` · `GA-TD-026` |
| **Revalidado** | 2026-09-03 — 31 coincidencias de credenciales en `GUIA_PRUEBAS_EN_VIVO.md`; `docker-compose.yml` no inyecta `FEATURE_RATE_LIMIT_ENABLED` |

> **Nota de manejo:** esta spec **no transcribe ningún secreto**. Se refiere a ellos por ubicación.

## Problema
Existen credenciales de acceso documentadas en el repositorio, incluida una cuenta de Super Administrador, contra un entorno accesible públicamente y con el limitador de intentos de login desactivado en producción por omisión de la variable de entorno.

## Evidencia
| Ítem | Ubicación | Naturaleza |
|---|---|---|
| 15 pares usuario/contraseña, incluido Super Admin | `GUIA_PRUEBAS_EN_VIVO.md:13-40` | documentación versionada |
| Contraseñas de seeds de desarrollo | `backend/seeds/dev_seeds.py:154-228` | código versionado |
| Contraseñas de seeds de integración | `backend/seeds/integration_seeds.py:174-203` | código versionado |
| Rate limit desactivado en producción | `docker-compose.yml` (no inyecta la variable) + `backend/app/config.py:96` (defecto `False`) | configuración |
| Credenciales de BD y SMTP reales | `.env` raíz y `backend/.env` | **no versionados** (verificado: `git log --all -- '*.env'` vacío) |
| BD en IP pública con rol superusuario y SSL comentado | `backend/.env`; `.env.example:30` | configuración |

## Comportamiento actual
- Las contraseñas de las cuentas de prueba son públicas y débiles.
- El decorador `@rate_limit("5/minute")` del login es un *no-op* en producción.
- El entorno de desarrollo se conecta directamente a la base de datos en la nube.

## Comportamiento esperado
- Ninguna credencial funcional reside en el repositorio.
- Las cuentas de demostración, si se conservan, viven en un entorno separado y no pueden autenticarse contra producción.
- El limitador de intentos está activo en producción.
- El acceso a la base de datos usa un rol de aplicación con privilegios mínimos y transporte cifrado.

## Alcance
1. **Inventario y clasificación** de toda credencial presente en el repositorio: real / seed de desarrollo / seed de integración / potencialmente válida en producción.
2. Determinar, con evidencia, si los seeds se ejecutaron contra la base que sirve el entorno público.
3. Rotación de lo que resulte válido en producción.
4. Retirada de credenciales de la documentación versionada, sustituyéndolas por referencias a un almacén fuera del repositorio.
5. Separación formal demo / test / producción y política de cuentas de prueba.
6. Activación de `FEATURE_RATE_LIMIT_ENABLED` en producción **sin tocar el mecanismo de despliegue** (es una variable de entorno del servicio, no del pipeline).
7. Rol de base de datos con privilegios mínimos y SSL obligatorio.

## Fuera de alcance
Gestor de secretos corporativo (queda en backlog P2) · MFA · política de complejidad de contraseñas (es `GA-REM-012`) · **cualquier cambio en workflows de despliegue**.

## Backend afectado
`seeds/*.py` (contraseñas dejan de estar en código; se leen de variable de entorno o se generan). Ningún cambio de lógica de negocio.

## Base de datos afectada
Ninguna estructuralmente. **Sí datos**: rotación de hashes de contraseña de cuentas existentes. Requiere procedimiento, no migración de esquema.

## Seguridad
Es el objeto de la spec. Cierra `S-04` (P0), mitiga `S-08` y `S-09` (P1).

## Compatibilidad
**Ruptura intencionada**: las credenciales documentadas dejarán de funcionar. Debe comunicarse a quien esté usando el entorno para pruebas.

## Edge cases
| Caso | Comportamiento exigido |
|---|---|
| Los seeds nunca se ejecutaron contra producción | se documenta con evidencia; se rota igualmente lo que exista |
| Existe una cuenta de Super Admin activa en producción | rotación obligatoria e inmediata |
| Un tester pierde acceso tras la rotación | canal de entrega de credenciales fuera del repositorio, definido en la spec |
| El rate limit bloquea a un usuario legítimo | umbral configurable; se documenta el valor elegido y su justificación |

## Acceptance Criteria

**AC01 — Sin credenciales funcionales en el repositorio**
```
Given el repositorio tras el cierre de GA-REM-004
When  se buscan pares usuario/contraseña en documentación y seeds
Then  ninguna combinación encontrada autentica contra ningún entorno desplegado
```
**AC02 — Las contraseñas de seeds no están en código**
```
Given backend/seeds/*.py
When  se inspecciona la definición de usuarios
Then  las contraseñas provienen de variable de entorno o se generan aleatoriamente
And   no hay literales de contraseña en el código versionado
```
**AC03 — Rate limiting activo en producción**
```
Given el servicio backend en producción
When  se realizan 6 intentos de login en menos de un minuto desde la misma IP
Then  el sexto responde 429
```
**AC04 — El deployment no ha sido modificado**
```
Given el diff de cierre de GA-REM-004
When  se listan los archivos modificados
Then  ninguno pertenece a .github/workflows/
And   docker-compose.yml no altera pull_policy, la etiqueta :latest ni el servicio watchtower
```
**AC05 — Inventario documentado**
```
Given el certification report de GA-REM-004
When  se consulta el inventario de credenciales
Then  cada credencial encontrada está clasificada y tiene una acción asociada
And   ningún secreto aparece transcrito en el informe
```
**AC06 — Separación de entornos**
```
Given la política de cuentas de prueba
When  se intenta autenticar una cuenta de demostración contra producción
Then  la autenticación falla
```
**AC07 — Acceso a base de datos con privilegios mínimos**
```
Given la configuración de conexión de la aplicación
When  se inspecciona el rol utilizado
Then  no es un superusuario
And   la cadena de conexión exige transporte cifrado
```

## Tests requeridos
`T-004-01` rate limit devuelve 429 (integración, entorno aislado) · `T-004-02` ausencia de literales de contraseña en `seeds/` (test estático) · `T-004-03` AC04 verificación del diff (script) · `T-004-04` cuenta demo rechazada en producción (verificación manual documentada).

## Riesgos
| Riesgo | Mitigación |
|---|---|
| Rotar contraseñas deja fuera a usuarios reales en operación | inventariar cuentas activas antes de rotar; comunicar |
| Activar rate limit bloquea a operadores tras un fallo de red | umbral por IP configurable; se documenta el valor |
| El rol de BD con privilegios mínimos rompe migraciones | separar rol de aplicación y rol de migración |

## Rollback lógico
La activación del rate limit es una variable de entorno reversible. La rotación de contraseñas **no es reversible** y no debe serlo.

## Definition of Done
- [ ] Inventario completo sin transcribir secretos · [ ] AC01–AC07 verificados · [ ] AC04 confirma que el deployment sigue intacto · [ ] Certification report
