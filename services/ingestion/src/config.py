"""Configuration management using Pydantic."""
from pathlib import Path
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class FTPConfig(BaseModel):
    """FTP server configuration."""
    
    host: str = Field(..., description="FTP server hostname")
    port: int = Field(21, description="FTP server port")
    username: str = Field(..., description="FTP username")
    password: str = Field(..., description="FTP password")
    base_path: str = Field("/", description="Base path on FTP server")
    timeout: int = Field(30, description="Connection timeout in seconds")
    passive_mode: bool = Field(True, description="Use passive mode")


class VolumeConfig(BaseModel):
    """Volume configuration for radar strategies."""
    
    number: str = Field(..., description="Volume number (e.g., '01', '02')")
    fields: List[str] = Field(..., description="Data fields to process")


class StrategyConfig(BaseModel):
    """Strategy configuration for radar data collection."""
    
    strategy_id: str = Field(..., description="Strategy identifier")
    volumes: List[VolumeConfig] = Field(..., description="List of volumes")


class RadarConfig(BaseModel):
    """Radar station configuration."""
    
    code: str = Field(..., description="Unique radar code (primary key)")
    title: str = Field(..., description="Radar station title")
    description: Optional[str] = Field(None, description="Radar description")
    center_lat: float = Field(..., description="Center latitude")
    center_long: float = Field(..., description="Center longitude")
    is_active: bool = Field(True, description="Whether radar is active")
    strategies: List[StrategyConfig] = Field(..., description="List of strategies")


class DatabaseConfig(BaseModel):
    """Database configuration."""
    
    host: str = Field("localhost", description="Database host")
    port: int = Field(5432, description="Database port")
    name: str = Field(..., description="Database name")
    user: str = Field(..., description="Database user")
    password: str = Field(..., description="Database password")
    pool_size: int = Field(10, description="Connection pool size")
    max_overflow: int = Field(20, description="Max pool overflow")
    
    @property
    def url(self) -> str:
        """Generate SQLAlchemy database URL."""
        return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.name}"


class AppConfig(BaseModel):
    """Application configuration."""
    
    environment: str = Field("development", description="Environment name")
    log_level: str = Field("INFO", description="Logging level")
    polling_interval: int = Field(300, description="FTP polling interval in seconds")
    max_concurrent_downloads: int = Field(5, description="Max concurrent downloads")
    retry_max_attempts: int = Field(3, description="Max retry attempts")
    retry_backoff_factor: int = Field(2, description="Retry backoff multiplier")


class StorageConfig(BaseModel):
    """Storage configuration."""
    
    bufr_path: Path = Field(..., description="Path for BUFR files")
    cog_path: Path = Field(..., description="Path for COG files")
    retention_days: int = Field(30, description="Data retention in days")
    
    @field_validator("bufr_path", "cog_path")
    @classmethod
    def create_path(cls, v: Path) -> Path:
        """Create path if it doesn't exist."""
        v.mkdir(parents=True, exist_ok=True)
        return v


class Settings(BaseSettings):
    """Main application settings."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_nested_delimiter="__"
    )
    
    ftp: FTPConfig
    radars: List[RadarConfig]
    database: DatabaseConfig
    app: AppConfig
    storage: StorageConfig


def load_settings() -> Settings:
    """Load settings from configuration files and environment.
    
    Returns:
        Loaded settings instance
    """
    import yaml
    from pathlib import Path
    
    # Try to load config.yaml
    config_path = Path("config.yaml")
    if config_path.exists():
        with open(config_path) as f:
            config_data = yaml.safe_load(f)
        return Settings(**config_data)
    
    # Fallback to environment variables
    return Settings()
