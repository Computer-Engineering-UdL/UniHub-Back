# UniRoom - Backend

[![Python](https://img.shields.io/badge/Python-3.13-blue?logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.118.0-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0.43-red?logo=sqlalchemy&logoColor=white)](https://www.sqlalchemy.org/)
[![Pydantic](https://img.shields.io/badge/Pydantic-2.11.0-E92063?logo=pydantic&logoColor=white)](https://docs.pydantic.dev/)
[![Uvicorn](https://img.shields.io/badge/Uvicorn-latest-2094f3?logo=uvicorn&logoColor=white)](https://www.uvicorn.org/)
[![uv](https://img.shields.io/badge/uv-package%20manager-purple?logo=python&logoColor=white)](https://github.com/astral-sh/uv)
[![Ruff](https://img.shields.io/badge/Ruff-0.13.2-orange?logo=ruff&logoColor=white)](https://docs.astral.sh/ruff/)
[![Docker](https://img.shields.io/badge/Docker-enabled-2496ED?logo=docker&logoColor=white)](https://www.docker.com/)
[![Conventional Commits](https://img.shields.io/badge/Conventional%20Commits-1.0.0-%23FE5196?logo=conventionalcommits&logoColor=white)](https://conventionalcommits.org)

## Features

- Oops! Pending section...

## Tech Stack

- **Framework**: FastAPI
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Authentication**: JWT tokens
- **Validation**: Pydantic v2
- **Package Manager**: uv
- **Containerization**: Docker & Docker Compose
- **Testing**: pytest
- **Code Quality**: Ruff (linting & formatting)

## Prerequisites

- [Python](https://www.python.org) `>=3.13`
- [uv](https://github.com/astral-sh/uv) (recommended) or pip
- [Docker](https://www.docker.com) (optional, for containerized deployment)
- [PostgreSQL](https://www.postgresql.org) `>=18` (if running locally)

## Installation

### Using uv (Recommended)

```bash
git clone https://github.com/Computer-Engineering-UdL/UniRoom-Back
cd UniRoom-Back
uv sync
```

## Configuration

Create a `.env` file in the root directory:

```env
DATABASE_URL=postgresql://user:password@localhost:5432/uniroom
SECRET_KEY=your-secret-key-here
API_V1_STR=/api/v1
PROJECT_NAME=UniRoom API
```

## Running the project

### Development Server

```bash
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8080
```

### Using Docker

```bash
docker build -t uniroom-backend .
docker run -p 8080:8080 uniroom-backend
```

The API will be available at `http://localhost:8080`

API documentation will be available at:
- Swagger UI: `http://localhost:8080/docs`
- ReDoc: `http://localhost:8080/redoc`

## Development

### Running Tests

```bash
uv run pytest
```

### Code Formatting

```bash
uv run ruff format .
```

### Linting

```bash
uv run ruff check .
```

### Adding Dependencies

```bash
# Add a package
uv add package-name

# Add a dev dependency
uv add --dev package-name
```

## Project Structure

```
app/
├── api/
│   └── v1/
│       └── endpoints/      # API route handlers
├── core/                   # Core configuration
├── crud/                   # Database operations
├── models/                 # Data models (Pydantic & SQLAlchemy)
├── services/              # Business logic
└── main.py                # Application entry point
tests/                     # Test files
```

## Authors

- [Aniol0012](https://github.com/Aniol0012)
- [TheSmuks](https://github.com/TheSmuks)
- [carless7](https://github.com/carless7)
- [cesarcres](https://github.com/cesarcres)
- [JerzyLeg](https://github.com/JerzyLeg)
