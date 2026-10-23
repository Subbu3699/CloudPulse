
import logging
import time
from datetime import datetime, timezone

import httpx
from sqlalchemy.orm import Session

from app.models import Incident, MonitoredAPI, MonitoringCheck
from app.notifications import send_incident_email

logger = logging.getLogger(__name__)


def run_api_check(db: Session, api: MonitoredAPI) -> MonitoringCheck:
    """Check an API, save the result, and manage its incident."""

    started = time.perf_counter()
    checked_at = datetime.now(timezone.utc)
    status_code = None
    error_message = None
    is_success = False

    # Perform the HTTP request.
    try:
        with httpx.Client(
            timeout=httpx.Timeout(float(api.timeout_seconds)),
            follow_redirects=True,
        ) as client:
            response = client.request(
                method=api.method,
                url=api.url,
            )

        status_code = response.status_code
        is_success = 200 <= status_code < 400

        if not is_success:
            error_message = f"HTTP {status_code}"

    except httpx.TimeoutException:
        error_message = (
            f"Request timed out after {api.timeout_seconds} seconds"
        )
        logger.warning("Timeout checking API id=%s", api.id)

    except httpx.RequestError as exc:
        error_message = f"{type(exc).__name__}: {str(exc)}"[:1000]
        logger.warning(
            "Request error checking API id=%s: %s",
            api.id,
            error_message,
        )

    except Exception:
        logger.exception("Unexpected error checking API id=%s", api.id)
        error_message = "Unexpected monitoring error"

    response_time_ms = round(
        (time.perf_counter() - started) * 1000,
        2,
    )

    check = MonitoringCheck(
        api_id=api.id,
        status_code=status_code,
        response_time_ms=response_time_ms,
        is_success=is_success,
        error_message=error_message,
        checked_at=checked_at,
    )

    # Save the check and update incident state.
    new_incident = None

    try:
        db.add(check)

        open_incident = (
            db.query(Incident)
            .filter(
                Incident.api_id == api.id,
                Incident.status == "open",
            )
            .first()
        )

        if not is_success:
            if open_incident is None:
                new_incident = Incident(
                    api_id=api.id,
                    title=f"API failure: {api.name}",
                    description=error_message or "API check failed",
                    severity="major",
                    status="open",
                )
                db.add(new_incident)
            else:
                # Update the existing incident without duplicating it.
                open_incident.description = (
                    error_message or "API check failed"
                )

        elif open_incident is not None:
            # A successful check resolves the open incident.
            open_incident.status = "resolved"
            open_incident.resolved_at = checked_at

        # Commit before attempting external email delivery.
        db.commit()
        db.refresh(check)

        if new_incident is not None:
            db.refresh(new_incident)

    except Exception:
        db.rollback()
        logger.exception(
            "Unable to save monitoring result for API id=%s",
            api.id,
        )
        raise

    # Notify only after the new incident has been committed.
    # Email failures must not undo the saved monitoring result.
    if new_incident is not None:
        try:
            send_incident_email(
                subject=f"[CloudPulse] {new_incident.title}",
                body=(
                    f"Incident ID: {new_incident.id}\n"
                    f"API ID: {api.id}\n"
                    f"API name: {api.name}\n"
                    f"API URL: {api.url}\n"
                    f"Severity: {new_incident.severity}\n"
                    f"Status: {new_incident.status}\n"
                    f"Details: {new_incident.description}\n"
                    f"Detected at: {checked_at.isoformat()}\n"
                ),
            )
        except Exception:
            logger.exception(
                "Incident saved, but notification failed for incident id=%s",
                new_incident.id,
            )

    return check
