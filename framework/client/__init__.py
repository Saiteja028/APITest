"""HTTP client layer built on Playwright's APIRequestContext."""
from framework.client.api_client import ApiClient
from framework.client.response import ApiResponse

__all__ = ["ApiClient", "ApiResponse"]
