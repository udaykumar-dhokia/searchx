import argparse
import asyncio
import json
import os
import sys
import contextlib

import truststore
import uvicorn
from rich.console import Console, Group
from rich.live import Live
from rich.markdown import Markdown
from rich.panel import Panel
from rich.spinner import Spinner
from rich.table import Table
from rich.text import Text

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

from ..utils.config_manager import ConfigManager

console = Console()

async def stream_research(query: str) -> None:
    """Stream research results to the terminal with animations and stable layout."""
    status_message = "Initializing..."
    full_content = ""
    sources = []
    images = []
    videos = []
    
    def make_layout():
        parts = []
        parts.append(Panel(
            Spinner("dots", text=status_message, style="cyan"),
            title=f"[bold blue]Researching: {query}[/]",
            border_style="blue",
            padding=(0, 1)
        ))
        
        if sources:
            source_table = Table(show_header=False, box=None, padding=(0, 1))
            for i, url in enumerate(sources[:5]):
                source_table.add_row(f"[dim]{i+1}.[/] [link={url}]{url}[/link]")
            parts.append(Panel(source_table, title="[bold]Sources[/]", border_style="dim"))

        if full_content:
            parts.append(Panel(
                Markdown(full_content),
                border_style="green",
                padding=(1, 2)
            ))
            
        media_parts = []
        if images:
            media_parts.append(f"[bold]Images:[/] {len(images)}")
        if videos:
            media_parts.append(f"[bold]Videos:[/] {len(videos)}")
        
        if media_parts:
            parts.append(Text.assemble("  ".join(media_parts), style="italic dim"))
            
        return Group(*parts)

    with Live(make_layout(), refresh_per_second=10) as live:
        try:
            async for chunk in invoke_chat(query=query, type="general"):
                if chunk.startswith("data: "):
                    try:
                        data = json.loads(chunk[6:])
                        event_type = data.get("type")
                        
                        if event_type == "status":
                            status_message = data.get("message", status_message)
                        elif event_type == "content":
                            full_content += data.get("text", "")
                        elif event_type == "urls":
                            sources = data.get("urls", [])
                        elif event_type == "image_urls":
                            images = data.get("image_urls", [])
                        elif event_type == "video_urls":
                            videos = data.get("video_urls", [])
                            
                        live.update(make_layout())
                    except json.JSONDecodeError:
                        pass
        except Exception as e:
            live.update(Panel(f"[bold red]Error:[/] {e}", title="[bold red]Error[/]", border_style="red"))
            return

    console.print(f"\n[bold green]✓ Research complete for:[/] {query}")

def handle_config(args: argparse.Namespace) -> None:
    """Handle config view and edit."""
    config = ConfigManager.get_config()
    
    if args.config_command == "view":
        table = Table(title="[bold blue]Trawl Configuration[/]", box=None)
        table.add_column("Setting", style="cyan")
        table.add_column("Value", style="green")
        
        for key, value in config.items():
            display_value = str(value)
            if "api_key" in key.lower() and value:
                display_value = f"{value[:4]}...{value[-4:]}"
            table.add_row(key, display_value)
            
        console.print(table)
    
    elif args.config_command == "set":
        if not args.key or args.value is None:
            console.print("[red]Error: Must specify key and value to set.[/]")
            return
            
        config[args.key] = args.value
        ConfigManager.save_config(config)
        console.print(f"[green]✓ Setting [bold]{args.key}[/] updated to [bold]{args.value}[/][/]")

def main() -> None:
    """Synchronous CLI entrypoint."""
    parser = argparse.ArgumentParser(
        description="trawl - On-Premise AI Powered Research Assistant",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Commands")
    
    research_parser = subparsers.add_parser("research", help="Search and research a query")
    research_parser.add_argument("query", nargs="?", help="Your research query")
    research_parser.add_argument("--q", "--query", dest="query_alt", help="Your research query (alternative)")
    
    subparsers.add_parser("tui", help="Run Textual TUI interface")
    
    api_parser = subparsers.add_parser("api", help="Run the FastAPI server")
    api_parser.add_argument("--host", default="0.0.0.0", help="Host (default: 0.0.0.0)")
    api_parser.add_argument("--port", type=int, default=8000, help="Port (default: 8000)")
    
    config_parser = subparsers.add_parser("config", help="Manage configuration")
    config_subparsers = config_parser.add_subparsers(dest="config_command", help="Config subcommands")
    config_subparsers.add_parser("view", help="View current configuration")
    set_parser = config_subparsers.add_parser("set", help="Set a configuration value")
    set_parser.add_argument("key", help="Configuration key")
    set_parser.add_argument("value", help="Configuration value")

    parser.add_argument("--q", "--query", dest="legacy_query", help=argparse.SUPPRESS)
    parser.add_argument("--tui", action="store_true", dest="legacy_tui", help=argparse.SUPPRESS)

    args = parser.parse_args()

    if args.command == "tui" or args.legacy_tui:
        run_tui()
    elif args.command == "api":
        truststore.inject_into_ssl()
        console.print(f"[bold blue]Starting trawl API server on {args.host}:{args.port}[/]")
        try:
            uvicorn.run(app, host=args.host, port=args.port)
        except KeyboardInterrupt:
            console.print("\n[yellow]Server stopped.[/]")
    elif args.command == "config":
        handle_config(args)
    else:
        query = args.query if hasattr(args, 'query') and args.query else None
        if not query and hasattr(args, 'query_alt'): query = args.query_alt
        if not query: query = args.legacy_query
        
        if query:
            try:
                asyncio.run(stream_research(query))
            except KeyboardInterrupt:
                console.print("\n[yellow]Query interrupted by user.[/]")
                sys.exit(1)
        else:
            parser.print_help()

if __name__ == "__main__":
    main()
