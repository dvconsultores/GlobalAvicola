# CORE FRENTE A UNIDAD DE NEGOCIO

Auditoría del 2026-09-07 · **solo lectura**

La pregunta que ordena esta matriz: **¿tiene sentido apagar esto para una empresa?**

---

| Capacidad | Clasificación | ¿Apagable? | Por qué |
|---|---|:--:|---|
| Autenticación, sesión, `/me` | **CORE** | no | apagarla deja el sistema inservible |
| Usuarios, roles, permisos | **CORE** | no | es cómo se concede todo lo demás |
| Empresas | **CORE** | no | es el inquilino mismo |
| Auditoría (`P-09`) | **CORE** | no | inmutable y transversal; apagarla rompería `R9`/`R10` |
| Notificaciones (`P-14`) | **CORE** | no | es un canal, no una unidad. Lo que se filtra es **qué** avisa |
| Áreas funcionales | **CORE** | no | organigrama de la empresa |
| **Progenitoras** | **BUSINESS** | **sí** | el propietario lo pide explícitamente |
| **Reproductoras** | **BUSINESS** | **sí** | ídem |
| **Incubadora** | **BUSINESS** | **sí** | ídem |
| **Engorde** | **BUSINESS** | **sí** | ídem |
| Datos maestros | **SHARED** | parcialmente | unos son de empresa y otros de unidad — ver su matriz |
| Revisión y aprobación (`P-07`) | **MULTI-MODULE** | no | el flujo es el mismo para las cuatro unidades |
| Consolidación SAP (`P-08`) | **MULTI-MODULE** | quizá | consolida las cuatro; apagarlo es plausible comercialmente |
| Reportes y KPI (`P-15`) | **SHARED** | no | pero **debe filtrarse** por unidad — hoy no lo hace |
| Trazabilidad generacional (`P-10`) | **MULTI-MODULE** | no | **cruza unidades por diseño**: es el caso difícil |

## Consecuencia para el diseño

```
Apagar una unidad de negocio  ≠  apagar un módulo funcional
```

Apagar «Incubadora» para una empresa **no** debe apagar `operations`, `reports` ni `review`:
esos siguen existiendo para las unidades que sí tenga. Lo que cambia es **qué filas** ven.

Por eso la capacidad no se resuelve escondiendo pantallas: se resuelve filtrando datos.
