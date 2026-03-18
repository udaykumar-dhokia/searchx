import re
import pyperclip
from rich.markup import escape
from textual import on
from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.widgets import Button, Label, Markdown, Static
from ...utils.export_pdf import export_markdown_to_pdf

class ChatBubble(Static):
    """A single query + response block in the chat history."""

    DEFAULT_CSS = """
    ChatBubble {
        height: auto;
        margin-bottom: 2;
        padding: 1 2;
        background: $surface;
        border: round $primary-darken-2;
    }
    ChatBubble .query {
        color: $accent;
        text-style: bold;
        margin-bottom: 1;
    }
    ChatBubble .response {
        color: $text;
    }
    ChatBubble #copy-full-btn, ChatBubble #download-pdf-btn {
        background: $accent-darken-1;
        color: $text;
        width: 20;
        height: 3;
        margin-right: 1;
        border: none;
    }
    ChatBubble #copy-full-btn:hover, ChatBubble #download-pdf-btn:hover {
        background: $accent;
    }
    ChatBubble #bubble-actions {
        height: 3;
        margin-top: 1;
    }

    /* ── CodeBlock specific styles ── */
    CodeBlock {
        margin: 1 0;
        background: $surface-darken-1;
        border: solid $primary-darken-3;
        height: auto;
    }
    .code-header {
        height: 1;
        background: $primary-darken-3;
        layout: horizontal;
        content-align: right middle;
    }
    .copy-icon-btn {
        min-width: 4;
        height: 1;
        padding: 0 1;
        background: transparent;
        border: none;
        color: $text-muted;
    }
    .copy-icon-btn:hover {
        color: $accent;
        background: $primary-darken-2;
    }
    """

    def __init__(self, query: str, response: str) -> None:
        super().__init__()
        self._query = query
        self._response = response

    def compose(self) -> ComposeResult:
        yield Label(f"You: {escape(self._query)}", classes="query")
        
        parts = re.split(r"(```(?:\w+)?\n.*?\n```)", self._response, flags=re.DOTALL)
        for part in parts:
            if part.startswith("```"):
                match = re.match(r"```(?:\w+)?\n(.*?)\n```", part, re.DOTALL)
                code = match.group(1) if match else part
                yield CodeBlock(code, original_md=part)
            elif part.strip():
                yield Markdown(part)
        
        with Horizontal(id="bubble-actions"):
            yield Button("📋 Copy Response", id="copy-full-btn")
            yield Button("📄 Download PDF", id="download-pdf-btn")

    @on(Button.Pressed, "#download-pdf-btn")
    def action_download_pdf(self) -> None:
        try:
            path = export_markdown_to_pdf(self._response, query=self._query)
            self.app.notify(f"PDF saved to {path}", severity="info", title="PDF Exported")
        except Exception as e:
            self.app.notify(f"PDF Export error: {str(e)}", severity="error", title="Error")

    @on(Button.Pressed, "#copy-full-btn")
    def copy_full(self) -> None:
        import pyperclip
        try:
            pyperclip.copy(self._response)
            self.notify("Full response copied to clipboard!", severity="info", title="Success")
        except Exception as e:
            self.notify(f"Clipboard error: {str(e)}", severity="error", title="Error")

class CodeBlock(Static):
    """A widget for displaying code with an integrated copy button."""
    
    DEFAULT_CSS = """
    CodeBlock {
        margin: 1 0;
        background: $surface-darken-1;
        border: solid $primary-darken-3;
        height: auto;
    }
    CodeBlock .code-header {
        height: 1;
        background: $primary-darken-3;
        layout: horizontal;
        content-align: right middle;
    }
    CodeBlock .copy-icon-btn {
        min-width: 4;
        height: 1;
        padding: 0 1;
        background: transparent;
        border: none;
        color: $text-muted;
    }
    CodeBlock .copy-icon-btn:hover {
        color: $accent;
        background: $primary-darken-2;
    }
    CodeBlock Markdown {
        margin: 0;
        padding: 0;
    }
    """

    def __init__(self, code: str, original_md: str) -> None:
        super().__init__()
        self._code = code
        self._original_md = original_md

    def compose(self) -> ComposeResult:
        with Horizontal(classes="code-header"):
            yield Button("📋", classes="copy-icon-btn")
        yield Markdown(self._original_md)

    @on(Button.Pressed, ".copy-icon-btn")
    def copy_code(self) -> None:
        pyperclip.copy(self._code)
        self.app.notify("Code copied to clipboard", severity="info")

