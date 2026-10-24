
import logging
import time

from apscheduler.schedulers.background import BackgroundScheduler
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models import MonitoredAPI
from app.tasks import check_monitored_api

logger = logging.getLogger(__name__)

scheduler = BackgroundScheduler(timezone="UTC")

# In-memory dispatch timing; resets when backend restarts.
_last_dispatch_times: dict[int, float] = {}


def check_all_active_apis():
    """Dispatch due API checks to Celery without running checks here."""
    started_at = time.perf_counter()
    logger.warning("Scheduler dispatch cycle started")

    db: Session = SessionLocal()
    logger.warning("Scheduler: database session opened")

    try:
        logger.warning("Scheduler: loading active APIs")

        apis = (
            db.query(MonitoredAPI)
            .filter(MonitoredAPI.is_active.is_(True))
            .all()
        )

        logger.warning("Scheduler: loaded %s active APIs", len(apis))

        active_api_ids = {api.id for api in apis}

        for api_id in list(_last_dispatch_times):
            if api_id not in active_api_ids:
                _last_dispatch_times.pop(api_id, None)

        logger.warning("Scheduler: starting API dispatch loop")

        for api in apis:
            api_id = api.id
            now = time.monotonic()
            interval = max(1, int(api.check_interval_seconds))
            last_dispatch = _last_dispatch_times.get(api_id)

            if (
                last_dispatch is not None
                and now - last_dispatch < interval
            ):
                continue

            try:
                logger.warning(
                    "Scheduler: queueing check for API id=%s",
                    api_id,
                )

                check_monitored_api.delay(api_id)
                _last_dispatch_times[api_id] = time.monotonic()

                logger.info(
                    "Queued API check id=%s name=%s interval=%s seconds",
                    api_id,
                    api.name,
                    interval,
                )

            except Exception:
                logger.exception(
                    "Unable to queue API check for id=%s",
                    api_id,
                )

    except Exception:
        logger.exception("Unable to load APIs for scheduled monitoring")

    finally:
        try:
            db.close()
            logger.warning("Scheduler: database session closed")
        except Exception:
            logger.exception("Scheduler: failed to close database session")

        elapsed = time.perf_counter() - started_at
        logger.warning(
            "Scheduler dispatch cycle completed in %.3f seconds",
            elapsed,
        )


def start_scheduler():
    """Start the scheduler that dispatches due API checks."""
    if not scheduler.running:
        scheduler.add_job(
            check_all_active_apis,
            trigger="interval",
            seconds=10,
            id="cloudpulse_api_monitor",
            replace_existing=True,
            max_instances=1,
            coalesce=True,
        )
        scheduler.start()
        logger.warning("CloudPulse monitoring scheduler started")


def stop_scheduler():
    """Stop the scheduler gracefully."""
    if scheduler.running:
        scheduler.shutdown(wait=False)
        logger.warning("CloudPulse monitoring scheduler stopped")
