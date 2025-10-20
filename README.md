# UniHub - Backend

[![Python](https://img.shields.io/badge/Python-3.13-blue?logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.118.0-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0.43-red?logo=sqlalchemy&logoColor=white)](https://www.sqlalchemy.org/)
[![uv](https://img.shields.io/badge/uv-package%20manager-purple?logo=python&logoColor=white)](https://github.com/astral-sh/uv)
[![pytest](https://img.shields.io/badge/pytest-8.0+-0A9EDC?logo=pytest&logoColor=white)](https://pytest.org/)
[![Docker](https://img.shields.io/badge/Docker-enabled-2496ED?logo=docker&logoColor=white)](https://www.docker.com/)

## Introduction

This project is part of the first semester project course at
the [University of Lleida (UdL)](https://www.udl.cat/ca/en/). It serves as the backend
for the UniHub application. This API includes the following main features:

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

> [!NOTE]
> After installation, restart your terminal or run `source ~/.bashrc` (Linux/macOS) or restart PowerShell (Windows).

### 2. Clone and Install

```bash
git clone https://github.com/Computer-Engineering-UdL/UniHub-Back
cd UniHub-Back
uv sync --group dev
```

### 3. Configure Environment

Create a `.env` file:

```env
API_VERSION=/api/v1
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_USER=unihub
POSTGRES_PASSWORD="test"
POSTGRES_DB=unihub
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
docker build -t unihub-backend .

# Run container
docker run -p 8080:8080 unihub-backend
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
  channel {
    UUID id PK
    VARCHAR(2048) channel_logo "nullable"
    VARCHAR(50) channel_type
    DATETIME created_at
    VARCHAR(120) description "nullable"
    VARCHAR(60) name "indexed"
  }

  channel_bans {
    UUID id PK
    UUID banned_by FK "nullable"
    UUID channel_id FK
    UUID user_id FK
    BOOLEAN active
    DATETIME banned_at
    DATETIME duration
    VARCHAR(255) motive
  }

  channel_unbans {
    UUID id PK
    UUID channel_id FK
    UUID unbanned_by FK "nullable"
    UUID user_id FK
    VARCHAR(255) motive
    DATETIME unbanned_at
  }

  user {
    UUID id PK
    VARCHAR(500) avatar_url "nullable"
    DATETIME created_at
    VARCHAR(255) email UK "indexed"
    VARCHAR(100) first_name
    BOOLEAN is_active
    BOOLEAN is_verified
    VARCHAR(100) last_name
    VARCHAR(255) password
    VARCHAR(20) phone "nullable"
    VARCHAR(50) provider
    VARCHAR(50) role
    VARCHAR(20) room_number "nullable"
    VARCHAR(100) university "nullable"
    VARCHAR(50) username UK "indexed"
  }

  channel_members {
    UUID channel_id PK,FK
    UUID user_id PK,FK
    BOOLEAN is_banned
    DATETIME joined_at
    VARCHAR(20) role
  }

  housing_offer {
    UUID id PK
    UUID category_id FK
    UUID user_id FK
    VARCHAR(255) address
    NUMERIC area
    VARCHAR(100) city
    NUMERIC deposit "nullable"
    TEXT description
    DATE end_date "nullable"
    BOOLEAN furnished
    VARCHAR(10) gender_preference "nullable"
    BOOLEAN internet_included
    INTEGER num_bathrooms "nullable"
    INTEGER num_rooms "nullable"
    DATE offer_valid_until
    DATETIME posted_date
    NUMERIC price
    DATE start_date
    VARCHAR(20) status
    VARCHAR(255) title
    BOOLEAN utilities_included
  }

  housing_category {
    UUID id PK
    VARCHAR(50) name UK
  }

  housing_photo {
    UUID id PK
    UUID offer_id FK
    DATETIME uploaded_at
    VARCHAR(255) url
  }

  interest_category {
    CHAR(32) id PK
    VARCHAR(120) name UK
  }

  interest {
    CHAR(32) id PK
    CHAR(32) category_id FK
    VARCHAR(120) name UK
  }

  user_interest {
    CHAR(32) id PK
    CHAR(32) interest_id FK "indexed"
    UUID user_id FK "indexed"
  }

  message {
    UUID id PK
    UUID channel_id FK
    UUID parent_message_id FK "nullable"
    UUID user_id FK
    VARCHAR(500) content
    DATETIME created_at
    BOOLEAN is_edited
    DATETIME updated_at "nullable"
  }

  channel ||--o{ channel_bans : channel_id
  user ||--o{ channel_bans : user_id
  user ||--o{ channel_bans : banned_by
  channel ||--o{ channel_unbans : channel_id
  user ||--o{ channel_unbans : user_id
  user ||--o{ channel_unbans : unbanned_by
  channel ||--o{ channel_members : channel_id
  user ||--o{ channel_members : user_id
  user ||--o{ housing_offer : user_id
  housing_category ||--o{ housing_offer : category_id
  housing_offer ||--o{ housing_photo : offer_id
  interest_category ||--o{ interest : category_id
  user ||--o{ user_interest : user_id
  interest ||--o{ user_interest : interest_id
  channel ||--o{ message : channel_id
  user ||--o{ message : user_id
  message ||--o{ message : parent_message_id
```

## Authors

<table>
  <tr>
    <td align="center">
      <a href="https://github.com/Aniol0012">
        <img src="https://github.com/Aniol0012.png" width="72" height="72" style="border-radius:50%;" alt="Aniol0012"><br/>
        <img src="https://img.shields.io/badge/Aniol0012-Contributor-181717?style=for-the-badge&logo=github&logoColor=white" alt="Aniol0012">
      </a>
    </td>
    <td align="center">
      <a href="https://github.com/carless7">
        <img src="https://github.com/carless7.png" width="72" height="72" style="border-radius:50%;" alt="carless7"><br/>
        <img src="https://img.shields.io/badge/carless7-Contributor-181717?style=for-the-badge&logo=github&logoColor=white" alt="carless7">
      </a>
    </td>
    <td align="center">
      <a href="https://github.com/cesarcres">
        <img src="https://github.com/cesarcres.png" width="72" height="72" style="border-radius:50%;" alt="cesarcres"><br/>
        <img src="https://img.shields.io/badge/cesarcres-Contributor-181717?style=for-the-badge&logo=github&logoColor=white" alt="cesarcres">
      </a>
    </td>
    <td align="center">
      <a href="https://github.com/JerzyLeg">
        <img src="https://github.com/JerzyLeg.png" width="72" height="72" style="border-radius:50%;" alt="JerzyLeg"><br/>
        <img src="https://img.shields.io/badge/JerzyLeg-Contributor-181717?style=for-the-badge&logo=github&logoColor=white" alt="JerzyLeg">
      </a>
    </td>
    <td align="center">
      <a href="https://github.com/TheSmuks">
        <img src="https://github.com/TheSmuks.png" width="72" height="72" style="border-radius:50%;" alt="TheSmuks"><br/>
        <img src="https://img.shields.io/badge/TheSmuks-Contributor-181717?style=for-the-badge&logo=github&logoColor=white" alt="TheSmuks">
      </a>
    </td>
  </tr>
</table>
