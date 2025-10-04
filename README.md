# UniRoom - Backend

[![Python](https://img.shields.io/badge/Python-3.13-blue?logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.118.0-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0.43-red?logo=sqlalchemy&logoColor=white)](https://www.sqlalchemy.org/)
[![uv](https://img.shields.io/badge/uv-package%20manager-purple?logo=python&logoColor=white)](https://github.com/astral-sh/uv)
[![pytest](https://img.shields.io/badge/pytest-8.0+-0A9EDC?logo=pytest&logoColor=white)](https://pytest.org/)
[![Docker](https://img.shields.io/badge/Docker-enabled-2496ED?logo=docker&logoColor=white)](https://www.docker.com/)

## Introduction

This project is part of the first semester project course at
the [University of Lleida (UdL)](https://www.udl.cat/ca/en/). It serves as the backend
for the UniRoom application. This API includes the following main features:

- Configurable user profiles, matching their preferences with listings and communities
- Housing search (rooms/apartments) with filters
- Real-time chat (1:1 and groups)
- University communication channel
- Landlord–tenant/roommate group spaces
- Ratings & reviews (listings, landlords, tenants)
- Interest-based community channels
- [UniServices] Service listings (e.g., private tutoring)
- [UniItems] Second-hand marketplace (buy/sell items)
- [UniCommunities] Sponsored promotions in community chats (venues/events)
- [UniCar] Student carpooling with in-app payments and commissions

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

> **Note:** After installation, restart your terminal or run `source ~/.bashrc` (Linux/macOS) or restart PowerShell (
> Windows).

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

## DB Schema

```mermaid
erDiagram
    USER {
      int id PK
      string username
      string email
      string password_hash
      string profile_pic_url
      int faculty_id FK
      datetime created_at
    }

    FACULTY {
      int id PK
      string name
    }

    INTEREST {
      int id PK
      string name
    }

    USER_INTEREST {
      int user_id PK, FK
      int interest_id PK, FK
      datetime created_at
    }

    ROLE {
      int id PK
      string name
      string description
    }

    USER_ROLE {
      int user_id PK, FK
      int role_id PK, FK
      datetime granted_at
    }

    CHANNEL {
      int id PK
      string name
      string description
      boolean is_private
      datetime created_at
    }

    PRIVATE_CHAT {
      int id PK
      datetime created_at
    }

    MESSAGE {
      int id PK
      int sender_user_id FK
      int channel_id FK  "nullable"
      int private_chat_id FK  "nullable"
      string content
      datetime created_at
    }

    MARKETPLACE_ITEM {
      int id PK
      int user_id FK
      string title
      string description
      date posted_date
      string location
      decimal price
      string category  "general | house | work"
      string photo_url
    }

    HOUSE {
      int item_id PK, FK
      int bedrooms
      int bathrooms
      float area_m2
    }

    WORK {
      int item_id PK, FK
      string job_title
      string company
      string contract_type
    }

    REPORT {
      int id PK
      int reporter_user_id FK
      string target_type  "user|message|item|channel"
      int target_id
      string status       "open|in_review|closed"
      string title
      string description
      string image_url
      datetime created_at
    }

    %% Relations
    FACULTY ||--o{ USER : has
    USER ||--o{ USER_INTEREST : has
    INTEREST ||--o{ USER_INTEREST : has

    USER ||--o{ USER_ROLE : has
    ROLE ||--o{ USER_ROLE : in

    CHANNEL ||--o{ MESSAGE : contains
    PRIVATE_CHAT ||--o{ MESSAGE : contains
    USER ||--o{ MESSAGE : sends

    USER ||--o{ MARKETPLACE_ITEM : posts
    MARKETPLACE_ITEM ||--|| HOUSE : details
    MARKETPLACE_ITEM ||--|| WORK : details

    USER ||--o{ REPORT : files
```

## Authors

- [Aniol0012](https://github.com/Aniol0012)
- [carless7](https://github.com/carless7)
- [cesarcres](https://github.com/cesarcres)
- [JerzyLeg](https://github.com/JerzyLeg)
- [TheSmuks](https://github.com/TheSmuks)
