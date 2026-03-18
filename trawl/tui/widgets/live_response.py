import json
import re
import time
import pyperclip
from rich.markup import escape
from textual import on
from textual.app import ComposeResult
from textual.containers import Vertical, Horizontal
from textual.widgets import Button, Label, Markdown

from .chat_bubble import CodeBlock
from ...utils.export_pdf import export_markdown_to_pdf

class LiveResponseWidget(Vertical):
    """Streaming response area — shows status, then streams markdown tokens."""

    DEFAULT_CSS = """
    LiveResponseWidget {
        height: auto;
        padding: 1 2;
        margin-bottom: 2;
        background: $surface;
        border: round $accent;
    }
    LiveResponseWidget #live-query {
        color: $accent;
        text-style: bold;
        margin-bottom: 1;
    }
    LiveResponseWidget #live-status {
        color: $warning;
        text-style: italic;
        height: 1;
    }
    LiveResponseWidget #live-md {
        height: auto;
    }
    LiveResponseWidget #live-copy-full-btn, LiveResponseWidget #live-download-pdf-btn {
        margin-right: 1;
        background: $accent-darken-1;
        color: $text;
        width: 20;
        height: 3;
        display: none;
        border: none;
    }
    LiveResponseWidget #live-copy-full-btn:hover, LiveResponseWidget #live-download-pdf-btn:hover {
        background: $accent;
    }
    #live-actions {
        height: 3;
        margin-top: 1;
    }
    #live-verticals {
        height: auto;
        padding: 0 1;
        margin-bottom: 1;
        display: none;
    }
    .vertical-label {
        height: 1;
        margin-bottom: 0;
        color: $text-muted;
    }
    .vertical-active {
        color: $warning;
        text-style: bold;
    }
    .vertical-done {
        color: $success;
    }
    """

    def compose(self) -> ComposeResult:
        yield Label("", id="live-query")
        yield Label("", id="live-status")
        with Vertical(id="live-verticals"):
            pass
        with Vertical(id="live-content"):
            yield Markdown("", id="live-md")
        with Horizontal(id="live-actions"):
            yield Button("📋 Copy Response", id="live-copy-full-btn")
            yield Button("📄 Download PDF", id="live-download-pdf-btn")

    def set_query(self, query: str) -> None:
        if not self.is_mounted: return
        try:
            self.query_one("#live-query", Label).update(f"You: {escape(query)}")
        except Exception:
            pass

    def set_status(self, msg: str) -> None:
        if not self.is_mounted: return
        try:
            self.query_one("#live-status", Label).update(f"⟳  {escape(msg)}")
        except Exception:
            pass

    def clear_status(self) -> None:
        if not self.is_mounted: return
        try:
            self.query_one("#live-status", Label).update("")
        except Exception:
            pass

    def append_token(self, token: str) -> None:
        """Append a token and throttle markdown re-renders to avoid UI stalls."""
        current = getattr(self, "_full_content", "") or ""
        current += token
        self._full_content = current

        if not self.is_mounted: return

        now = time.monotonic()
        last_render = getattr(self, "_last_render_time", 0.0)
        if now - last_render >= 0.15:
            self._last_render_time = now
            try:
                md: Markdown = self.query_one("#live-md", Markdown)
                md.update(current)
            except Exception:
                pass

    def flush_content(self) -> None:
        """Force a final render of accumulated content."""
        if not self.is_mounted: return
        content = getattr(self, "_full_content", "")
        if content:
            try:
                md: Markdown = self.query_one("#live-md", Markdown)
                md.update(content)
            except Exception:
                pass

    def set_verticals(self, verticals: list) -> None:
        """Display the 3 DeepSearch verticals with progress indicators."""
        if not self.is_mounted: return
        try:
            container = self.query_one("#live-verticals", Vertical)
            container.display = True
            container.remove_children()
            container.mount(Label("[bold cyan] Research Verticals:[/]"))
            self._vertical_labels = []
            for i, v in enumerate(verticals):
                lbl = Label(f"  ⏳ V{i+1}: {v}", classes="vertical-label")
                container.mount(lbl)
                self._vertical_labels.append(lbl)
        except Exception:
            pass

    def update_vertical_progress(self, index: int, query: str, status: str, url_count: int = 0) -> None:
        """Update a specific vertical's progress."""
        if not hasattr(self, "_vertical_labels") or index >= len(self._vertical_labels):
            return
        lbl = self._vertical_labels[index]
        if status == "searching":
            lbl.update(f"  🔍 V{index+1}: {query}")
            lbl.set_classes("vertical-label vertical-active")
        elif status == "done":
            lbl.update(f"  ✅ V{index+1}: {query} ({url_count} sources)")
            lbl.set_classes("vertical-label vertical-done")

    def show_copy_buttons(self) -> None:
        """Show copy and download buttons and populate code block buttons."""
        if not self.is_mounted: return
        
        content = self.get_content()
        try:
            self.query_one("#live-copy-full-btn").display = True
            self.query_one("#live-download-pdf-btn").display = True
            
            container = self.query_one("#live-content", Vertical)
            container.remove_children()
            
            parts = re.split(r"(```(?:\w+)?\n.*?\n```)", content, flags=re.DOTALL)
            for part in parts:
                if part.startswith("```"):
                    match = re.match(r"```(?:\w+)?\n(.*?)\n```", part, re.DOTALL)
                    code = match.group(1) if match else part
                    container.mount(CodeBlock(code, original_md=part))
                elif part.strip():
                    container.mount(Markdown(part))
        except Exception:
            pass

    @on(Button.Pressed, "#live-download-pdf-btn")
    def action_download_pdf(self) -> None:
        try:
            query_lbl = self.query_one("#live-query", Label).renderable
            query_text = str(query_lbl).replace("You: ", "")
            path = export_markdown_to_pdf(self.get_content(), query=query_text)
            self.app.notify(f"PDF saved to {path}", severity="info", title="PDF Exported")
        except Exception as e:
            self.app.notify(f"PDF Export error: {str(e)}", severity="error", title="Error")

    @on(Button.Pressed, "#live-copy-full-btn")
    def copy_full(self) -> None:
        import pyperclip
        try:
            pyperclip.copy(self.get_content())
            self.app.notify("Full response copied to clipboard!", severity="info", title="Success")
        except Exception as e:
            self.app.notify(f"Clipboard error: {str(e)}", severity="error", title="Error")

    def get_content(self) -> str:
        return getattr(self, "_full_content", "")

