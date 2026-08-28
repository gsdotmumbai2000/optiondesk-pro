"""Application configuration models."""

from enum import Enum

from pydantic import BaseModel, Field

from app.config.models.logging_config import LoggingConfig


class BreezeEnvironment(str, Enum):
    """ICICI Breeze API environment."""

    SANDBOX = "sandbox"
    PRODUCTION = "production"


class MarketMode(str, Enum):
    """Live vs. simulator market-data source selection."""

    AUTO = "auto"
    LIVE = "live"
    SIMULATOR = "simulator"


class ApplicationConfig(BaseModel):
    """Core application settings."""

    schema_version: int = 1
    name: str = "OptionDesk Pro"
    environment: str = "development"
    locale: str = "en_IN"
    timezone: str = "Asia/Kolkata"
    data_directory: str = ""
    auto_save_interval_sec: int = 300
    check_updates_on_startup: bool = True
    market_data_debug: bool = True


class DatabaseConnectionConfig(BaseModel):
    """Single database connection settings."""

    backend: str = "sqlite"
    path: str = ""
    wal_mode: bool = True
    echo: bool = False


class DatabaseConfig(BaseModel):
    """Five-database configuration."""

    schema_version: int = 1
    data_directory: str = ""
    config: DatabaseConnectionConfig = Field(
        default_factory=lambda: DatabaseConnectionConfig(path="config.db")
    )
    market: DatabaseConnectionConfig = Field(
        default_factory=lambda: DatabaseConnectionConfig(path="market.db")
    )
    strategy: DatabaseConnectionConfig = Field(
        default_factory=lambda: DatabaseConnectionConfig(path="strategy.db")
    )
    backtest: DatabaseConnectionConfig = Field(
        default_factory=lambda: DatabaseConnectionConfig(path="backtest.db")
    )
    log: DatabaseConnectionConfig = Field(
        default_factory=lambda: DatabaseConnectionConfig(path="log.db")
    )


class BrokerConfig(BaseModel):
    """Broker connection settings (credentials via CredentialManager)."""

    schema_version: int = 1
    broker_code: str = "BREEZE"
    market_mode: MarketMode = MarketMode.AUTO
    account_name: str = "Default"
    user_id: str = ""
    environment: BreezeEnvironment = BreezeEnvironment.PRODUCTION
    websocket_enabled: bool = True
    auto_login: bool = True
    reconnect_max_retries: int = 5
    reconnect_backoff_ms: int = 2000
    session_timeout_min: int = 480
    rate_limit_per_second: int = 10


class UIConfig(BaseModel):
    """User interface settings."""

    schema_version: int = 1
    theme: str = "dark"
    font_family: str = "Segoe UI"
    font_size: int = 10
    chart_refresh_ms: int = 100
    confirm_on_exit: bool = True
    restore_last_workspace: bool = True


class RiskConfig(BaseModel):
    """Risk management defaults."""

    schema_version: int = 1
    max_daily_loss: str | None = None
    max_position_delta: str | None = None
    max_portfolio_margin: str | None = None
    pop_warning_threshold: str = "0.45"
    delta_roll_threshold: str = "20"
    require_order_confirmation: bool = True


class SchedulerConfig(BaseModel):
    """Scheduler settings."""

    schema_version: int = 1
    enabled: bool = True
    timezone: str = "Asia/Kolkata"
    auto_refresh_interval_sec: int = 30
    backup_cron: str = "0 8 * * *"
    cleanup_cron: str = "0 0 * * *"


class PluginsConfig(BaseModel):
    """Plugin system settings."""

    schema_version: int = 1
    enabled: bool = True
    plugin_directory: str = "plugins"
    auto_load: bool = True
    sandbox_untrusted: bool = False


class AppConfiguration(BaseModel):
    """Root configuration aggregate."""

    application: ApplicationConfig = Field(default_factory=ApplicationConfig)
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    broker: BrokerConfig = Field(default_factory=BrokerConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    ui: UIConfig = Field(default_factory=UIConfig)
    risk: RiskConfig = Field(default_factory=RiskConfig)
    scheduler: SchedulerConfig = Field(default_factory=SchedulerConfig)
    plugins: PluginsConfig = Field(default_factory=PluginsConfig)
