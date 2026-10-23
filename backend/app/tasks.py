
import logging

from app.celery_app import celery_app
from app.database import SessionLocal
from app.models import MonitoredAPI
from app.monitor import run_api_check

logger = logging.getLogger(__name__)


@celery_app.task(name="app.tasks.ping_task")
def ping_task():
    return "CloudPulse background worker is working!"


@celery_app.task(
    bind=True,
    name="app.tasks.check_monitored_api",
    max_retries=2,
    default_retry_delay=5,
)
def check_monitored_api(self, api_id: int):
    """Run one API health check in a separate worker process."""
    db = SessionLocal()

    try:
        api = (
            db.query(MonitoredAPI)
            .filter(
                MonitoredAPI.id == api_id,
                MonitoredAPI.is_active.is_(True),
            )
            .first()
        )

        if api is None:
            logger.info(
                "Skipping missing or inactive API id=%s",
                api_id,
            )
            return {"api_id": api_id, "status": "skipped"}

        run_api_check(db, api)

        return {"api_id": api_id, "status": "checked"}

    except Exception as exc:
        db.rollback()
        logger.exception("Background check failed for API id=%s", api_id)

        if self.request.retries < self.max_retries:
            raise self.retry(exc=exc)

        raise

    finally:
        db.close()
