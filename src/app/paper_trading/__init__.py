"""Paper trading: simulated order execution and position tracking against
a virtual account, so broker integrations can be smoke-tested without
risking capital. Reuses the backtesting engine's real ExecutionSimulator
for fills (slippage/commission), not invented pricing math."""
