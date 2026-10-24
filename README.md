# Profile Intelligence Service

An asynchronous REST API built with **FastAPI** that classifies names and manages enriched profile data. This project demonstrates asynchronous programming, external API integration, database management, data validation, filtering, sorting, pagination, and database migrations.

## Features

### Stage 0 — Name Classification
- Classifies names using the Genderize API.
- Uses asynchronous HTTP requests with `httpx`.
- Returns gender predictions, probability, and sample size.
- Validates input and handles errors.
- Supports Cross-Origin Resource Sharing (CORS).

### Stage 1 — Profile Management
- Stores profile information in a database.
- Enriches profiles using external APIs such as Genderize, Agify, and Nationalize.
- Uses asynchronous SQLAlchemy for database operations.
- Provides profile management functionality.

### Stage 2 — Advanced Profile Queries
- Supports filtering and sorting profile records.
- Supports pagination.
- Includes rule-based natural-language query parsing.
- Generates UUID version 7 identifiers.
- Includes country names alongside country codes.
- Uses database indexes to support common queries.

## Technology Stack

- **Python** — Programming language
- **FastAPI** — Web framework
- **Uvicorn** — ASGI server
- **SQLAlchemy** — Database ORM
- **SQLite** — Local development database
- **Alembic** — Database migrations
- **httpx** — Asynchronous HTTP requests
- **aiosqlite** — Asynchronous SQLite driver
- **pycountry** — Country-code and country-name information
- **Pydantic** — Data validation and serialization

## Project Structure

```text
search/
├── alembic/
│   ├── versions/
│   └── env.py
├── app/
│   ├── main.py
│   ├── database.py
│   ├── models.py
│   ├── schemas.py
│   ├── classify.py
│   ├── profile_service.py
│   ├── query_parser.py
│   └── routers/
│       └── profiles.py
├── scripts/
│   └── seed_profiles.py
├── requirements.txt
├── alembic.ini
├── .gitignore
└── README.md
```

The structure above represents the expected organization of the project. The actual files may differ depending on the implementation.

## Requirements

Before running the application, ensure you have:

- Python installed
- pip installed
- Git installed (optional)

## Installation and Setup

### 1. Clone the Repository

Replace the example URL with your actual GitHub repository URL.

```bash
git clone https://github.com/YOUR_USERNAME/YOUR_REPOSITORY.git
cd YOUR_REPOSITORY
```

Alternatively, open your existing project directory in Visual Studio Code.

### 2. Create a Virtual Environment

On Windows, run:

```powershell
python -m venv venv
```

Activate the virtual environment:

```powershell
.\venv\Scripts\Activate.ps1
```

If PowerShell blocks activation, run:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
.\venv\Scripts\Activate.ps1
```

### 3. Install Dependencies

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Ensure that `requirements.txt` includes all dependencies required by the application, including Alembic and the asynchronous database driver.

## Database Configuration

The application uses SQLite for local development.

Default database URL:

```text
sqlite+aiosqlite:///./profiles.db
```

Database schema changes are managed with Alembic.

Apply the database migrations:

```