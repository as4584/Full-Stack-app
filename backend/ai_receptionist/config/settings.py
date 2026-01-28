"""
Centralized configuration module for AI Receptionist.

This module loads all configuration from environment variables
without hardcoding any sensitive values.
"""

from typing import Optional
import logging

try:
    from pydantic_settings import BaseSettings, SettingsConfigDict
    from pydantic import Field
except ImportError:
    from pydantic import BaseSettings, Field
    SettingsConfigDict = None

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables or .env file.
    
    All sensitive values are loaded from environment, never hardcoded.
    """
    
    # Application Environment
    app_env: str = Field(default="local", validation_alias="ENVIRONMENT")
    debug: bool = False
    
    # Twilio Configuration (loaded from environment only)
    twilio_account_sid: Optional[str] = None
    twilio_auth_token: Optional[str] = None
    twilio_phone_number: Optional[str] = None
    
    # Database Configuration
    database_url: Optional[str] = None
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_db: str = "ai_receptionist"
    postgres_user: Optional[str] = None
    postgres_password: Optional[str] = None
    
    # Redis Configuration
    redis_url: Optional[str] = None
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0
    
    # OpenAI Configuration
    openai_api_key: Optional[str] = None
    
    # Google Configuration
    google_api_key: Optional[str] = None
    
    # Google OAuth Configuration
    google_client_id: Optional[str] = None
    google_client_secret: Optional[str] = None
    google_redirect_uri: Optional[str] = None
    
    # Admin/Security
    admin_private_key: Optional[str] = None
    enable_twilio_signature: bool = True
    global_ai_kill_switch: bool = False
    
    # Token Conservation - Disable expensive AI features
    enable_shadow_ai: bool = False  # Shadow AI evaluation after each call
    enable_auditor: bool = False    # Business info auditor simulation
    
    # Email Configuration
    sendgrid_api_key: Optional[str] = None
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_user: Optional[str] = None
    smtp_password: Optional[str] = None
    smtp_from_email: str = "noreply@lexmakesit.com"
    smtp_from_name: str = "AI Receptionist"
    
    # Application Settings
    log_level: str = "INFO"
    public_host: str = "receptionist.lexmakesit.com"
    dashboard_url: str = "https://dashboard.lexmakesit.com"
    
    if SettingsConfigDict:
        model_config = SettingsConfigDict(
            env_file=".env",
            env_file_encoding="utf-8",
            env_prefix="",
            case_sensitive=False,
            extra="ignore"
        )
    else:
        class Config:
            env_file = ".env"
            env_file_encoding = "utf-8"
            case_sensitive = False
            extra = "ignore"
    
    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.app_env.lower() == "production"
    
    @property
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.app_env.lower() in ["local", "development", "dev"]
    
    def get_database_url(self) -> Optional[str]:
        """
        Get database URL, constructing from components if DATABASE_URL not set.
        
        Returns:
            Database connection string or None if not configured
            
        Raises:
            RuntimeError: If SQLite is configured in production
        """
        if self.database_url:
            # PRODUCTION SAFETY: Block SQLite in production
            if self.is_production and self.database_url.startswith('sqlite'):
                raise RuntimeError(
                    f"CRITICAL: SQLite database detected in PRODUCTION environment! "
                    f"Database URL: {self.database_url}. "
                    f"Production systems MUST use PostgreSQL to prevent data loss."
                )
            return self.database_url
        
        if self.postgres_user and self.postgres_password:
            return (
                f"postgresql://{self.postgres_user}:{self.postgres_password}"
                f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
            )
        
        # In production, we MUST have a database URL
        if self.is_production:
            raise RuntimeError(
                "CRITICAL: No database configuration found in PRODUCTION! "
                "Set DATABASE_URL or PostgreSQL credentials (POSTGRES_USER, POSTGRES_PASSWORD)."
            )
            
        return None
    
    def validate_production_secrets(self) -> None:
        """
        Validate that all required secrets are configured in production.
        
        Raises:
            RuntimeError: If any required secret is missing in production
        """
        if not self.is_production:
            return
        
        missing_secrets = []
        
        # JWT Secret (ADMIN_PRIVATE_KEY) is CRITICAL
        if not self.admin_private_key:
            missing_secrets.append("ADMIN_PRIVATE_KEY (JWT_SECRET)")
        
        # Database credentials are CRITICAL
        if not self.database_url and not (self.postgres_user and self.postgres_password):
            missing_secrets.append("DATABASE_URL or POSTGRES_USER/POSTGRES_PASSWORD")
        
        # OpenAI API key is required for core functionality
        if not self.openai_api_key:
            missing_secrets.append("OPENAI_API_KEY")
        
        # Twilio credentials are CRITICAL for voice functionality
        if not self.twilio_account_sid:
            missing_secrets.append("TWILIO_ACCOUNT_SID")
        if not self.twilio_auth_token:
            missing_secrets.append("TWILIO_AUTH_TOKEN")
        
        if missing_secrets:
            raise RuntimeError(
                f"CRITICAL: Production startup BLOCKED due to missing required secrets:\n"
                f"  - {chr(10).join(missing_secrets)}\n\n"
                f"These secrets MUST be set in .env file to prevent auth lockouts and service failures.\n"
                f"Never use fallback values in production."
            )
        
        # Log Twilio config status (not the actual values)
        logger.info(f"✅ Twilio config: SID={self.twilio_account_sid[:8]}..., Token={'set' if self.twilio_auth_token else 'MISSING'}")
        logger.info("✅ Production secrets validation passed")
    
    def get_redis_url(self) -> str:
        """
        Get Redis URL, constructing from components if REDIS_URL not set.
        
        Returns:
            Redis connection string
        """
        if self.redis_url:
            return self.redis_url
        
        return f"redis://{self.redis_host}:{self.redis_port}/{self.redis_db}"
    
    def validate_twilio_config(self) -> bool:
        """
        Validate that required Twilio configuration is present.
        
        Returns:
            True if Twilio is properly configured
        """
        return all([
            self.twilio_account_sid,
            self.twilio_auth_token,
            self.twilio_phone_number
        ])
    
    def configure_logging(self) -> None:
        """Configure application logging based on settings."""
        log_level = getattr(logging, self.log_level.upper(), logging.INFO)
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        if self.is_development:
            logging.getLogger('ai_receptionist').setLevel(logging.DEBUG)


# Global settings instance
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """
    Get or create the global settings instance.
    
    Returns:
        Settings instance loaded from environment
    """
    global _settings
    if _settings is None:
        _settings = Settings()
        _settings.configure_logging()
        logger.info(f"Settings loaded for environment: {_settings.app_env}")
    return _settings


def reset_settings() -> None:
    """Reset settings instance (mainly for testing)."""
    global _settings
    _settings = None
