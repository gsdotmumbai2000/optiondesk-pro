"""Logging configuration models."""

from pydantic import BaseModel, Field


class ConsoleLogConfig(BaseModel):
    """Console logging configuration."""

    enabled: bool = True
    level: str = "INFO"
    colorize: bool = True


class FileLogConfig(BaseModel):
    """File logging configuration."""

    enabled: bool = True
    level: str = "DEBUG"
    path: str = "logs/application.log"
    rotation: str = "10 MB"
    retention: str = "30 days"
    compression: str = "zip"


class DailyLogConfig(BaseModel):
    """Daily rotating log configuration."""

    enabled: bool = True
    level: str = "INFO"
    path: str = "logs/daily/{time:YYYY-MM-DD}.log"
    retention: str = "180 days"


class ErrorLogConfig(BaseModel):
    """Error log configuration."""

    enabled: bool = True
    level: str = "ERROR"
    path: str = "logs/error.log"
    rotation: str = "5 MB"
    retention: str = "365 days"


class PerformanceLogConfig(BaseModel):
    """Performance log configuration."""

    enabled: bool = True
    level: str = "INFO"
    path: str = "logs/performance.log"
    rotation: str = "10 MB"


class AuditLogConfig(BaseModel):
    """Audit log configuration."""

    enabled: bool = True
    level: str = "INFO"
    path: str = "logs/audit.log"
    rotation: str = "10 MB"
    retention: str = "2555 days"


class ApiLogConfig(BaseModel):
    """API log configuration."""

    enabled: bool = True
    level: str = "DEBUG"
    path: str = "logs/api.log"
    rotation: str = "10 MB"
    retention: str = "90 days"


class LoggingConfig(BaseModel):
    """Root logging configuration."""

    schema_version: int = 1
    console: ConsoleLogConfig = Field(default_factory=ConsoleLogConfig)
    file: FileLogConfig = Field(default_factory=FileLogConfig)
    daily: DailyLogConfig = Field(default_factory=DailyLogConfig)
    error: ErrorLogConfig = Field(default_factory=ErrorLogConfig)
    performance: PerformanceLogConfig = Field(default_factory=PerformanceLogConfig)
    audit: AuditLogConfig = Field(default_factory=AuditLogConfig)
    api: ApiLogConfig = Field(default_factory=ApiLogConfig)
