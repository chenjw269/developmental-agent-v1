"""Apache APISIX Admin API client."""
import httpx
from typing import Any, Optional

from app.config import get_settings


class ApisixError(Exception):
    """APISIX Admin API error."""
    def __init__(self, message: str, status_code: Optional[int] = None, body: Any = None):
        self.message = message
        self.status_code = status_code
        self.body = body
        super().__init__(message)


class ApisixClient:
    """Sync client for APISIX Admin API (consumers)."""

    def __init__(
        self,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
    ) -> None:
        settings = get_settings()
        self.base_url = (base_url or settings.APISIX_ADMIN_URL).rstrip("/")
        self.api_key = api_key or settings.APISIX_ADMIN_KEY
        self._headers: dict[str, str] = {}
        if self.api_key:
            self._headers["X-API-KEY"] = self.api_key

    def _request(
        self,
        method: str,
        path: str,
        json: Optional[dict] = None,
    ) -> dict:
        url = f"{self.base_url}{path}"
        with httpx.Client(timeout=10.0) as client:
            resp = client.request(
                method,
                url,
                headers=self._headers,
                json=json,
            )
        if resp.status_code >= 400:
            raise ApisixError(
                f"APISIX Admin API error: {resp.status_code}",
                status_code=resp.status_code,
                body=resp.text,
            )
        return resp.json() if resp.content else {}

    def create_consumer(
        self,
        username: str,
        api_key_value: str,
        quota_per_minute: int = 60,
    ) -> None:
        """
        Create a Consumer with key-auth and limit-count.
        username: unique consumer id (we use consumer_name from api_credentials).
        """
        body = {
            "username": username,
            "plugins": {
                "key-auth": {},
                "limit-count": {
                    "count": quota_per_minute,
                    "time_window": 60,
                    "rejected_code": 429,
                    "key_type": "var",
                    "key": "consumer_name",
                },
            },
        }
        # key-auth plugin expects the key in header; we set it via consumer credentials
        # In APISIX, key-auth can be configured with key in the consumer
        # See: https://apisix.apache.org/docs/apisix/plugins/key-auth/
        # Consumer can have plugins.key-auth with no config; key is added via Admin API
        # Actually the key is set by creating a consumer and then adding key-auth credential.
        # In APISIX 3.x, key-auth in consumer: you need to pass the key. Looking at docs:
        # Consumer body: { "username": "xxx", "plugins": { "key-auth": { "key": "my-key" } } }
        # So the key is in plugins.key-auth.key
        body["plugins"]["key-auth"] = {"key": api_key_value}
        self._request("PUT", f"/apisix/admin/consumers/{username}", json=body)

    def update_consumer_quota(self, username: str, quota_per_minute: int) -> None:
        """Update limit-count for an existing consumer. GET then PUT."""
        data = self._request("GET", f"/apisix/admin/consumers/{username}")
        node = data.get("node", {})
        value = node.get("value")
        if not value:
            raise ApisixError(f"Consumer not found: {username}", status_code=404)
        plugins = value.get("plugins", {})
        plugins["limit-count"] = {
            "count": quota_per_minute,
            "time_window": 60,
            "rejected_code": 429,
            "key_type": "var",
            "key": "consumer_name",
        }
        value["plugins"] = plugins
        self._request("PUT", f"/apisix/admin/consumers/{username}", json=value)

    def delete_consumer(self, username: str) -> None:
        """Remove consumer so the key no longer works."""
        self._request("DELETE", f"/apisix/admin/consumers/{username}")

    def get_consumer(self, username: str) -> Optional[dict]:
        """Get consumer if exists."""
        try:
            return self._request("GET", f"/apisix/admin/consumers/{username}")
        except ApisixError as e:
            if e.status_code == 404:
                return None
            raise
