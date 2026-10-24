# CloudPulse — API Monitoring & Incident Management Platform

CloudPulse is an API monitoring platform that periodically checks registered endpoints, records response times and HTTP status codes, detects failures, manages incidents, and sends email notifications.

## Features

- **API Management:** Register and manage monitored API endpoints.
- **Automated Monitoring:** Schedule recurring health checks.
- **Performance Tracking:** Record HTTP status codes and response times.
- **Incident Management:** Create incidents when endpoints fail and resolve them after recovery.
- **Email Notifications:** Send SMTP email alerts for incidents.
- **Dashboard:** View API health, failures, incidents, and monitoring history.
- **Background Processing:** Use Celery and Redis to process monitoring tasks.
- **Retry Handling:** Retry eligible failed background tasks.
- **Automated Tests:** Test API endpoints, monitoring behavior, and scheduling logic.
- **Containerization:** Run the application using Docker Compose.

## Tech Stack

| Component | Technology |
|---|---|
| Frontend | React, Vite, JavaScript |
| UI and Charts | Tailwind CSS, Recharts, Lucide |
| Backend | Python, FastAPI |
| Database | PostgreSQL |
| ORM and Validation | SQLAlchemy, Pydantic |
| Background Tasks | Celery |
| Message Broker | Redis |
| HTTP Monitoring | HTTPX |
| Scheduling | APScheduler |
| Testing | pytest |
| Deployment Environment | Docker, Docker Compose |

## Architecture

```text
User
  |
  v
React Dashboard
  |
  v
FastAPI Backend
  |
  +------ PostgreSQL
  |        API records
  |        Health-check history
  |        Incidents
  |
  +------ APScheduler
             |
             v
          Redis Queue
             |
             v
          Celery Worker
             |
             v
       External API Checks
             |
             v
      Save Results & Incidents
             |
             v
       SMTP Email Alerts
```

## Prerequisites

- Python 3.13+
- Node.js 22+
- PostgreSQL
- Docker Desktop with Docker Compose
- Git

## Run with Docker Compose

Clone the repository and open the project directory:

```bash
git clone <YOUR_GITHUB_REPOSITORY_URL>
cd CloudPulse
```

Configure the environment variables in `backend/.env` using the required local settings. Do not commit real credentials or secret keys.

Build and start the services:

```bash
docker compose config --quiet
docker compose build
docker compose up -d
```

Check service status:

```bash
docker compose ps
```

Stop the services:

```bash
docker compose down
```

## Access the Application

- Dashboard: http://localhost:5173
- FastAPI Swagger documentation: http://127.0.0.1:8000/docs
- Backend health endpoint: http://127.0.0.1:8000/health

## Local Backend Development

Create and activate a Python virtual environment from the `backend` directory:

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m uvicorn app.main:app --reload
```

## Local Frontend Development

From the `frontend` directory:

```bash
npm ci
npm run dev
```

The frontend development server will display its local URL in the terminal.

## Testing

Run the backend test suite from the `backend` directory:

```powershell
.\venv\Scripts\Activate.ps1
python -m pytest -v
```

**Verified result during development:** 21 tests passed in 11.91 seconds.

The tests cover API endpoints, input validation, monitoring checks, incident creation and recovery, duplicate-incident prevention, and scheduler behavior.

## Security

- Keep `.env` files and credentials out of Git.
- Use strong, unique database passwords and secret keys.
- Configure SMTP credentials through environment variables.
- Run the backend and Celery worker as non-root users in Docker.
- Review logs before sharing them publicly to ensure they contain no secrets.

## Project Status

The core monitoring workflow has been tested locally with Docker Compose. API health checks, HTTP failure detection, incident recovery, SMTP email delivery, and the automated backend test suite have been verified during development.

Further production hardening, deployment configuration, and monitoring under sustained load may be required before production use.

## License

Choose and add an appropriate open-source license before distributing the project publicly.
