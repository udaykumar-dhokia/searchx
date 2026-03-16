# searchx - on-premise ai powered research assistant

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=flat&logo=fastapi)](https://fastapi.tiangolo.com/)
[![Textual](https://img.shields.io/badge/Built%20with-Textual-ff00ff.svg)](https://textual.textualize.io/)

**searchx** is a high-performance, On-Premise AI Powered Research Assistant with terminal interface. Inspired by modern search engines like Perplexity, it brings deep-dive research capabilities directly to your command line.

![SearchX Demo Mockup](./demo.svg)

---

## Features

- **Live Streaming Responses**: Real-time markdown streaming for immediate feedback.
- **Visual Research Insights**: Dedicated image and video sidebar displaying relevant visuals discovered during research.
- **Smart Research Orchestration**: Automatically searches the web, processes multiple sources, and synthesizes answers.
- **Source Citations**: Interactive sidebar displaying all research sources with site-specific icons/emojis.
- **Persistent Threads**: Full chat history support powered by PostgreSQL and SQLAlchemy.
- **Premium TUI**: A sleek, customizable terminal interface with both Light and Dark themes.
- **Fast-API Backend**: Robust, asynchronous backend architecture for multi-step research.

---

## Technology Stack

- **Frontend**: [Textual](https://textual.textualize.io/) (Rich TUI Framework)
- **Backend**: [FastAPI](https://fastapi.tiangolo.com/) (Asynchronous Python Web Framework)
- **Database**: [PostgreSQL](https://www.postgresql.org/) with [SQLAlchemy](https://www.sqlalchemy.org/) ORM
- **LLM Engine**: Integration with Google Gemini / Ollama
- **Search Engine**: [SearxNG](https://github.com/searxng/searxng)

---

## Quick Start

### 1. Requirements

Ensure you have [Python 3.10+](https://www.python.org/downloads/) and [uv](https://github.com/astral-sh/uv) installed.

### 2. Installation

```bash
git clone https://github.com/udaykumar-dhokia/searchx.git
cd searchx
uv sync
```

### 3. Configuration

Create a `.env` file in the root directory:

```env
DATABASE_URL=postgresql://user:pass@localhost:5432/searchx_db
SEARXNG_BASE_URL=http://localhost:8080
GOOGLE_API_KEY=your_gemini_api_key
DEFAULT_MODEL=gemini-1.5-pro
API_BASE=http://localhost:8000
```

### 4. Running the Application

#### Option A: Using Docker Compose (Recommended)

This will start everything (Database, SearXNG, Redis, and Backend) automatically.

```bash
docker compose up -d
```

Once the containers are up, launch the Research TUI:

```bash
uv run python src/tui_app.py
```

#### Option B: Manual Startup

Launch the FastAPI backend:

```bash
uv run fastapi run src/main.py
```

Launch the Research TUI:

```bash
uv run python src/tui_app.py
```

---

## Keyboard Shortcuts

| Shortcut   | Action            |
| :--------- | :---------------- |
| `Ctrl + N` | New Chat          |
| `Ctrl + R` | Refresh Chat List |
| `Escape`   | Blur / Exit Input |
| `Ctrl + C` | Quit Application  |

---

## 🤝 Contributing

Contributions are welcome! Whether it's adding a new search provider, improving the UI, or fixing bugs, please feel free to fork the repo and submit a PR.

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

<p align="center">Built with ❤️ by udthedeveloper</p>
