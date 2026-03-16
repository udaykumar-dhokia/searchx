from __future__ import annotations

import asyncio
import json
import webbrowser
from typing import List, Optional, Dict
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session
from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical, ScrollableContainer
from textual.message import Message
from textual.reactive import reactive
from textual.widgets import Footer, Header, Input, Label, ListItem, ListView, Static, Button, Markdown
from textual.widget import Widget
from textual import work

from .db.database import engine
from .models.chat import Chat
from .models.response import Response
from .services.invoke_chat import invoke_chat
from .utils.insert_chat import insert_chat

class ChatListItem(ListItem):
    """List item representing a single chat."""
    def __init__(self, chat_id: UUID, title: str) -> None:
        super().__init__(Label(title))
        self.chat_id = chat_id

class ChatSidebar(Vertical):
    """Left sidebar listing all chats."""
    class ChatSelected(Message):
        def __init__(self, chat_id: UUID):
            self.chat_id = chat_id
            super().__init__()

    class NewChatRequested(Message):
        pass

    def compose(self) -> ComposeResult:
        yield Label("SearchX", id="chats-title")
        yield Button("+ New Thread", id="new-chat-btn")
        self.list_view = ListView(id="chats-list")
        yield self.list_view

    async def on_mount(self) -> None:
        await self.refresh_chats()

    async def refresh_chats(self) -> None:
        if not hasattr(self, "list_view"): return
        
        current_id = None
        if self.list_view.index is not None and self.list_view.children:
            item = self.list_view.children[self.list_view.index]
            if isinstance(item, ChatListItem):
                current_id = item.chat_id

        self.list_view.clear()
        with Session(engine) as session:
            chats: List[Chat] = session.execute(
                select(Chat).order_by(Chat.created_at.desc())
            ).scalars().all()

        for chat in chats:
            title = chat.title or str(chat.id)[:8]
            item = ChatListItem(chat.id, title)
            self.list_view.append(item)

        if current_id:
            for i, child in enumerate(self.list_view.children):
                if isinstance(child, ChatListItem) and child.chat_id == current_id:
                    self.list_view.index = i
                    break

    async def on_list_view_selected(self, event: ListView.Selected) -> None:
        if isinstance(event.item, ChatListItem):
            self.post_message(self.ChatSelected(event.item.chat_id))

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "new-chat-btn":
            self.post_message(self.NewChatRequested())

class SourceCard(Static):
    """Compact card for research sources, mimicking Perplexity search results."""
    def __init__(self, url: str):
        super().__init__(classes="source-card")
        self.url = url

    def compose(self) -> ComposeResult:
        domain = self.url.replace("https://", "").replace("http://", "").split("/")[0]
        with Horizontal():
            yield Label("🌐", classes="source-icon")
            with Vertical():
                yield Label(domain, classes="source-domain")
                yield Label(self.url, classes="source-full-url")

    def on_click(self) -> None:
        webbrowser.open(self.url)

class SourcesSidebar(Vertical):
    """Right sidebar listing all sources in a clean, compact grid."""
    sources: reactive[List[str]] = reactive([])

    def compose(self) -> ComposeResult:
        yield Label("Sources", id="sources-title")
        self.container = Vertical(id="sources-container")
        yield self.container

    def watch_sources(self, sources: List[str]) -> None:
        try:
            container = self.query_one("#sources-container", Vertical)
            container.remove_children()
            for url in sources:
                container.mount(SourceCard(url))
        except Exception:
            pass

class ResearchStep(Static):
    """A single step in the research process (Thinking state)."""
    completed = reactive(False)
    
    def __init__(self, label: str):
        super().__init__(classes="research-step")
        self.label_text = label

    def compose(self) -> ComposeResult:
        self.icon = Label("○", classes="step-icon")
        yield self.icon
        yield Label(self.label_text, classes="step-label")

    def watch_completed(self, completed: bool) -> None:
        if hasattr(self, "icon"):
            self.icon.update("●" if completed else "○")
            if completed:
                self.add_class("completed")

class ThinkingWidget(Vertical):
    """Container for discrete research steps."""
    def compose(self) -> ComposeResult:
        self.steps: Dict[str, ResearchStep] = {}
        yield Label("Researching...", id="thinking-header")
    
    def add_step(self, id: str, label: str):
        if id not in self.steps:
            step = ResearchStep(label)
            self.steps[id] = step
            self.mount(step)
    
    def complete_step(self, id: str):
        if id in self.steps:
            self.steps[id].completed = True

class StreamingMarkdown(Static):
    """Markdown widget with premium streaming feel."""
    content: reactive[str] = reactive("")

    def compose(self) -> ComposeResult:
        yield Markdown(self.content or " ")

    def watch_content(self, new_content: str) -> None:
        try:
            md = self.query_one(Markdown)
            if md:
                md.update(new_content)
        except Exception:
            pass

class MessageWidget(Static):
    """Message widget refined for Perplexity aesthetic."""
    def __init__(self, role: str, content: str = ""):
        super().__init__(classes=f"message message-{role}")
        self.role = role
        self.content = content

    def compose(self) -> ComposeResult:
        if self.role == "assistant":
            yield StreamingMarkdown(self.content, classes="message-content")
        else:
            yield Label(self.content, classes="message-content user-query")

    def update_content(self, new_text: str) -> None:
        self.content = new_text
        try:
            sm = self.query_one(StreamingMarkdown)
            sm.content = new_text
        except Exception:
            pass

class ChatView(Vertical):
    """Main chat interface with Perplexity-style Prompt Bar and flow."""
    chat_id: Optional[UUID] = None
    is_streaming: reactive[bool] = reactive(False)

    class SourcesUpdated(Message):
        def __init__(self, sources: List[str]):
            self.sources = sources
            super().__init__()

    def compose(self) -> ComposeResult:
        with ScrollableContainer(id="chat-history"):
            self.history_container = Vertical(id="history-inner")
            yield self.history_container
        
        with Horizontal(id="prompt-bar-container"):
            with Container(id="prompt-input-wrapper"):
                yield Input(placeholder="Ask anything...", id="chat-input")

    async def on_mount(self) -> None:
        self.query_one("#chat-input").focus()

    async def load_chat(self, chat_id: UUID) -> None:
        self.chat_id = chat_id
        try:
            container = self.query_one("#history-inner", Vertical)
            container.remove_children()
            
            with Session(engine) as session:
                responses: List[Response] = session.execute(
                    select(Response)
                    .where(Response.chat_id == chat_id)
                    .order_by(Response.created_at.asc())
                ).scalars().all()

            sources = []
            for resp in responses:
                if resp.query:
                    container.mount(MessageWidget("user", resp.query))
                if resp.response:
                    container.mount(MessageWidget("assistant", resp.response))
                if resp.sources:
                    for url in resp.sources:
                        if url not in sources:
                            sources.append(url)
            
            self.post_message(self.SourcesUpdated(sources))
            self.scroll_to_end()
        except Exception:
            pass

    def scroll_to_end(self) -> None:
        try:
            container = self.query_one("#chat-history", ScrollableContainer)
            container.scroll_end(animate=True)
        except Exception:
            pass

    @work(exclusive=True)
    async def handle_submit(self, query: str) -> None:
        if self.chat_id is None:
            self.chat_id = await insert_chat()
            await self.app.chat_sidebar.refresh_chats()

        history = self.query_one("#history-inner", Vertical)
        history.mount(MessageWidget("user", query))
        
        thinking = ThinkingWidget(classes="thinking-view")
        history.mount(thinking)
        thinking.add_step("enhance", "Understanding query")
        self.scroll_to_end()

        self.is_streaming = True
        
        assistant_msg = MessageWidget("assistant", "")
        history.mount(assistant_msg)

        try:
            async for chunk in invoke_chat(query=query, chat_id=self.chat_id):
                chunk_str = str(chunk).strip()
                if not chunk_str: continue
                
                parts = chunk_str.split("data:")
                for part in parts:
                    clean_part = part.strip()
                    if not clean_part: continue
                    try:
                        data = json.loads(clean_part)
                        etype = data.get("type")
                        if etype == "status":
                            msg = data.get("message", "")
                            if "Searching" in msg:
                                thinking.complete_step("enhance")
                                thinking.add_step("search", "Searching the web")
                            elif "Reading" in msg:
                                thinking.complete_step("search")
                                thinking.add_step("read", "Reading sources")
                            elif "Generating" in msg:
                                thinking.complete_step("read")
                                thinking.add_step("gen", "Synthesizing answer")
                                thinking.complete_step("gen")
                        elif etype == "urls":
                            urls = data.get("urls", [])
                            if urls:
                                self.post_message(self.SourcesUpdated(urls))
                        elif etype == "content":
                            text = data.get("text", "")
                            if text:
                                assistant_msg.update_content(assistant_msg.content + text)
                                self.call_after_refresh(self.scroll_to_end)
                    except Exception:
                        continue

        except Exception as e:
            history.mount(Label(f"Error: {str(e)}", classes="error-text"))
        
        for step_id in thinking.steps: thinking.complete_step(step_id)
        
        self.is_streaming = False
        self.scroll_to_end()
        await self.app.chat_sidebar.refresh_chats()

    async def on_input_submitted(self, event: Input.Submitted) -> None:
        if self.is_streaming: return
        query = event.value.strip()
        if not query: return
        event.input.value = ""
        self.handle_submit(query)

class ResearchTUI(App):
    """SearchX Preplexity-Style Premium Research Agent TUI."""
    CSS_PATH = "tui.css"
    BINDINGS = [
        ("q", "quit", "Quit"),
        ("n", "new_chat", "New Chat"),
        ("r", "refresh", "Refresh"),
    ]

    def compose(self) -> ComposeResult:
        yield Header()
        with Horizontal(id="main"):
            self.chat_sidebar = ChatSidebar(id="chat-sidebar")
            self.chat_view = ChatView(id="chat-view")
            self.sources_sidebar = SourcesSidebar(id="sources-sidebar")
            yield self.chat_sidebar
            yield self.chat_view
            yield self.sources_sidebar
        yield Footer()

    def on_mount(self) -> None:
        self.query_one("#chat-input").focus()

    async def action_refresh(self) -> None:
        await self.chat_sidebar.refresh_chats()
        if self.chat_view.chat_id:
            await self.chat_view.load_chat(self.chat_view.chat_id)

    async def action_new_chat(self) -> None:
        self.chat_view.chat_id = None
        try:
            history = self.chat_view.query_one("#history-inner", Vertical)
            history.remove_children()
        except:
            pass
        self.chat_view.post_message(ChatView.SourcesUpdated([]))
        self.query_one("#chat-input").focus()

    def on_chat_sidebar_chat_selected(self, message: ChatSidebar.ChatSelected) -> None:
        asyncio.create_task(self.chat_view.load_chat(message.chat_id))

    def on_chat_sidebar_new_chat_requested(self, message: ChatSidebar.NewChatRequested) -> None:
        asyncio.create_task(self.action_new_chat())

    def on_chat_view_sources_updated(self, message: ChatView.SourcesUpdated) -> None:
        self.sources_sidebar.sources = message.sources

def run_tui() -> None:
    ResearchTUI().run()
