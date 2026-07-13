"""Enterprise live option chain and analytics engine."""

__all__ = ["LiveAnalyticsProvider"]


def __getattr__(name: str):
    if name == "LiveAnalyticsProvider":
        from app.live.bootstrap import LiveAnalyticsProvider

        return LiveAnalyticsProvider
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
