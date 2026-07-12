"""Application-wide constants."""

from pathlib import Path

APP_NAME: str = "OptionDesk Pro"
APP_VERSION: str = "0.1.0"
APP_CODENAME: str = "Foundation"
APP_VENDOR: str = "OptionDesk"

BASE_DIR: Path = Path(__file__).resolve().parents[3]
SRC_DIR: Path = BASE_DIR / "src"
CONFIG_DIR: Path = BASE_DIR / "config"
RESOURCES_DIR: Path = BASE_DIR / "resources"
DATA_DIR_NAME: str = "OptionDeskPro"

DEFAULT_THEME: str = "dark"
DEFAULT_LOCALE: str = "en_IN"
DEFAULT_TIMEZONE: str = "Asia/Kolkata"

APPLICATION_YAML: str = "application.yaml"
DATABASE_YAML: str = "database.yaml"
BROKER_YAML: str = "broker.yaml"
LOGGING_YAML: str = "logging.yaml"
UI_YAML: str = "ui.yaml"
RISK_YAML: str = "risk.yaml"
SCHEDULER_YAML: str = "scheduler.yaml"
PLUGINS_YAML: str = "plugins.yaml"
VERSION_JSON: str = "version.json"

DATABASE_CONFIG: str = "config.db"
DATABASE_MARKET: str = "market.db"
DATABASE_STRATEGY: str = "strategy.db"
DATABASE_BACKTEST: str = "backtest.db"
DATABASE_LOG: str = "log.db"

LOG_DIR_NAME: str = "logs"
BACKUP_DIR_NAME: str = "backups"
PLUGIN_DIR_NAME: str = "plugins"
WORKSPACE_DIR_NAME: str = "workspaces"

MAX_FILE_LINES: int = 300
MAX_FUNCTION_LINES: int = 40
MAX_CLASS_LINES: int = 250

CREDENTIAL_SERVICE_NAME: str = "OptionDeskPro"
CREDENTIAL_API_KEY: str = "breeze_api_key"
CREDENTIAL_API_SECRET: str = "breeze_api_secret"
CREDENTIAL_SESSION_TOKEN: str = "breeze_session_token"
