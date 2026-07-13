"""Backward-compatible subscription manager export."""

from app.market_data.subscriptions.subscription_service import SubscriptionService

MarketDataSubscriptionManager = SubscriptionService

__all__ = ["MarketDataSubscriptionManager", "SubscriptionService"]
