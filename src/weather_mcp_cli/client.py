"""Interactive demo MCP client for the NWS weather server."""

from __future__ import annotations

import asyncio
import sys

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


HELP = """
Commands:
  tools                     List tools from the MCP server
  forecast <lat> <lon>      Call get_forecast
  alerts <STATE>            Call get_alerts (two-letter state)
  help                      Show this help
  quit                      Exit
""".strip()


def _tool_text(result) -> str:
    parts: list[str] = []
    for block in result.content:
        text = getattr(block, "text", None)
        if text:
            parts.append(text)
        else:
            parts.append(str(block))
    return "\n".join(parts) if parts else "(empty result)"


async def _run_session() -> None:
    server_params = StdioServerParameters(
        command=sys.executable,
        args=["-m", "weather_mcp.server"],
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            print("Connected to NWS weather MCP server.")
            print(HELP)
            print()

            while True:
                try:
                    line = await asyncio.to_thread(input, "weather> ")
                except (EOFError, KeyboardInterrupt):
                    print()
                    break

                line = line.strip()
                if not line:
                    continue

                parts = line.split()
                cmd = parts[0].lower()

                if cmd in {"quit", "exit", "q"}:
                    break

                if cmd == "help":
                    print(HELP)
                    continue

                if cmd == "tools":
                    listed = await session.list_tools()
                    for tool in listed.tools:
                        print(f"- {tool.name}: {tool.description}")
                    continue

                if cmd == "forecast":
                    if len(parts) != 3:
                        print("Usage: forecast <lat> <lon>")
                        continue
                    try:
                        lat = float(parts[1])
                        lon = float(parts[2])
                    except ValueError:
                        print("Latitude and longitude must be numbers.")
                        continue
                    result = await session.call_tool(
                        "get_forecast",
                        arguments={"latitude": lat, "longitude": lon},
                    )
                    print(_tool_text(result))
                    continue

                if cmd == "alerts":
                    if len(parts) != 2:
                        print("Usage: alerts <STATE>")
                        continue
                    result = await session.call_tool(
                        "get_alerts",
                        arguments={"state": parts[1]},
                    )
                    print(_tool_text(result))
                    continue

                print(f"Unknown command: {cmd}. Type 'help' for commands.")


def main() -> None:
    asyncio.run(_run_session())


if __name__ == "__main__":
    main()
