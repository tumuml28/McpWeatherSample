"""MCP weather server exposing NWS forecast and alert tools over stdio."""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from weather_mcp import nws

mcp = FastMCP("nws-weather")


@mcp.tool()
async def get_forecast(latitude: float, longitude: float) -> str:
    """Get a National Weather Service forecast for a US latitude/longitude.

    Args:
        latitude: Latitude in decimal degrees (e.g. 40.7128 for NYC).
        longitude: Longitude in decimal degrees (e.g. -74.0060 for NYC).
    """
    try:
        return await nws.get_forecast(latitude, longitude)
    except Exception as exc:  # noqa: BLE001 - surface clean tool errors to the host
        return f"Failed to fetch forecast: {exc}"


@mcp.tool()
async def get_alerts(state: str) -> str:
    """Get active National Weather Service alerts for a US state.

    Args:
        state: Two-letter US state code (e.g. CA, NY, TX).
    """
    try:
        return await nws.get_alerts(state)
    except Exception as exc:  # noqa: BLE001 - surface clean tool errors to the host
        return f"Failed to fetch alerts: {exc}"


def main() -> None:
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
