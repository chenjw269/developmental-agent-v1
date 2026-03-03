"""Call admin-backend internal API to deduct token for a consumer."""
import urllib.request
import urllib.error
import json

from app.config import get_settings


def deduct_token(consumer_name: str) -> tuple[bool, int]:
    """
    Call admin-backend POST /api/v1/internal/deduct-token.
    Returns (success, remaining_tokens). On 402 or error, returns (False, 0).
    """
    settings = get_settings()
    url = f"{settings.ADMIN_BACKEND_URL}/api/v1/internal/deduct-token"
    data = json.dumps({"consumer_name": consumer_name}).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        method="POST",
        headers={"Content-Type": "application/json"},
    )
    if settings.INTERNAL_SECRET:
        req.add_header("X-Internal-Secret", settings.INTERNAL_SECRET)
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            body = json.loads(resp.read().decode())
            return True, int(body.get("remaining_tokens", 0))
    except urllib.error.HTTPError as e:
        if e.code == 402:
            return False, 0
        raise
    except Exception:
        raise
