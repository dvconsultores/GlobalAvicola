# ENV-01 — CLASIFICACIÓN DE ENTORNO

## Metadata
| Campo | Valor |
|---|---|
| ID | `ENV-01` |
| Tipo | **Decisión normativa** (no es una remediación) |
| Fecha | 2026-09-04 |
| Origen | Aclaración formal del propietario del producto |
| Estado | **VIGENTE** |
| Alcance | Todo el proyecto: informes, gates, políticas de push, estrategia de datos |

---

## 1. Declaración

```
CURRENT DEPLOYED ENVIRONMENT   =  SHARED DEVELOPMENT / TEST / CERTIFICATION
REAL PRODUCTION                =  NOT DEPLOYED YET
CURRENT DATABASE BUSINESS DATA =  TEST / CERTIFICATION DATA
CURRENT USERS                  =  DEVELOPMENT / TEST / CERTIFICATION USERS
CURRENT AUTO DEPLOY            =  DEPLOYS TO SHARED DEVELOPMENT / CERTIFICATION
REAL PRODUCTION RELEASE        =  FUTURE SEPARATE GATE
```

**No existe todavía ninguna instalación empresarial real de Global Avícola.**

## 2. Qué se creía antes

Hasta este punto, los informes técnicos del proyecto —auditoría integral, Waves 1 a 3,
runbooks y gates— trataron el entorno desplegado en `avicola.globaldv.net` como
**producción**. Esa denominación gobernó decisiones de riesgo importantes: la exigencia de
copia de seguridad verificada antes de migrar, la prohibición de tocar el servidor, la
clasificación de `GA-TD-040` como bloqueante de publicación, y la lectura del despliegue
automático como una vía directa a producción empresarial.

La interpretación era razonable con la información disponible y **no se borra**. Se corrige
hacia adelante.

## 3. Terminología obligatoria a partir de ahora

| Concepto | Término correcto | Ya no usar |
|---|---|---|
| El servidor desplegado hoy | `SHARED_TEST` · `CERTIFICATION_ENVIRONMENT` | ~~producción~~ |
| Sus datos de negocio | `TEST / CERTIFICATION DATA` | ~~datos productivos~~ |
| Sus cuentas | `DEVELOPMENT / TEST / CERTIFICATION USERS` | ~~usuarios reales~~ |
| La futura instalación de cliente | `PRODUCTION` · `REAL_PRODUCTION` | — |

`PRODUCTION` y `REAL_PRODUCTION` quedan **reservados** para la instalación empresarial que
todavía no existe.

## 4. Estados de readiness

El estado único `READY_FOR_RELEASE` era ambiguo: no decía a qué entorno se refería. Se
sustituye por dos:

```
READY_FOR_SHARED_TEST_DEPLOY   ¿puede este código desplegarse al entorno compartido?
READY_FOR_REAL_PRODUCTION      ¿puede instalarse para un cliente real?
```

Son independientes. El primero se satisface con calidad de desarrollo verificada; el
segundo exige el gate completo de publicación, que no está abierto.

## 5. Qué NO cambia

La metodología sigue íntegra:

```
NO SPEC = NO DEVELOPMENT
NO AC = NO IMPLEMENTATION
NO TEST = NO COMPLETE
NO E2E = NO PROCESS CERTIFIED
NO EVIDENCE = NO CERTIFICATION
```

Y el flujo:

```
FINDING → SPEC → AC → TASK → CODE → TEST → CERTIFICATION → COMMIT → PUSH
```

`EX-01` tampoco cambia. El despliegue automático sigue exactamente como está; lo único que
cambia es **a dónde se entiende que despliega**:

```
COMMIT/PUSH → SHARED DEVELOPMENT/CERTIFICATION DEPLOY → USER TESTING → E2E CERTIFICATION
```

y no:

```
PUSH → REAL BUSINESS PRODUCTION RELEASE
```

## 6. Consecuencia sobre los hallazgos abiertos

Ningún hallazgo se cierra por esta reclasificación. Varios cambian de **urgencia**:

| Hallazgo | Antes | Ahora |
|---|---|---|
| `GA-TD-040` copia verificada | bloqueante de publicación | **`PRE-REAL-PRODUCTION`** — necesario antes del primer cliente, no bloquea el desarrollo |
| `GA-TD-039` observabilidad | pre-producción | **`PRE-REAL-PRODUCTION`**; la observabilidad mínima del entorno compartido sigue siendo útil ya |
| `R-52` volumen de evidencias | acción de activación productiva | **acción normal de mantenimiento del entorno de certificación** |
| `R-58` entrypoint en Docker real | pendiente del despliegue productivo | **debe cerrarse en el entorno compartido**, que es Docker real |
| `R-44` efecto de la reconciliación | riesgo sobre datos de cliente | riesgo sobre datos de prueba; sigue abierto porque afecta a quien está probando hoy |

## 7. Anotación para documentos históricos

Los informes anteriores que digan «producción» y cuya conclusión dependa de ello llevan
este bloque, sin modificar su fecha, su hallazgo, su evidencia ni su decisión:

```
OWNER CLARIFICATION / ENV-01

The currently deployed environment was previously referred to as
"production" in technical reports.

It is not a real business production environment.

It is a shared development, testing and certification environment
containing only test/certification data.

No real business production deployment currently exists.
```

## 8. Por qué esta decisión importa más de lo que parece

Reclasificar el entorno no es un cambio de etiqueta. Cambia **qué se puede hacer con sus
datos**: dejan de ser información empresarial que hay que preservar y pasan a ser datos de
prueba acumulados que conviene retirar. Eso habilita `GA-REM-025` —el baseline limpio— que
a su vez obliga a demostrar algo que nunca se ha demostrado: que Global Avícola **arranca
desde una base vacía**, que es exactamente el escenario del primer cliente real.
