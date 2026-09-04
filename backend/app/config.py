from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # General
    ENVIRONMENT: str = "development"
    PROJECT_NAME: str = "Global Avícola"
    DEBUG: bool = True

    # Backend
    BACKEND_HOST: str = "0.0.0.0"
    BACKEND_PORT: int = 8000
    BACKEND_CORS_ORIGINS: str = "http://localhost:5173"

    # Database (S-03/04: sin defaults inseguros — requieren config explícita en .env)
    POSTGRES_HOST: str = ""
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = ""
    POSTGRES_USER: str = ""
    POSTGRES_PASSWORD: str = ""
    DATABASE_URL: str = ""

    @property
    def database_url(self) -> str:
        if self.DATABASE_URL:
            return self.DATABASE_URL
        if not self.POSTGRES_USER or not self.POSTGRES_PASSWORD:
            raise ValueError(
                "POSTGRES_USER y POSTGRES_PASSWORD deben configurarse en .env "
                "(sin valores por defecto)"
            )
        return (
            f"postgresql+asyncpg://"
            f"{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}"
            f"/{self.POSTGRES_DB}"
        )

    # JWT (S-03: sin default inseguro — requiere config explícita en .env)
    JWT_SECRET_KEY: str = ""
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # S-03/04: Validar que no se usen defaults inseguros
        if not self.JWT_SECRET_KEY or self.JWT_SECRET_KEY.startswith("change_me"):
            raise ValueError(
                "JWT_SECRET_KEY debe configurarse en .env con un valor seguro. "
                "Genera uno con: python -c 'import secrets; print(secrets.token_hex(32))'"
            )
        # Si DATABASE_URL está definido, ya contiene las credenciales completas
        # (usuario/contraseña/host), por lo que POSTGRES_PASSWORD es redundante.
        # Solo se exige cuando se arma la URL a partir de las variables sueltas.
        if not self.DATABASE_URL and (
            not self.POSTGRES_PASSWORD or self.POSTGRES_PASSWORD == "change_me"
        ):
            raise ValueError(
                "POSTGRES_PASSWORD debe configurarse en .env con un valor seguro"
            )

    # CORS
    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.BACKEND_CORS_ORIGINS.split(",")]

    # Rate limiting (S-05)
    RATE_LIMIT_LOGIN: str = "5/minute"
    RATE_LIMIT_GLOBAL: str = "60/minute"

    # ── Umbrales de alerta operativa ─────────────────────────────────────────
    # `docs/02-functional-spec.md:516` exige «Mortalidad > umbral **configurable**», y la
    # auditoría lo registró como hueco: estaba fijo en el código (`audit/06:259`).
    #
    # Se hace configurable por el mismo mecanismo que todo lo demás en este sistema
    # —variables de entorno vía `Settings`— y no por empresa: ninguna fuente pide ese
    # alcance, y añadir una columna y una pantalla para algo que nadie ha solicitado sería
    # inventar requisitos. La configurabilidad por empresa queda como mejora opcional en
    # `GA-REM-019`.
    #
    # Porcentaje del saldo de aves previo al evento.
    MORTALITY_ALERT_WARNING_PCT: float = 3.0
    MORTALITY_ALERT_CRITICAL_PCT: float = 8.0

    # ============================================================
    # Feature Flags — controlan qué se habilita en cada entorno
    # ============================================================
    # SAP Integration: false en desarrollo (sin SAP disponible),
    # true en producción cuando se configure la conexión real.
    FEATURE_SAP_ENABLED: bool = False

    # Rate Limiting: false en desarrollo para no bloquear pruebas,
    # true en producción para proteger la API.
    FEATURE_RATE_LIMIT_ENABLED: bool = False

    # Audit: true en todos los entornos (siempre auditar).
    FEATURE_AUDIT_ENABLED: bool = True

    # Review & Approval workflow: true en producción.
    # En desarrollo se puede desactivar para agilizar pruebas.
    FEATURE_REVIEW_ENABLED: bool = True

    # ============================================================
    # SAP — selección de adaptador (GA-REM-010)
    # ============================================================
    # "manual": genera un artefacto para carga por el analista. NO entrega a SAP.
    # "mock"  : simulación para pruebas. NO entrega a SAP.
    # "real"  : entrega verificada a SAP S/4HANA — NO IMPLEMENTADO (GA-REM-017).
    # Un adaptador sin entrega verificada nunca marca un evento como enviado a SAP.
    SAP_ADAPTER: str = "manual"

    # Telegram Bot
    TELEGRAM_API_KEY: str = ""
    TELEGRAM_MINI_APP_URL: str = ""


settings = Settings()
