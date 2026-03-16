import argparse
import asyncio

import truststore
import uvicorn

from src.main import app
from src.services.invoke_chat import invoke_chat
from src.tui_app import run_tui


def main() -> None:
    """Synchronous CLI entrypoint to avoid nested event loops."""
    parser = argparse.ArgumentParser(description="searchx")
    parser.add_argument("--q", type=str, help="Your query")
    parser.add_argument("--tui", action="store_true", help="Run Textual TUI")
    args = parser.parse_args()

    if args.tui:
        # Textual manages its own asyncio loop internally
        run_tui()
    elif args.q:
        # Fire the async chat invocation once and exit
        query = args.q
        asyncio.run(invoke_chat(query=query))  # type: ignore[arg-type]
    else:
        # Run FastAPI HTTP server
        uvicorn.run(app, host="0.0.0.0", port=8000)


if __name__ == "__main__":
    truststore.inject_into_ssl()
    main()