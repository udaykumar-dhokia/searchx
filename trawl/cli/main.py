import argparse
import asyncio
import sys

import truststore
import uvicorn

import contextlib
import os

@contextlib.contextmanager
def suppress_output():
    with open(os.devnull, "w") as devnull:
        old_stdout = sys.stdout
        old_stderr = sys.stderr
        sys.stdout = devnull
        sys.stderr = devnull
        try:
            yield
        finally:
            sys.stdout = old_stdout
            sys.stderr = old_stderr

with suppress_output():
    from ..api.main import app
    from ..services.invoke_chat import invoke_chat
    from ..tui.app import run_tui


def main() -> None:
    """Synchronous CLI entrypoint to avoid nested event loops."""
    parser = argparse.ArgumentParser(
        description="trawl - On-Premise AI Powered Research Assistant",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  trawl --q "What is machine learning?"
  trawl --tui
  trawl-api  # Runs the FastAPI server
        """,
    )
    parser.add_argument(
        "--q", "--query",
        type=str,
        help="Your research query"
    )
    parser.add_argument(
        "--tui",
        action="store_true",
        help="Run Textual TUI interface"
    )
    parser.add_argument(
        "--host",
        default="0.0.0.0",
        help="Host for the API server (default: 0.0.0.0)"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port for the API server (default: 8000)"
    )

    args = parser.parse_args()

    if args.tui:
        run_tui()
    elif args.q:
        query = args.q
        try:
            asyncio.run(invoke_chat(query=query, type="general"))
        except KeyboardInterrupt:
            print("\nQuery interrupted by user.")
            sys.exit(1)
    else:
        truststore.inject_into_ssl()
        print(f"Starting trawl API server on {args.host}:{args.port}")
        print("Press Ctrl+C to stop")
        try:
            uvicorn.run(app, host=args.host, port=args.port)
        except KeyboardInterrupt:
            print("\nServer stopped.")


if __name__ == "__main__":
    main()