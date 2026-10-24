
import logging
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from app.database import SessionLocal, test_db_connection
from app.models import Incident, MonitoredAPI, MonitoringCheck
from app.monitor import run_api_check
from app.scheduler import scheduler, start_scheduler, stop_scheduler
from app.schemas import MonitoredAPICreate, MonitoredAPIResponse


logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.warning("CloudPulse lifespan starting")

    start_scheduler()

    logger.warning("Scheduler running: %s", scheduler.running)
    logger.warning("Scheduler jobs: %s", scheduler.get_jobs())

    try:
        yield
    finally:
        stop_scheduler()
        logger.warning("CloudPulse lifespan stopped")


app = FastAPI(
    title="CloudPulse API",
    description="API Monitoring and Incident Management Platform",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Database dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Root endpoint
@app.get("/")
def root():
    return {
        "message": "Welcome to CloudPulse",
        "status": "running",
    }


# Application health check
@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "CloudPulse API",
    }


# Database health check
@app.get("/health/database")
def database_health_check():
    try:
        if test_db_connection() == 1:
            return {
                "status": "healthy",
                "database": "connected",
            }

        raise RuntimeError("Unexpected database response")

    except Exception:
        logger.exception("Database health check failed")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database connection failed",
        )


# Register a new API for monitoring
@app.post(
    "/api/v1/monitored-apis",
    response_model=MonitoredAPIResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_monitored_api(
    api_data: MonitoredAPICreate,
    db: Session = Depends(get_db),
):
    monitored_api = MonitoredAPI(
        name=api_data.name,
        url=str(api_data.url),
        method=api_data.method,
        check_interval_seconds=api_data.check_interval_seconds,
        timeout_seconds=api_data.timeout_seconds,
    )

    db.add(monitored_api)
    db.commit()
    db.refresh(monitored_api)

    return monitored_api


# List all registered APIs
@app.get(
    "/api/v1/monitored-apis",
    response_model=list[MonitoredAPIResponse],
)
def list_monitored_apis(db: Session = Depends(get_db)):
    return (
        db.query(MonitoredAPI)
        .order_by(MonitoredAPI.id.desc())
        .all()
    )


# Get a registered API by ID
@app.get(
    "/api/v1/monitored-apis/{api_id}",
    response_model=MonitoredAPIResponse,
)
def get_monitored_api(
    api_id: int,
    db: Session = Depends(get_db),
):
    monitored_api = db.get(MonitoredAPI, api_id)

    if monitored_api is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Monitored API not found",
        )

    return monitored_api


# Update a registered API
@app.put(
    "/api/v1/monitored-apis/{api_id}",
    response_model=MonitoredAPIResponse,
)
def update_monitored_api(
    api_id: int,
    api_data: MonitoredAPICreate,
    db: Session = Depends(get_db),
):
    monitored_api = db.get(MonitoredAPI, api_id)

    if monitored_api is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Monitored API not found",
        )

    monitored_api.name = api_data.name
    monitored_api.url = str(api_data.url)
    monitored_api.method = api_data.method
    monitored_api.check_interval_seconds = (
        api_data.check_interval_seconds
    )
    monitored_api.timeout_seconds = api_data.timeout_seconds

    db.commit()
    db.refresh(monitored_api)

    return monitored_api


# Delete a registered API
@app.delete(
    "/api/v1/monitored-apis/{api_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_monitored_api(
    api_id: int,
    db: Session = Depends(get_db),
):
    monitored_api = db.get(MonitoredAPI, api_id)

    if monitored_api is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Monitored API not found",
        )

    db.delete(monitored_api)
    db.commit()


# Manually run a monitoring check
@app.post("/api/v1/monitored-apis/{api_id}/check")
def check_monitored_api(
    api_id: int,
    db: Session = Depends(get_db),
):
    api = db.get(MonitoredAPI, api_id)

    if api is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Monitored API not found",
        )

    if not api.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This API is inactive",
        )

    check = run_api_check(db, api)

    return {
        "id": check.id,
        "api_id": check.api_id,
        "status_code": check.status_code,
        "response_time_ms": check.response_time_ms,
        "is_success": check.is_success,
        "error_message": check.error_message,
        "checked_at": check.checked_at,
    }


# Get monitoring history for a specific API
@app.get("/api/v1/monitored-apis/{api_id}/checks")
def get_monitoring_history(
    api_id: int,
    limit: int = 50,
    db: Session = Depends(get_db),
):
    api = db.get(MonitoredAPI, api_id)

    if api is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Monitored API not found",
        )

    if limit < 1 or limit > 200:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Limit must be between 1 and 200",
        )

    checks = (
        db.query(MonitoringCheck)
        .filter(MonitoringCheck.api_id == api_id)
        .order_by(MonitoringCheck.checked_at.desc())
        .limit(limit)
        .all()
    )

    return [
        {
            "id": check.id,
            "api_id": check.api_id,
            "status_code": check.status_code,
            "response_time_ms": check.response_time_ms,
            "is_success": check.is_success,
            "error_message": check.error_message,
            "checked_at": check.checked_at,
        }
        for check in checks
    ]


# List incidents
@app.get("/api/v1/incidents")
def list_incidents(
    incident_status: str | None = None,
    db: Session = Depends(get_db),
):
    query = db.query(Incident)

    if incident_status is not None:
        if incident_status not in {"open", "resolved"}:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="incident_status must be open or resolved",
            )

        query = query.filter(Incident.status == incident_status)

    incidents = query.order_by(Incident.started_at.desc()).all()

    return [
        {
            "id": incident.id,
            "api_id": incident.api_id,
            "title": incident.title,
            "description": incident.description,
            "severity": incident.severity,
            "status": incident.status,
            "started_at": incident.started_at,
            "resolved_at": incident.resolved_at,
        }
        for incident in incidents
    ]
