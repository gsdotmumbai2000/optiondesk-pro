"""Broker integration package."""

__all__ = ["BrokerFactory", "BrokerInterface", "BrokerManager", "BrokerProvider"]


def __getattr__(name: str) -> object:
    """Lazy exports to avoid import cycles."""
    if name == "BrokerInterface":
        from app.brokers.broker_interface.interface import BrokerInterface

        return BrokerInterface
    if name == "BrokerFactory":
        from app.brokers.broker_factory.factory import BrokerFactory

        return BrokerFactory
    if name == "BrokerManager":
        from app.brokers.broker_manager.manager import BrokerManager

        return BrokerManager
    if name == "BrokerProvider":
        from app.brokers.bootstrap import BrokerProvider

        return BrokerProvider
    raise AttributeError(name)
