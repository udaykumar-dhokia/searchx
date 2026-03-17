from rich.markup import escape
from textual.widgets import Static

class ImageItem(Static):
    """Clickable image URL item with thumbnail placeholder."""

    DEFAULT_CSS = """
    ImageItem {
        height: auto;
        padding: 0 1;
        margin-bottom: 1;
        border-left: thick $warning;
        color: $text;
        background: $surface;
    }
    ImageItem:hover {
        background: $boost;
    }
    """

    def __init__(self, index: int, url: str) -> None:
        super().__init__()
        self._index = index
        self._url = url

    def render(self) -> str:
        domain = escape(self._url.split("/")[2] if "//" in self._url else self._url)
        short_url = self._url[:55] + ("…" if len(self._url) > 55 else "")
        safe_short = escape(short_url)

        return (
            f"[{self._index}] 🖼  {domain}\n"
            f"[dim][link='{self._url}']{safe_short}[/link][/dim]"
        )

    def on_click(self) -> None:
        import webbrowser
        webbrowser.open(self._url)

class VideoItem(Static):
    """Clickable video URL item."""

    DEFAULT_CSS = """
    VideoItem {
        height: auto;
        padding: 0 1;
        margin-bottom: 1;
        border-left: thick $success;
        color: $text;
        background: $surface;
    }
    VideoItem:hover {
        background: $boost;
    }
    """

    def __init__(self, index: int, url: str) -> None:
        super().__init__()
        self._index = index
        self._url = url

    def render(self) -> str:
        domain = escape(self._url.split("/")[2] if "//" in self._url else self._url)
        short_url = self._url[:55] + ("…" if len(self._url) > 55 else "")
        safe_short = escape(short_url)

        return (
            f"[{self._index}] 🎥  {domain}\n"
            f"[dim][link='{self._url}']{safe_short}[/link][/dim]"
        )

    def on_click(self) -> None:
        import webbrowser
        webbrowser.open(self._url)

class SourceItem(Static):
    """Single source link in the right sidebar."""

    DEFAULT_CSS = """
    SourceItem {
        height: auto;
        padding: 0 1;
        margin-bottom: 1;
        border-left: thick $accent;
        color: $text;
        background: $surface;
    }
    SourceItem:hover {
        background: $boost;
    }
    """

    def __init__(self, index: int, url: str) -> None:
        super().__init__()
        self._index = index
        self._url = url

    def render(self) -> str:
        domain = escape(self._url.split("/")[2] if "//" in self._url else self._url)
        short_url = self._url[:60] + ("…" if len(self._url) > 60 else "")
        safe_short = escape(short_url)

        return f"[{self._index}] {domain}\n[dim][link='{self._url}']{safe_short}[/link][/dim]"

    def on_click(self) -> None:
        import webbrowser
        webbrowser.open(self._url)


