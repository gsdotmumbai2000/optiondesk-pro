"""Plugin metadata model."""

from pydantic import BaseModel, Field


class PluginMetadata(BaseModel):
    """Plugin manifest metadata."""

    plugin_key: str
    name: str
    version: str
    slot_type: str
    author: str = ""
    description: str = ""
    api_version: str = "1.0.0"
    dependencies: list[str] = Field(default_factory=list)
    permissions: list[str] = Field(default_factory=list)
    entry_point: str = ""
