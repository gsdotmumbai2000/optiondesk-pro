"""Domain ports (interfaces)."""

from app.ports.repository_port import IRepository
from app.ports.service_port import IService, IStartable, IStoppable

__all__ = ["IRepository", "IService", "IStartable", "IStoppable"]
