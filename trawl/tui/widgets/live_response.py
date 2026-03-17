import json
import re
import pyperclip
from rich.markup import escape
from textual import on
from textual.app import ComposeResult
from textual.containers import Vertical
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
    """

    def compose(self) -> ComposeResult:
        yield Label("", id="live-query")
        yield Label("", id="live-status")
        with Vertical(id="live-content"):
            yield Markdown("", id="live-md")
        with Horizontal(id="live-actions"):
            yield Button("📋 Copy Response", id="live-copy-full-btn")
            yield Button("📄 Download PDF", id="live-download-pdf-btn")

    def set_query(self, query: str) -> None:
        self.query_one("#live-query", Label).update(f"You: {escape(query)}")

    def set_status(self, msg: str) -> None:
        self.query_one("#live-status", Label).update(f"⟳  {escape(msg)}")

    def clear_status(self) -> None:
        self.query_one("#live-status", Label).update("")

    def append_token(self, token: str) -> None:
        md: Markdown = self.query_one("#live-md", Markdown)
        current = getattr(md, "_markdown", "") or ""
        current += token
        md._markdown = current
        md.update(current)
        self._full_content = current

    def show_copy_buttons(self) -> None:
        """Show copy and download buttons and populate code block buttons."""
        content = self.get_content()
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

