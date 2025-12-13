# SSO Service v2

Scalable SSO service with multi-method authentication and centralized user data.

## Features

- Multi-platform authentication (Android, iOS, Web)
- Firebase Authentication (Google, Email/Password, Phone OTP, Apple)
- gRPC API for inter-service user data access
- Redis-based session management
- Multi-device login support

## Tech Stack

- Python 3.12+
- FastAPI
- PostgreSQL
- Redis
- gRPC
- Firebase Admin SDK

## Setup

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run migrations
alembic upgrade head

# Start server
uvicorn app.main:app --reload
```

## Project Structure

```
app/
├── config/          # Settings, database config
├── core/            # Shared utilities, schemas, exceptions
└── modules/
    ├── auth/        # Authentication module
    └── users/       # User management module
```
