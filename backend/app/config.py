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
        if not self.POSTGRES_PASSWORD or self.POSTGRES_PASSWORD == "change_me":
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


settings = Settings()
