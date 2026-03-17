from __future__ import annotations

import json
from datetime import datetime
from typing import Optional

import httpx
from ..core.config import API_BASE
from textual import on, work
from rich.markup import escape

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, ScrollableContainer, Vertical
from textual.widgets import (
    Footer,
    Header,
    Input,
    Label,
    ListItem,
    ListView,
    Static,
    Button,
    Select
)
from ..utils.config_manager import ConfigManager
import os

STREAM_ENDPOINT = f"{API_BASE}/chat"
CHATS_ENDPOINT = f"{API_BASE}/chats"
RESPONSES_ENDPOINT = f"{API_BASE}/responses"

def fmt_time(iso: str) -> str:
    try:
        dt = datetime.fromisoformat(iso)
        return dt.strftime("%b %d, %H:%M")
    except Exception:
        return iso


from .screens.config_modal import ConfigModal
from .widgets.media_items import ImageItem, VideoItem, SourceItem
from .widgets.chat_bubble import ChatBubble
from .widgets.live_response import LiveResponseWidget
class TrawlApp(App):
    """Trawl TUI."""

    TITLE = "trawl"
    SUB_TITLE = "AI Powered Knowledge Assistant"

    CSS = """
    /* ── Layout ── */
    #root {
        layout: horizontal;
        height: 1fr;
    }

    /* ── Left sidebar: chat list ── */
    #sidebar-left {
        width: 24;
        min-width: 20;
        background: $panel;
        border-right: tall $primary-darken-3;
        height: 1fr;
    }
    #sidebar-left-title {
        background: $primary-darken-2;
        color: $text;
        text-style: bold;
        padding: 0 2;
        height: 3;
        content-align: left middle;
    }
    #chat-list {
        height: 1fr;
        scrollbar-size: 1 1;
    }
    #chat-list > ListItem {
        padding: 1 2;
        background: $panel;
        border-bottom: solid $primary-darken-3;
        height: auto;
    }
    #chat-list > ListItem.--highlight {
        background: $boost;
    }
    #chat-list > ListItem:focus {
        background: $accent-darken-2;
    }
    #new-chat-btn {
        dock: bottom;
        height: 3;
        background: $accent;
        color: $text;
        text-style: bold;
        content-align: center middle;
        border-top: tall $accent-lighten-1;
    }
    #new-chat-btn:hover {
        background: $accent-lighten-1;
    }

    /* ── Centre: chat interface ── */
    #chat-panel {
        width: 1fr;
        height: 1fr;
        background: $background;
        border-right: tall $primary-darken-3;
    }
    #chat-panel-title {
        background: $primary-darken-2;
        color: $text;
        text-style: bold;
        padding: 0 2;
        height: 3;
        content-align: left middle;
    }
    #messages {
        height: 1fr;
        padding: 1 2;
        scrollbar-size: 1 1;
    }
    #input-row {
        dock: bottom;
        height: 5;
        padding: 1 2;
        background: $panel;
        border-top: tall $primary-darken-3;
        layout: horizontal;
    }
    #llm-switcher {
        width: 25;
        margin-right: 1;
    }
    #search-type-switcher {
        width: 15;
        margin-right: 1;
    }
    #query-input {
        width: 1fr;
        height: 3;
    }
    #send-btn {
        width: 10;
        height: 3;
        margin-left: 1;
        background: $accent;
        color: $text;
        text-style: bold;
        content-align: center middle;
        border: tall $accent-lighten-1;
    }
    #send-btn:hover {
        background: $accent-lighten-1;
    }

    /* ── Right sidebar: sources ── */
    #sidebar-right {
        width: 28;
        min-width: 22;
        background: $panel;
        height: 1fr;
    }
    #sidebar-right-title {
        background: $primary-darken-2;
        color: $text;
        text-style: bold;
        padding: 0 2;
        height: 3;
        content-align: left middle;
    }
    #sources-scroll {
        height: 1fr;
        padding: 1 1;
        scrollbar-size: 1 1;
    }
    #no-sources {
        color: $text-muted;
        text-style: italic;
        padding: 1 2;
    }

    #sidebar-right-images-title {
    background: $primary-darken-2;
    color: $text;
    text-style: bold;
    padding: 0 2;
    height: 3;
    content-align: left middle;
    }
    #images-scroll {
        height: 1fr;
        padding: 1 1;
        scrollbar-size: 1 1;
        border-bottom: tall $primary-darken-3;
    }
    #sidebar-right-videos-title {
        background: $primary-darken-2;
        color: $text;
        text-style: bold;
        padding: 0 2;
        height: 3;
        content-align: left middle;
    }
    #videos-scroll {
        height: 1fr;
        padding: 1 1;
        scrollbar-size: 1 1;
        border-bottom: tall $primary-darken-3;
    }
    #sources-scroll {
        height: 1fr;
        padding: 1 1;
        scrollbar-size: 1 1;
    }

    /* ── Empty state ── */
    #empty-state {
        height: 1fr;
        content-align: center middle;
        color: $text-muted;
        text-style: italic;
    }
    """

    BINDINGS = [
        Binding("ctrl+n", "new_chat", "New Chat"),
        Binding("ctrl+r", "refresh_chats", "Refresh"),
        Binding("ctrl+s", "settings", "Settings"),
        Binding("escape", "blur_input", "Blur"),
        Binding("ctrl+c", "quit", "Quit"),
    ]

    current_chat_id: Optional[str] = None
    _streaming: bool = False

    def compose(self) -> ComposeResult:
        yield Header()

        with Horizontal(id="root"):

            # Left sidebar
            with Vertical(id="sidebar-left"):
                yield Label("💬  Chats", id="sidebar-left-title")
                yield ListView(id="chat-list")
                yield Button("＋  New Chat", id="new-chat-btn", variant="success")

            # Centre chat panel
            with Vertical(id="chat-panel"):
                yield Label("trawl", id="chat-panel-title")
                with ScrollableContainer(id="messages"):
                    yield Static(
                        "Select a chat or start a new one  ↙",
                        id="empty-state",
                    )
                with Horizontal(id="input-row"):
                    yield Select([], id="llm-switcher", prompt="Select LLM")
                    yield Select([("General", "general"), ("Social", "social")], value="general", id="search-type-switcher")
                    yield Input(placeholder="Ask anything…", id="query-input")
                    yield Button("Send ↵", id="send-btn", variant="primary")

            # Right sidebar
            with Vertical(id="sidebar-right"):
                yield Label("🖼️  Images", id="sidebar-right-images-title")
                with ScrollableContainer(id="images-scroll"):
                    yield Static("No images yet.")
                yield Label("🎥  Videos", id="sidebar-right-videos-title")
                with ScrollableContainer(id="videos-scroll"):
                    yield Static("No videos yet.")
                yield Label("🔗  Sources", id="sidebar-right-title")
                with ScrollableContainer(id="sources-scroll"):
                    yield Static("No sources yet.")

        yield Footer()

    def on_mount(self) -> None:
        self.load_chats()
        self._populate_llm_switcher()
        if not ConfigManager.is_configured():
            self.action_settings()

    @work(exclusive=True)
    async def _populate_llm_switcher(self) -> None:
        """Fetch models from providers and populate the switcher."""
        config = ConfigManager.get_config()
        options = []
        
        def truncate_name(name: str, limit: int = 15) -> str:
            return name[:limit-3] + "..." if len(name) > limit else name

        ollama_url = config.get("ollama_base_url") or "http://localhost:11434"
        ollama_models = await ConfigManager.fetch_ollama_models(ollama_url)
        if ollama_models:
            options.append(("[Ollama]", "header-ollama"))
            for m in ollama_models:
                display_name = truncate_name(m)
                options.append((f"  {display_name}", f"ollama:{m}"))
            
        google_key = config.get("google_api_key") or os.getenv("GOOGLE_API_KEY")
        if google_key:
            google_models = await ConfigManager.fetch_google_models(google_key)
            if google_models:
                options.append(("[Google Gemini]", "header-google"))
                for m in google_models:
                    display_name = truncate_name(m)
                    options.append((f"  {display_name}", f"google:{m}"))
        
        switcher = self.query_one("#llm-switcher", Select)
        switcher.set_options(options)
        
        current_provider = config.get("provider", "ollama")
        current_model = config.get("model")
        if current_model:
            val = f"{current_provider}:{current_model}"
            if any(opt[1] == val for opt in options):
                switcher.value = val

    @on(Select.Changed, "#llm-switcher")
    def on_llm_changed(self, event: Select.Changed) -> None:
        if not isinstance(event.value, str):
            return
        if ":" not in event.value:
            return
        provider, model = event.value.split(":", 1)
        config = ConfigManager.get_config()
        config["provider"] = provider
        config["model"] = model
        ConfigManager.save_config(config)

    def action_settings(self) -> None:
        self.push_screen(ConfigModal(), callback=lambda _: self._populate_llm_switcher())

    @work(thread=True)
    def load_chats(self) -> None:
        """Fetch chat list from API and populate sidebar."""
        try:
            r = httpx.get(CHATS_ENDPOINT, timeout=5)
            chats = r.json()
        except Exception:
            chats = []

        self.call_from_thread(self._populate_chat_list, chats)

    def _populate_chat_list(self, chats: list[dict]) -> None:
        lv: ListView = self.query_one("#chat-list", ListView)
        lv.clear()
        for chat in chats:
            title = chat.get("title") or "Untitled"
            ts = fmt_time(chat.get("created_at", ""))
            item = ListItem(
                Label(f"{escape(title)}\n[dim]{escape(ts)}[/dim]"),
            )
            item.data = chat
            lv.append(item)

    @on(ListView.Selected, "#chat-list")
    def on_chat_selected(self, event: ListView.Selected) -> None:
        chat = getattr(event.item, "data", None)
        if chat:
            self.current_chat_id = str(chat["id"])
            self.load_chat_history(self.current_chat_id)
            title = chat.get("title") or "Untitled"
            self.query_one("#chat-panel-title", Label).update(f"💬  {title}")

    @work(thread=True)
    def load_chat_history(self, chat_id: str) -> None:
        """Load all responses for a chat from the API."""
        try:
            r = httpx.get(RESPONSES_ENDPOINT, params={"chat_id": chat_id}, timeout=5)
            responses = r.json()
        except Exception:
            responses = []
        self.call_from_thread(self._render_history, responses)

    def _render_history(self, responses: list[dict]) -> None:
        messages = self.query_one("#messages", ScrollableContainer)
        messages.remove_children()

        if not responses:
            messages.mount(Static("No messages yet."))
            return

        all_sources: list[str] = []
        all_images: list[str] = []
        all_videos: list[str] = []

        for resp in responses:
            query = resp.get("query", "")
            content = resp.get("response", "")
            sources = resp.get("sources") or []
            images = resp.get("image_urls") or []
            videos = resp.get("video_urls") or []
            all_sources.extend(sources)
            all_images.extend(images)
            all_videos.extend(videos)
            messages.mount(ChatBubble(query, content))

        messages.scroll_end(animate=False)
        self._update_sources(all_sources)
        self._update_images(all_images)
        self._update_videos(all_videos)

    def _update_images(self, urls: list[str]) -> None:
        scroll = self.query_one("#images-scroll", ScrollableContainer)
        scroll.remove_children()
        if not urls:
            scroll.mount(Static("No images yet."))
            return
        for i, url in enumerate(urls, 1):
            scroll.mount(ImageItem(i, url))

    def _update_videos(self, urls: list[str]) -> None:
        scroll = self.query_one("#videos-scroll", ScrollableContainer)
        scroll.remove_children()
        if not urls:
            scroll.mount(Static("No videos yet."))
            return
        for i, url in enumerate(urls, 1):
            scroll.mount(VideoItem(i, url))


    def _update_sources(self, urls: list[str]) -> None:
        scroll = self.query_one("#sources-scroll", ScrollableContainer)
        scroll.remove_children()
        if not urls:
            scroll.mount(Static("No sources yet."))
            return
        for i, url in enumerate(urls, 1):
            scroll.mount(SourceItem(i, url))

    @on(Input.Submitted, "#query-input")
    def on_input_submitted(self, event: Input.Submitted) -> None:
        self._send_query(event.value)

    @on(Button.Pressed, "#send-btn")
    def on_send_clicked(self) -> None:
        inp = self.query_one("#query-input", Input)
        self._send_query(inp.value)

    def _send_query(self, query: str) -> None:
        query = query.strip()
        if not query or self._streaming:
            return
        inp = self.query_one("#query-input", Input)
        inp.value = ""
        inp.disabled = True
        self._streaming = True
        self.stream_response(query)

    @work(exclusive=True)
    async def stream_response(self, query: str) -> None:
        """Stream SSE events from the API and update the UI live."""

        messages = self.query_one("#messages", ScrollableContainer)

        for w in messages.children:
            if isinstance(w, Static) and not isinstance(w, (ChatBubble, LiveResponseWidget)):
                await w.remove()

        live = LiveResponseWidget()
        await messages.mount(live)
        live.set_query(query)
        messages.scroll_end(animate=True)

        current_sources: list[str] = []
        search_type = self.query_one("#search-type-switcher", Select).value
        payload = {"query": query, "type": search_type}
        if self.current_chat_id:
            payload["chat_id"] = self.current_chat_id

        try:
            async with httpx.AsyncClient(timeout=120) as client:
                async with client.stream(
                    "POST",
                    STREAM_ENDPOINT,
                    json=payload,
                    headers={"Accept": "text/event-stream"},
                ) as resp:

                    async for line in resp.aiter_lines():
                        if not line.startswith("data:"):
                            continue
                        raw = line[5:].strip()
                        if not raw:
                            continue

                        try:
                            data = json.loads(raw)
                        except json.JSONDecodeError:
                            continue

                        event_type = data.get("type")

                        if event_type == "status":
                            live.set_status(data.get("message", ""))

                        elif event_type == "enhanced_query":
                            live.set_status(f"Searching: {data.get('text', '')}")

                        elif event_type == "urls":
                            current_sources = data.get("urls", [])
                            self._update_sources(current_sources)

                        elif event_type == "content":
                            live.clear_status()
                            live.append_token(data.get("text", ""))
                            messages.scroll_end(animate=False)

                        elif event_type == "title":
                            title_text = data.get("text", query[:40])
                            self.query_one("#chat-panel-title", Label).update(
                                f"💬  {title_text}"
                            )
                        
                        elif event_type == "image_urls":
                            self._update_images(data.get("image_urls", []))

                        elif event_type == "video_urls":
                            self._update_videos(data.get("video_urls", []))

                        elif event_type == "done":
                            chat_id = data.get("chat_id")
                            if chat_id:
                                self.current_chat_id = chat_id
                            live.clear_status()
                            live.show_copy_buttons()
                            self.load_chats()

        except Exception as e:
            live.set_status(f"Error: {e}")

        finally:
            self._streaming = False
            inp = self.query_one("#query-input", Input)
            inp.disabled = False
            inp.focus()


    def action_new_chat(self) -> None:
        self.current_chat_id = None
        messages = self.query_one("#messages", ScrollableContainer)
        messages.remove_children()
        messages.mount(Static("Start a new conversation ↓"))
        self._update_sources([])
        self._update_images([])
        self._update_videos([])
        self.query_one("#chat-panel-title", Label).update("")
        self.query_one("#query-input", Input).focus()

    def action_refresh_chats(self) -> None:
        self.load_chats()

    def action_blur_input(self) -> None:
        self.query_one("#query-input", Input).blur()

    @on(Button.Pressed, "#new-chat-btn")
    def on_new_chat_clicked(self) -> None:
        self.action_new_chat()


def run_tui() -> None:
    TrawlApp().run()

if __name__ == "__main__":
    run_tui()