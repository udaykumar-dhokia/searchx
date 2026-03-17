from rich.markup import escape
from textual.reactive import reactive
from textual.widgets import Static

class StatusBar(Static):
    """Thin status strip shown inside the chat panel."""

    DEFAULT_CSS = """
    StatusBar {
        height: 1;
        background: $surface;
        color: $text-muted;
        padding: 0 2;
        text-style: italic;
    }
    """

    status: reactive[str] = reactive("")

    def render(self) -> str:
        return f"⟳  {escape(self.status)}" if self.status else ""

