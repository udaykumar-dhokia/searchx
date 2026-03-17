# Contributing to trawl

Thank you for your interest in contributing to trawl! We welcome contributions from the community.

## Development Setup

### Prerequisites

- Python 3.10 or higher
- [uv](https://github.com/astral-sh/uv) package manager
- PostgreSQL database
- Ollama (optional, for local LLM support)

### Installation

1. Fork and clone the repository:

   ```bash
   git clone https://github.com/udaykumar-dhokia/trawl.git
   cd trawl
   ```

2. Install dependencies:

   ```bash
   uv sync
   ```

3. Set up your environment:

   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

4. Run tests:
   ```bash
   uv run pytest
   ```

## Development Workflow

1. Create a feature branch: `git checkout -b feature/your-feature-name`
2. Make your changes
3. Run tests: `uv run pytest`
4. Run linting: `uv run ruff check .`
5. Format code: `uv run ruff format .`
6. Commit your changes: `git commit -m "Add your feature"`
7. Push to your fork: `git push origin feature/your-feature-name`
8. Create a Pull Request

## Code Style

This project uses:

- **Ruff** for linting and formatting
- **MyPy** for type checking
- **Black** for code formatting (via Ruff)

Run all checks with:

```bash
uv run ruff check .
uv run ruff format .
uv run mypy .
```

## Project Structure

```
trawl/
├── cli.py              # Command-line interface
├── main.py             # FastAPI application
├── tui_app.py          # Textual TUI interface
├── core/               # Core configuration and utilities
├── db/                 # Database models and connections
├── models/             # SQLAlchemy models
├── schemas/            # Pydantic schemas
├── services/           # Business logic services
└── utils/              # Utility functions

tests/                  # Test suite
docs/                   # Documentation
examples/               # Usage examples
scripts/                # Utility scripts
```

## Testing

Add tests for new features in the `tests/` directory. Run tests with:

```bash
uv run pytest
```

## Documentation

Update documentation in the `docs/` directory and README.md as needed.

## Commit Messages

Use conventional commit format:

- `feat:` for new features
- `fix:` for bug fixes
- `docs:` for documentation
- `style:` for formatting
- `refactor:` for code restructuring
- `test:` for tests
- `chore:` for maintenance

## Issues

- Check existing issues before creating new ones
- Use issue templates when available
- Provide detailed reproduction steps for bugs

## License

By contributing to trawl, you agree that your contributions will be licensed under the MIT License.
