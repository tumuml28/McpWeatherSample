"""National Weather Service API helpers (api.weather.gov)."""

from __future__ import annotations

import asyncio
import ssl
from typing import Any

import httpx
import truststore

NWS_BASE = "https://api.weather.gov"
USER_AGENT = "McpWeatherSample/0.1 (weather-mcp; educational)"
MAX_RETRIES = 3
RETRY_DELAY_SECONDS = 1.0


def _headers() -> dict[str, str]:
    return {
        "User-Agent": USER_AGENT,
        "Accept": "application/geo+json",
    }


def _ssl_context() -> ssl.SSLContext:
    # Use the OS trust store so corporate/Windows CA chains verify correctly.
    return truststore.SSLContext(ssl.PROTOCOL_TLS_CLIENT)


def _client() -> httpx.AsyncClient:
    return httpx.AsyncClient(
        headers=_headers(),
        timeout=30.0,
        follow_redirects=True,
        verify=_ssl_context(),
    )


async def _get_json(client: httpx.AsyncClient, url: str) -> dict[str, Any]:
    last_error: Exception | None = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = await client.get(url)
            response.raise_for_status()
            return response.json()
        except (httpx.HTTPError, ValueError) as exc:
            last_error = exc
            if attempt < MAX_RETRIES:
                await asyncio.sleep(RETRY_DELAY_SECONDS * attempt)
    assert last_error is not None
    raise last_error


def _format_forecast_periods(periods: list[dict[str, Any]], limit: int = 14) -> str:
    if not periods:
        return "No forecast periods available."

    lines: list[str] = []
    for period in periods[:limit]:
        name = period.get("name", "Unknown")
        temp = period.get("temperature")
        unit = period.get("temperatureUnit", "F")
        wind = period.get("windSpeed", "?")
        wind_dir = period.get("windDirection", "")
        short = period.get("shortForecast", "")
        detailed = period.get("detailedForecast", "")
        lines.append(
            f"{name}: {temp}°{unit}, wind {wind} {wind_dir}. {short}\n  {detailed}"
        )
    return "\n\n".join(lines)


def _format_alerts(features: list[dict[str, Any]]) -> str:
    if not features:
        return "No active alerts for this area."

    lines: list[str] = []
    for feature in features:
        props = feature.get("properties") or {}
        event = props.get("event", "Alert")
        severity = props.get("severity", "Unknown")
        area = props.get("areaDesc", "Unknown area")
        headline = props.get("headline") or props.get("description", "No details")
        # Keep headlines readable; truncate very long descriptions.
        if len(headline) > 400:
            headline = headline[:397] + "..."
        lines.append(
            f"- {event} ({severity})\n  Area: {area}\n  {headline}"
        )
    return f"{len(features)} active alert(s):\n\n" + "\n\n".join(lines)


async def get_forecast(latitude: float, longitude: float) -> str:
    """Fetch a readable forecast summary for a lat/lon point."""
    async with _client() as client:
        points_url = f"{NWS_BASE}/points/{latitude},{longitude}"
        points = await _get_json(client, points_url)
        props = points.get("properties") or {}
        forecast_url = props.get("forecast")
        if not forecast_url:
            return (
                f"Could not resolve a forecast for ({latitude}, {longitude}). "
                "NWS only covers US locations."
            )

        location = props.get("relativeLocation", {}).get("properties", {})
        city = location.get("city")
        state = location.get("state")
        place = f"{city}, {state}" if city and state else f"{latitude}, {longitude}"

        forecast = await _get_json(client, forecast_url)
        periods = (forecast.get("properties") or {}).get("periods") or []
        body = _format_forecast_periods(periods)
        return f"Forecast for {place}:\n\n{body}"


async def get_alerts(state: str) -> str:
    """Fetch active alerts for a two-letter US state code."""
    area = state.strip().upper()
    if len(area) != 2 or not area.isalpha():
        return "State must be a two-letter US code (e.g. CA, NY)."

    async with _client() as client:
        url = f"{NWS_BASE}/alerts/active"
        # Prefer query via client for encoding; NWS expects area=XX
        last_error: Exception | None = None
        data: dict[str, Any] | None = None
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                response = await client.get(url, params={"area": area})
                response.raise_for_status()
                data = response.json()
                break
            except (httpx.HTTPError, ValueError) as exc:
                last_error = exc
                if attempt < MAX_RETRIES:
                    await asyncio.sleep(RETRY_DELAY_SECONDS * attempt)
        if data is None:
            assert last_error is not None
            raise last_error

        features = data.get("features") or []
        return f"Active alerts for {area}:\n\n{_format_alerts(features)}"
