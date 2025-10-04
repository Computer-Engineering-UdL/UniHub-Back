# UniRoom - Backend

[![Python](https://img.shields.io/badge/Python-3.13-blue?logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.118.0-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0.43-red?logo=sqlalchemy&logoColor=white)](https://www.sqlalchemy.org/)
[![uv](https://img.shields.io/badge/uv-package%20manager-purple?logo=python&logoColor=white)](https://github.com/astral-sh/uv)
[![pytest](https://img.shields.io/badge/pytest-8.0+-0A9EDC?logo=pytest&logoColor=white)](https://pytest.org/)
[![Docker](https://img.shields.io/badge/Docker-enabled-2496ED?logo=docker&logoColor=white)](https://www.docker.com/)

## Features

- Oops! Pending section...

## Tech Stack

- **Framework**: FastAPI
- **Database**: PostgreSQL with SQLAlchemy
- **Package Manager**: uv
- **Testing**: pytest
- **Code Quality**: Ruff
- **CI/CD**: GitHub Actions

## Getting Started

### 1. Install uv

**macOS/Linux:**
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

**Windows (PowerShell):**
```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

**Alternative (using pip):**
```bash
pip install uv
```

> **Note:** After installation, restart your terminal or run `source ~/.bashrc` (Linux/macOS) or restart PowerShell (Windows).

### 2. Clone and Install

```bash
git clone https://github.com/Computer-Engineering-UdL/UniRoom-Back
cd UniRoom-Back
uv sync
```

### 3. Configure Environment

Create a `.env` file:

```env
DATABASE_URL=postgresql://user:password@localhost:5432/uniroom
SECRET_KEY=your-secret-key-here
API_V1_STR=/api/v1
PROJECT_NAME=UniRoom API
```

### 4. Run the Server

```bash
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8080
```

Visit:
- API: `http://localhost:8080`
- Docs: `http://localhost:8080/docs`

## Development

### Run Tests

```bash
uv run pytest
```

### Check Code Quality

```bash
# Format code
uv run ruff format .

# Check for issues
uv run ruff check .
```

### Add Dependencies

```bash
# Production dependency
uv add package-name

# Development dependency
uv add --dev package-name
```

## Docker

```bash
# Build image
docker build -t uniroom-backend .

# Run container
docker run -p 8080:8080 uniroom-backend
```

## Project Structure

```
app/
├── api/v1/endpoints/    # API routes
├── core/                # Configuration
├── crud/                # Database operations
├── models/              # Data models
├── services/            # Business logic
└── main.py              # Entry point
tests/                   # Tests
```

## Authors

- [Aniol0012](https://github.com/Aniol0012)
- [TheSmuks](https://github.com/TheSmuks)
- [carless7](https://github.com/carless7)
- [cesarcres](https://github.com/cesarcres)
- [JerzyLeg](https://github.com/JerzyLeg)
