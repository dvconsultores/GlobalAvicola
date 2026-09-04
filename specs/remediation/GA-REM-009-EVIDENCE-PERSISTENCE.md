# GA-REM-009 — PERSISTENCIA DE EVIDENCIAS Y ARCHIVOS

## Metadata
| Campo | Valor |
|---|---|
| **ID** | `GA-REM-009` · **Tipo** `INFRASTRUCTURE SPEC` · `POST-AUDIT REMEDIATION SPEC` |
| **Prioridad** | **P0** — pérdida de datos activa · **Estado** `SPEC_READY` |
| **Dependencias** | `GA-REM-001` |
| **Hallazgos** | P0-6 · `GA-TD-006` · `GA-TD-027` (`client_max_body_size`) · `GA-REQ-041` (`PARCIAL`) |
| **Revalidado** | 2026-09-03 — `MEDIA_DIR = "/app/media"`; el servicio `backend` de `docker-compose.yml` no declara `volumes` |

## Problema
Las evidencias adjuntas a los eventos operativos (fotos y PDF) se escriben en el sistema de archivos del contenedor, sin volumen persistente. Watchtower recrea el contenedor en cada publicación de imagen. **Cada despliegue destruye todas las evidencias**, dejando filas en `evidences` que apuntan a rutas inexistentes.

El mismo problema afecta a `/tmp/sap_exports/`.

## Evidencia
| Ítem | Ruta |
|---|---|
| Directorio de medios | `backend/app/operations/router.py:19` — `MEDIA_DIR = os.environ.get("MEDIA_DIR", "/app/media")` |
| Escritura del archivo | `router.py:166-176` |
| Sin volumen en el compose | `docker-compose.yml`, servicio `backend` — 0 declaraciones `volumes` |
| Watchtower recreando contenedores | `docker-compose.yml:87-99` — `WATCHTOWER_POLL_INTERVAL=60` |
| Exportaciones SAP efímeras | `backend/app/integrations/sap/adapter.py:82` — `export_dir="/tmp/sap_exports"` |
| Límite de subida incompatible | backend admite 10 MB (`router.py:21`); `frontend/nginx.conf` no define `client_max_body_size` (defecto 1 MB) |

## Comportamiento actual
Subir una evidencia funciona. Recuperarla después de un despliegue, no.

## Comportamiento esperado
Una evidencia subida sobrevive a cualquier número de despliegues y es recuperable mientras exista su registro en base de datos.

## Alcance
1. Volumen persistente para `MEDIA_DIR`, **sin modificar el mecanismo de despliegue** (declarar un volumen es configuración del servicio, no del pipeline).
2. Misma decisión para el directorio de exportaciones SAP.
3. `client_max_body_size` coherente con el límite del backend.
4. Verificación de permisos: el contenedor corre como usuario `avicola` no root; el volumen debe ser escribible por él.
5. Inventario del daño ya causado: filas de `evidences` cuyo archivo no existe.
6. Política de retención, copia de seguridad y borrado.

## Fuera de alcance
Migrar a almacenamiento de objetos (S3 o equivalente) — se evalúa como alternativa pero no se impone si un volumen resuelve · CDN para servir archivos · **cualquier cambio en workflows de despliegue, Watchtower o la etiqueta `:latest`**.

## Decisión de arquitectura requerida
| Opción | Ventaja | Coste |
|---|---|---|
| **A · Volumen nombrado de Docker** | mínima intervención; no añade servicios; resuelve el problema | atado al host; la copia de seguridad es responsabilidad del host |
| **B · Bind mount a ruta del host** | copia de seguridad trivial | acopla el contenedor a la disposición del host |
| **C · Almacenamiento de objetos** | desacoplado, escalable, con versionado | añade dependencia externa y credenciales; mayor alcance |

**Recomendación para la revisión: opción A.** El principio §40 del programa desaconseja introducir servicios externos si un volumen resuelve correctamente el problema.

## Backend afectado
Posiblemente ninguno si se resuelve por configuración. Si se opta por C: `operations/router.py` y `operations/service.py` (rutas y borrado).

## Base de datos afectada
Ninguna estructuralmente. **Sí datos**: identificar y marcar las filas de `evidences` huérfanas.

## Seguridad
La descarga ya exige autenticación y valida la compañía (`operations/service.py:547,566`). El volumen no debe exponerse por HTTP directamente.

## Edge cases
| Caso | Comportamiento exigido |
|---|---|
| Evidencia cuyo archivo ya no existe | la descarga devuelve un error claro, no un 500; la fila se marca como huérfana |
| Volumen sin permisos de escritura para el usuario `avicola` | el arranque falla con mensaje explícito, no en la primera subida |
| Archivo de 8 MB a través de Nginx | se sube correctamente (hoy da 413) |
| Archivo mayor que el límite del backend | 400 con mensaje de negocio, antes de escribir |
| Borrado de una evidencia | se borra el archivo y la fila de forma consistente |
| Dos evidencias con el mismo nombre original | ya resuelto por el prefijo `uuid4().hex` |

## Acceptance Criteria

**AC01 — La evidencia sobrevive a un redespliegue**
```
Given una evidencia subida a un evento
When  el contenedor del backend se recrea
Then  la evidencia sigue siendo descargable y su contenido es idéntico
```
**AC02 — Archivos de hasta 10 MB**
```
Given una evidencia de 8 MB de un tipo permitido
When  se sube a través de la interfaz
Then  se almacena correctamente y no se recibe 413
```
**AC03 — El límite del backend se respeta**
```
Given un archivo de 11 MB
When  se intenta subir
Then  se rechaza con 400 y mensaje de negocio
```
**AC04 — Evidencia huérfana**
```
Given una fila de evidences cuyo archivo no existe
When  se intenta descargar
Then  se recibe un error explícito, no un 500
```
**AC05 — Permisos del volumen**
```
Given el contenedor arrancando como usuario no root
When  se inicializa el almacenamiento de medios
Then  el directorio es escribible o el arranque falla con mensaje explícito
```
**AC06 — El deployment no ha sido modificado**
```
Given el diff de cierre de GA-REM-009
When  se listan los archivos modificados
Then  ninguno pertenece a .github/workflows/
And   docker-compose.yml conserva pull_policy, la etiqueta :latest y el servicio watchtower sin cambios
```
**AC07 — Inventario del daño**
```
Given la base de datos de producción
When  se ejecuta el inventario de evidencias
Then  existe el recuento de filas cuyo archivo no existe
```

## Tests requeridos
`T-009-01` supervivencia a recreación de contenedor (verificación de infraestructura documentada) · `T-009-02` subida de 8 MB (integración/E2E) · `T-009-03` rechazo de 11 MB · `T-009-04` evidencia huérfana · `T-009-05` AC06 verificación del diff (script) · `T-009-06` inventario (consulta documentada).

## Riesgos
| Riesgo | Mitigación |
|---|---|
| El volumen se crea vacío y las evidencias antiguas ya se perdieron | AC07 lo cuantifica; se comunica como pérdida consumada, no se oculta |
| Un cambio en el compose se interpreta como tocar el deployment | AC06 verifica explícitamente que `pull_policy`, `:latest` y `watchtower` no cambian |
| El volumen crece sin control | política de retención definida en la spec |

## Rollback lógico
Retirar la declaración de volumen restaura el comportamiento anterior. Los archivos ya escritos en el volumen persisten.

## Definition of Done
- [ ] Decisión A/B/C documentada · [ ] AC01–AC07 verificados · [ ] AC06 confirma deployment intacto · [ ] Política de retención y copia de seguridad definida · [ ] Certification report
