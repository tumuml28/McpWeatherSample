# NWS Weather MCP Sample

Python MCP server that pulls forecasts and alerts from the [National Weather Service API](https://www.weather.gov/documentation/services-web-api), plus a small demo CLI client. The same server works with Claude Desktop.

## Layout

```
src/weather_mcp/           # MCP server + NWS helpers
src/weather_mcp_client/    # Demo stdio MCP client
config/                    # Claude Desktop example config
```

## Setup

```powershell
cd C:\Work\Projects\McpWeatherSample
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e .
```

## Demo CLI (no LLM)

Spawns the MCP server over stdio and lets you call tools directly:

```powershell
weather-mcp-cli
# or: python -m weather_mcp_cli.client
```

Example session:

```
weather> tools
weather> forecast 40.7128 -74.0060
weather> alerts NY
weather> quit
```

## Claude Desktop

1. Install the package into a venv (see Setup).
2. Copy [config/claude_desktop_config.example.json](config/claude_desktop_config.example.json) into `%APPDATA%\Claude\claude_desktop_config.json`.
3. Confirm the `command` path points at your venv Python, e.g. `C:\\Work\\Projects\\McpWeatherSample\\.venv\\Scripts\\python.exe`.
4. Restart Claude Desktop.
5. Confirm the `nws-weather` tools appear (hammer / MCP tools UI).

Example prompts:

- What's the forecast for 38.89, -77.03?
- How is the weather in NYC?
- Any weather alerts in CA?

## Tools

| Tool | Arguments | Description |
|------|-----------|-------------|
| `get_forecast` | `latitude`, `longitude` | NWS 7-day / 12-hour periods for a US point |
| `get_alerts` | `state` | Active alerts for a two-letter US state |

NWS requires a `User-Agent` on every request; the server sets one automatically. No API key is required.
