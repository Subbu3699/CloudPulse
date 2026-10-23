# CloudPulse — API Monitoring and Incident Management Platform

CloudPulse is an API monitoring platform designed to check endpoint availability, record response times, track failures, and manage incidents. It uses a React frontend, FastAPI backend, PostgreSQL database, Redis, and Celery for background monitoring tasks.

## Features

- **API Management:** Register and manage monitored API endpoints.
- **Health Checks:** Check HTTP status codes and response times.
- **Monitoring History:** Store and review API check results.
- **Incident Management:** Create incidents when monitored APIs fail and resolve them when service recovers.
- **Email Notifications:** Send email alerts for newly detected incidents.
- **Background Tasks:** Use Celery workers and Redis to process monitoring checks asynchronously.
- **REST API:** Explore backend endpoints through FastAPI Swagger documentation.
- **Automated Tests:** Test API routes, monitoring behavior, and scheduler dispatch logic.

## Tech Stack

| Layer | Technologies |
|---|---|
| Frontend | React, Vite, JavaScript, CSS |
| Backend | Python, FastAPI |
| Database | PostgreSQL, SQLAlchemy |
| Background Jobs | Celery, Redis, APScheduler |
| HTTP Requests | HTTPX |
| Database Migrations | Alembic |
| Testing | pytest |
| Version Control | Git, GitHub |

## Architecture

```text
User
  |
  v
React Frontend
  |
  v
FastAPI Backend ------> PostgreSQL
  |
  v
APScheduler
  |
  v
Redis Message Broker
  |
  v
Celery Worker -------> HTTP API Checks
  |
  v
Monitoring Results and Incidents
  |
  v
Email Notifications
```

## Prerequisites

Install the following before running CloudPulse locally:

- Python 3.13 or a compatible Python version
- Node.js and npm
- PostgreSQL
- Docker Desktop
- Git

## Local Setup

### 1. Clone the repository

```bash
git clone https://github.com/Subbu3699/CloudPulse.git
cd CloudPulse
```

### 2. Configure the backend

```powershell
cd backend
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install fastapi "uvicorn[standard]" sqlalchemy psycopg2-binary python-dotenv httpx apscheduler alembic "celery[redis]>=5.4,<6" "redis>=5,<7"
```

Create a local `.env` file in the `backend` directory. Configure your PostgreSQL connection, a strong JWT secret if required by your application, and email settings using your own credentials. Never commit `.env` or secret values to GitHub.

Ensure the PostgreSQL database exists and apply the project's database migrations if required.

Start the API:

```powershell
python -m uvicorn app.main:app --reload
```

Backend API: `http://127.0.0.1:8000`

Swagger documentation: `http://127.0.0.1:8000/docs`

### 3. Start Redis

From a terminal with Docker available:

```bash
docker run -d --name cloudpulse-redis -p 6379:6379 --restart unless-stopped redis:7-alpine
```

If a container named `cloudpulse-redis` already exists, start that container instead of creating another one.

Configure `REDIS_URL=redis://127.0.0.1:6379/0` in `backend/.env`.

### 4. Start the Celery worker

Open another terminal:

```powershell
cd backend
.\venv\Scripts\Activate.ps1
python -m celery -A app.celery_app:celery_app worker --pool=solo --loglevel=info
```

Keep Redis and the Celery worker running while using background monitoring.

### 5. Start the frontend

Open another terminal:

```powershell
cd frontend
npm install
npm run dev
```

Open the local frontend URL shown in the terminal, usually `http://localhost:5173`.

## Running Tests

From the backend directory with the virtual environment activated:

```powershell
python -m pytest -v
```

## Project Structure

```text
CloudPulse/
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── models.py
│   │   ├── schemas.py
│   │   ├── database.py
│   │   ├── monitor.py
│   │   ├── scheduler.py
│   │   ├── tasks.py
│   │   ├── celery_app.py
│   │   ├── redis_client.py
│   │   └── notifications.py
│   ├── migrations/
│   └── tests/
├── frontend/
└── .gitignore
```

## Future Improvements

- Docker Compose for the complete application stack
- CI/CD with GitHub Actions
- Monitoring dashboards with uptime and response-time charts
- Production deployment and environment-specific configuration
- Improved task deduplication, observability, and retry handling

## Author

**Subba Raju Thotakura**

GitHub: [Subbu3699](https://github.com/Subbu3699)

---

*CloudPulse is a portfolio project for learning and demonstrating API monitoring, asynchronous processing, incident management, and full-stack development.*
