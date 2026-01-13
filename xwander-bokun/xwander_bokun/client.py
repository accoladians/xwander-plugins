"""
Async Bokun API client with HMAC-SHA1 authentication.
"""

import os
import hmac
import hashlib
import base64
import asyncio
from datetime import datetime
from typing import Optional, Dict, Any, List
from collections import deque

import httpx


class RateLimiter:
    """Handle API rate limiting with automatic throttling."""

    def __init__(self, max_requests: int = 350, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.request_times: deque = deque()
        self.backoff_seconds = 1.0

    async def wait_if_needed(self):
        """Wait if approaching rate limit."""
        now = asyncio.get_event_loop().time()

        # Clean old requests
        while self.request_times and self.request_times[0] < now - self.window_seconds:
            self.request_times.popleft()

        # Wait if at limit
        if len(self.request_times) >= self.max_requests:
            sleep_time = self.window_seconds - (now - self.request_times[0]) + 1
            if sleep_time > 0:
                await asyncio.sleep(sleep_time)

        self.request_times.append(now)

    async def handle_429(self):
        """Handle rate limit with exponential backoff."""
        await asyncio.sleep(self.backoff_seconds)
        self.backoff_seconds = min(self.backoff_seconds * 2, 60)

    def reset_backoff(self):
        """Reset backoff after success."""
        self.backoff_seconds = 1.0


class BokunClient:
    """
    Async Bokun API client.

    Usage:
        async with BokunClient() as client:
            result = await client.get("/activity.json/123")
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        api_secret: Optional[str] = None,
        base_url: str = "https://api.bokun.io",
        debug: bool = False,
    ):
        self.api_key = api_key or os.getenv("BOKUN_API_KEY") or os.getenv("BOKUN_ACCESS_KEY")
        self.api_secret = api_secret or os.getenv("BOKUN_API_SECRET") or os.getenv("BOKUN_SECRET_KEY")
        self.base_url = base_url
        self.debug = debug
        self.rate_limiter = RateLimiter()
        self._client: Optional[httpx.AsyncClient] = None

        if not self.api_key or not self.api_secret:
            raise ValueError(
                "Bokun API credentials not found. Set BOKUN_ACCESS_KEY/BOKUN_SECRET_KEY "
                "or BOKUN_API_KEY/BOKUN_API_SECRET (environment or constructor)"
            )

    async def __aenter__(self) -> "BokunClient":
        self._client = httpx.AsyncClient(timeout=30.0)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self._client:
            await self._client.aclose()
            self._client = None

    def _sign_request(self, method: str, path: str) -> Dict[str, str]:
        """Generate HMAC-SHA1 authentication headers."""
        utc_date = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        message = utc_date + self.api_key + method.upper() + path

        digest = hmac.new(
            self.api_secret.encode("utf-8"),
            message.encode("utf-8"),
            hashlib.sha1,
        ).digest()

        signature = base64.b64encode(digest).decode("utf-8")

        return {
            "Accept": "application/json",
            "Content-Type": "application/json;charset=UTF-8",
            "X-Bokun-Date": utc_date,
            "X-Bokun-Signature": signature,
            "X-Bokun-AccessKey": self.api_key,
        }

    async def request(
        self,
        method: str,
        path: str,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        retry: bool = True,
    ) -> Dict[str, Any]:
        """Make authenticated API request."""
        if not self._client:
            raise RuntimeError("Client not initialized. Use 'async with' context.")

        await self.rate_limiter.wait_if_needed()

        url = f"{self.base_url}{path}"
        headers = self._sign_request(method, path)

        if self.debug:
            print(f"DEBUG: {method} {url}")
            if data:
                import json
                print(f"DEBUG: Body: {json.dumps(data, indent=2)[:500]}")

        try:
            response = await self._client.request(
                method=method,
                url=url,
                headers=headers,
                json=data,
                params=params,
            )

            if response.status_code == 429 and retry:
                await self.rate_limiter.handle_429()
                return await self.request(method, path, data, params, retry=False)

            response.raise_for_status()
            self.rate_limiter.reset_backoff()

            if self.debug and response.text:
                print(f"DEBUG: Response: {response.text[:500]}...")

            return response.json() if response.text else {}

        except httpx.HTTPStatusError as e:
            if self.debug:
                print(f"Error: {e}")
                print(f"Response: {e.response.text}")
            raise

    # Convenience methods
    async def get(self, path: str, params: Optional[Dict] = None) -> Dict[str, Any]:
        """GET request."""
        return await self.request("GET", path, params=params)

    async def post(self, path: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """POST request."""
        return await self.request("POST", path, data=data)

    async def put(self, path: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """PUT request."""
        return await self.request("PUT", path, data=data)

    async def delete(self, path: str) -> Dict[str, Any]:
        """DELETE request."""
        return await self.request("DELETE", path)

    # High-level API methods
    async def get_experience(self, experience_id: int) -> Dict[str, Any]:
        """Get experience/activity details."""
        return await self.get(f"/activity.json/{experience_id}")

    async def search_experiences(
        self,
        query: Optional[str] = None,
        page: int = 0,
        page_size: int = 20,
    ) -> Dict[str, Any]:
        """Search experiences/activities."""
        payload = {"page": page, "pageSize": page_size}
        if query:
            payload["query"] = query
        return await self.post("/activity.json/search", payload)

    async def get_experience_components(
        self,
        experience_id: int,
        components: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Get experience components via v2.0 API."""
        path = f"/restapi/v2.0/experience/{experience_id}/components"
        if components:
            params = "&".join(f"componentType={c}" for c in components)
            path += f"?{params}"
        return await self.get(path)

    async def update_experience_components(
        self,
        experience_id: int,
        components_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Update experience components via v2.0 API."""
        return await self.put(
            f"/restapi/v2.0/experience/{experience_id}/components",
            components_data,
        )

    async def create_experience(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create new experience via v2.0 API."""
        return await self.post("/restapi/v2.0/experience", data)

    async def search_bookings(
        self,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        customer_email: Optional[str] = None,
        statuses: Optional[List[str]] = None,
        page: int = 0,
        page_size: int = 20,
    ) -> Dict[str, Any]:
        """Search bookings."""
        payload: Dict[str, Any] = {"page": page, "pageSize": page_size}

        if date_from or date_to:
            date_range = {}
            if date_from:
                date_range["from"] = f"{date_from}T00:00:00Z"
            if date_to:
                date_range["to"] = f"{date_to}T23:59:59Z"
            payload["startDateRange"] = date_range

        if customer_email:
            payload["customerEmail"] = customer_email

        if statuses:
            payload["statuses"] = statuses

        return await self.post("/booking.json/booking-search", payload)

    async def get_booking(self, confirmation_code: str) -> Dict[str, Any]:
        """Get booking by confirmation code."""
        # Remove XWA- prefix if present
        code = confirmation_code.replace("XWA-", "") if confirmation_code.startswith("XWA-") else confirmation_code
        result = await self.post("/booking.json/booking-search", {"confirmationCode": code})
        items = result.get("items", [])
        if not items:
            raise ValueError(f"Booking {confirmation_code} not found")
        return items[0]

    async def check_availability(
        self,
        activity_id: int,
        date: str,
    ) -> List[Dict[str, Any]]:
        """Check availability for a date."""
        return await self.get(
            f"/activity.json/{activity_id}/availabilities",
            params={"date": date},
        )
