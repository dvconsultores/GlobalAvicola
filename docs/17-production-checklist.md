# ============================================================
# Global Avícola — Checklist de Pase a Producción
# ============================================================
# Este documento lista todo lo que DEBE activarse/verificarse
# antes de hacer el deploy a producción.
# ============================================================

## 🔐 Seguridad

### 1. JWT Secret Key
- [ ] Generar una clave segura: `python -c 'import secrets; print(secrets.token_hex(32))'`
- [ ] Reemplazar `JWT_SECRET_KEY` en `.env` de producción
- [ ] **NUNCA** usar la clave de desarrollo en producción

### 2. Base de Datos
- [ ] Cambiar `POSTGRES_PASSWORD` por una contraseña fuerte
- [ ] Usar SSL en la conexión (`?ssl=require` en `DATABASE_URL`)
- [ ] Verificar que el usuario de BD tiene permisos mínimos necesarios

### 3. CORS
- [ ] Restringir `BACKEND_CORS_ORIGINS` SOLO al dominio de producción
- [ ] Ejemplo: `BACKEND_CORS_ORIGINS=https://avicola.globaldv.net`

## ⚙️ Feature Flags (Activar en .env)

| Flag | Dev | Prod | Acción |
|------|-----|------|--------|
| `FEATURE_SAP_ENABLED` | `false` | `true` | Activar cuando SAP esté configurado |
| `FEATURE_RATE_LIMIT_ENABLED` | `false` | `true` | Proteger la API de abusos |
| `FEATURE_AUDIT_ENABLED` | `true` | `true` | Debe estar siempre activo |
| `FEATURE_REVIEW_ENABLED` | `true` | `true` | Workflow de aprobación |
| `ENVIRONMENT` | `development` | `production` | Activa headers HSTS, etc. |
| `DEBUG` | `true` | `false` | Desactivar en producción |

## 🔄 SAP Integration

Cuando se configure la conexión real con SAP S/4HANA:

1. [ ] Cambiar `FEATURE_SAP_ENABLED=true`
2. [ ] Implementar `RealSapAdapter` en `backend/app/integrations/sap/adapter.py`
   - Hereda de `SapIntegrationAdapter`
   - Implementa `export_consolidated()`, `check_connection()`, `get_adapter_name()`
3. [ ] Configurar en `SapService.get_adapter()` la selección del adaptador real
4. [ ] Probar idempotencia y reintentos
5. [ ] Ejecutar tests de SAP: `uv run pytest tests/test_sap.py -v`

## 🚀 Deploy

1. [ ] Verificar que `.env` de producción NO se commitea (está en `.gitignore`)
2. [ ] Docker: `docker compose -f docker-compose.yml up -d`
3. [ ] Health check: `curl https://api.avicola.globaldv.net/health`
4. [ ] Verificar Swagger docs: `https://api.avicola.globaldv.net/docs`
5. [ ] Monitorear logs por 24h después del deploy
