from textual import on, work
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Input, Label, RadioButton, RadioSet, Select

from trawl.utils.config_manager import ConfigManager

class ConfigModal(ModalScreen):
    """Configuration modal for LLM settings."""

    DEFAULT_CSS = """
    ConfigModal {
        align: center middle;
    }
    #modal-container {
        width: 60;
        height: auto;
        border: thick $primary;
        background: $surface;
        padding: 1 2;
    }
    #modal-title {
        text-align: center;
        text-style: bold;
        margin-bottom: 1;
    }
    .config-label {
        margin-top: 1;
        color: $text-muted;
    }
    #provider-select {
        layout: horizontal;
        height: 3;
        margin-bottom: 1;
    }
    #button-row {
        margin-top: 2;
        height: 3;
        layout: horizontal;
    }
    #save-btn {
        width: 1fr;
    }
    #cancel-btn {
        width: 15;
        margin-left: 1;
    }
    #sel-model {
        margin-top: 1;
    }
    """

    BINDINGS = [
        Binding("escape", "dismiss", "Cancel"),
    ]

    def compose(self) -> ComposeResult:
        config = ConfigManager.get_config()
        provider = config.get("provider", "ollama")
        
        with Vertical(id="modal-container"):
            yield Label("⚙️ trawl Settings", id="modal-title")
            
            yield Label("LLM Provider", classes="config-label")
            with RadioSet(id="provider-select"):
                yield RadioButton("Ollama", id="opt-ollama", value=(provider == "ollama"))
                yield RadioButton("Google", id="opt-google", value=(provider == "google"))
            
            yield Label("Ollama Base URL", id="lbl-ollama-url", classes="config-label")
            yield Input(
                config.get("ollama_base_url", "http://localhost:11434"),
                placeholder="http://localhost:11434",
                id="in-ollama-url"
            )
            
            yield Label("Google API Key", id="lbl-google-key", classes="config-label")
            yield Input(
                config.get("google_api_key", ""),
                placeholder="Enter Gemini API Key",
                id="in-google-key",
                password=True
            )
            
            yield Label("Choose Model", classes="config-label")
            yield Select([], id="sel-model", prompt="Select a model...")
            
            with Horizontal(id="button-row"):
                yield Button("Save", variant="success", id="save-btn")
                yield Button("Cancel", id="cancel-btn")

    @on(Button.Pressed, "#cancel-btn")
    def cancel_settings(self) -> None:
        self.dismiss()

    def on_mount(self) -> None:
        self._update_visibility()
        self._load_models()

    def _update_visibility(self) -> None:
        provider = "google" if self.query_one("#opt-google", RadioButton).value else "ollama"
        is_google = (provider == "google")
        
        self.query_one("#lbl-ollama-url").display = not is_google
        self.query_one("#in-ollama-url").display = not is_google
        
        self.query_one("#lbl-google-key").display = is_google
        self.query_one("#in-google-key").display = is_google

    @on(RadioSet.Changed)
    def on_provider_changed(self) -> None:
        self._update_visibility()
        self._load_models()

    @work(exclusive=True)
    async def _load_models(self) -> None:
        provider = "google" if self.query_one("#opt-google", RadioButton).value else "ollama"
        models = []
        
        if provider == "ollama":
            url = self.query_one("#in-ollama-url", Input).value
            models = await ConfigManager.fetch_ollama_models(url)
        else:
            key = self.query_one("#in-google-key", Input).value
            if key:
                models = await ConfigManager.fetch_google_models(key)
        
        if models:
            def truncate_name(name: str, limit: int = 22) -> str:
                return name[:limit-3] + "..." if len(name) > limit else name

            options = [(truncate_name(m), m) for m in models]
            self.query_one("#sel-model", Select).set_options(options)
            
            current = ConfigManager.get_config().get("model")
            if current in models:
                self.query_one("#sel-model", Select).value = current

    @on(Button.Pressed, "#save-btn")
    def save_settings(self) -> None:
        provider = "google" if self.query_one("#opt-google", RadioButton).value else "ollama"
        config = {
            "provider": provider,
            "ollama_base_url": self.query_one("#in-ollama-url", Input).value,
            "google_api_key": self.query_one("#in-google-key", Input).value,
            "model": self.query_one("#sel-model", Select).value
        }
        ConfigManager.save_config(config)
        self.dismiss()

