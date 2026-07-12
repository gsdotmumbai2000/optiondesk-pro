"""Commands package."""

__all__ = ["CommandDispatcher"]


def __getattr__(name: str) -> object:
    """Lazy exports to avoid import cycles."""
    if name == "CommandDispatcher":
        from app.application.commands.command_dispatcher import CommandDispatcher

        return CommandDispatcher
    raise AttributeError(name)
