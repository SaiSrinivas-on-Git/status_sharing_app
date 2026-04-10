"""Google Maps API service for outdoor heuristic enrichment."""

import httpx
import logging
import time
from typing import Optional
from functools import lru_cache

from app.config import get_settings

logger = logging.getLogger(__name__)


class GeoService:
    """
    Google Maps API integration for outdoor heuristic.
    Includes rate limiting and cost-conscious caching.
    """

    GEOCODE_URL = "https://maps.googleapis.com/maps/api/geocode/json"
    ROADS_URL = "https://roads.googleapis.com/v1/nearestRoads"

    # Rate limiting
    MAX_CALLS_PER_MINUTE = 10
    _call_timestamps: list[float] = []

    # Simple in-memory cache (location → result)
    _cache: dict[str, dict] = {}
    CACHE_TTL = 300  # 5 minutes

    def __init__(self):
        self.settings = get_settings()
        self.api_key = self.settings.google_maps_api_key

    def _rate_limit_check(self) -> bool:
        """Check if we're within rate limits."""
        now = time.time()
        # Remove timestamps older than 60 seconds
        self._call_timestamps[:] = [
            t for t in self._call_timestamps if now - t < 60
        ]
        if len(self._call_timestamps) >= self.MAX_CALLS_PER_MINUTE:
            logger.warning("Rate limit reached for Maps API")
            return False
        self._call_timestamps.append(now)
        return True

    def _cache_key(self, lat: float, lon: float) -> str:
        """Round coordinates to ~100m grid for caching."""
        return f"{round(lat, 3)},{round(lon, 3)}"

    async def reverse_geocode(self, lat: float, lon: float) -> Optional[str]:
        """
        Get location type context from coordinates.
        Returns the most relevant location type or None.
        """
        if not self.api_key:
            return None

        cache_key = self._cache_key(lat, lon)
        cached = self._cache.get(cache_key)
        if cached and time.time() - cached["time"] < self.CACHE_TTL:
            return cached["result"]

        if not self._rate_limit_check():
            return None

        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.get(self.GEOCODE_URL, params={
                    "latlng": f"{lat},{lon}",
                    "key": self.api_key,
                    "result_type": "street_address|route|establishment|point_of_interest",
                })
                data = resp.json()

                if data.get("status") == "OK" and data.get("results"):
                    types = data["results"][0].get("types", [])
                    location_type = types[0] if types else None

                    self._cache[cache_key] = {
                        "result": location_type,
                        "time": time.time()
                    }
                    return location_type

        except Exception as e:
            logger.error(f"Reverse geocode failed: {e}")

        return None

    async def check_near_road(self, lat: float, lon: float) -> Optional[bool]:
        """
        Check if the location is near a road using Roads API.
        Returns True if near a road, False if not, None on error.
        """
        if not self.api_key:
            return None

        if not self._rate_limit_check():
            return None

        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.get(self.ROADS_URL, params={
                    "points": f"{lat},{lon}",
                    "key": self.api_key,
                })
                data = resp.json()

                # If snappedPoints exist, there's a road nearby
                return bool(data.get("snappedPoints"))

        except Exception as e:
            logger.error(f"Roads API check failed: {e}")
            return None

    async def enrich_outdoor_heuristic(self, lat: float, lon: float,
                                        speed: Optional[float] = None,
                                        activity: Optional[str] = None) -> dict:
        """
        Full outdoor heuristic enrichment using Maps APIs.
        Returns dict with near_road and location_type.
        """
        location_type = await self.reverse_geocode(lat, lon)
        near_road = await self.check_near_road(lat, lon)

        return {
            "near_road": near_road,
            "location_type": location_type,
        }
