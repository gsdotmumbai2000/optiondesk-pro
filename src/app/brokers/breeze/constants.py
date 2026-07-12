"""Official Breeze API constants from breeze-connect SDK."""

import urllib.parse
from typing import Any

# Official login URL documented by ICICI Direct Breeze API.
BREEZE_LOGIN_BASE_URL = "https://api.icicidirect.com/apiuser/login"


def breeze_config() -> Any:
    """Return official breeze-connect configuration module."""
    import breeze_connect.config as breeze_config_module

    return breeze_config_module


def login_url(api_key: str) -> str:
    """Build official Breeze login URL with encoded API key."""
    encoded = urllib.parse.quote_plus(api_key)
    return f"{BREEZE_LOGIN_BASE_URL}?api_key={encoded}"
