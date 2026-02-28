# PPSC Crack — Backend (FastAPI)

> AI-Powered Exam Domination System — API Server

## Tech Stack

- **Python 3.12+**
- **FastAPI** — async web framework
- **SQLAlchemy 2.0** — async ORM
- **PostgreSQL** — primary database (via asyncpg)
- **Alembic** — database migrations
- **Pydantic v2** — request / response validation
- **python-jose** — JWT authentication

## Folder Structure

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI app factory
│   ├── config.py            # Settings from .env
│   ├── database.py          # SQLAlchemy async engine & session
│   ├── dependencies.py      # Shared FastAPI dependencies
│   ├── api/
│   │   ├── __init__.py
│   │   └── v1/
│   │       ├── __init__.py
│   │       ├── router.py    # Aggregated v1 router
│   │       └── endpoints/
│   │           ├── __init__.py
│   │           ├── auth.py
│   │           ├── users.py
│   │           ├── papers.py
│   │           ├── predictions.py
│   │           ├── current_affairs.py
│   │           └── health.py
│   ├── models/
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── paper.py
│   │   ├── prediction.py
│   │   └── current_affair.py
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── auth.py
│   │   ├── user.py
│   │   ├── paper.py
│   │   ├── prediction.py
│   │   └── current_affair.py
│   ├── services/
│   │   ├── __init__.py
│   │   ├── auth_service.py
│   │   ├── user_service.py
│   │   ├── paper_service.py
│   │   ├── prediction_service.py
│   │   └── current_affairs_service.py
│   ├── core/
│   │   ├── __init__.py
│   │   ├── security.py      # JWT / hashing helpers
│   │   └── exceptions.py    # Custom HTTP exceptions
│   └── utils/
│       ├── __init__.py
│       └── helpers.py
├── alembic/
│   ├── env.py
│   └── versions/
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   └── api/
│       └── __init__.py
├── alembic.ini
├── .env                     # Environment variables (git-ignored)
├── .env.example             # Template for .env
├── pyproject.toml
├── requirements.txt
└── README.md
```

## Quick Start

```bash
cd backend

# Create virtual environment
python3.12 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Copy env template
cp .env.example .env
# Edit .env with your values

# Run development server
uvicorn app.main:app --reload --port 8000
```

API docs available at: `http://localhost:8000/docs`
