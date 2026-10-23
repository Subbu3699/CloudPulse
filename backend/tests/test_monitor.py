
from datetime import datetime, timezone
from unittest.mock import Mock, patch

import httpx
import pytest

from app.models import Incident, MonitoredAPI, MonitoringCheck
from app.monitor import run_api_check


@pytest.fixture
def monitored_api(db_session):
    api = MonitoredAPI(
        name="Monitor Test API",
        url="https://example.com/",
        method="GET",
        check_interval_seconds=60,
        timeout_seconds=10,
        is_active=True,
    )
    db_session.add(api)
    db_session.commit()
    db_session.refresh(api)
    return api


def mock_http_response(status_code):
    response = Mock()
    response.status_code = status_code
    return response


def test_successful_check_is_saved(db_session, monitored_api):
    with patch("app.monitor.httpx.Client") as client_class:
        client_class.return_value.__enter__.return_value.request.return_value = (
            mock_http_response(200)
        )

        check = run_api_check(db_session, monitored_api)

    assert check.is_success is True
    assert check.status_code == 200
    assert check.error_message is None

    saved = db_session.query(MonitoringCheck).filter_by(
        id=check.id
    ).one()
    assert saved.is_success is True


def test_failed_check_creates_incident(db_session, monitored_api):
    with patch("app.monitor.httpx.Client") as client_class:
        client_class.return_value.__enter__.return_value.request.return_value = (
            mock_http_response(500)
        )

        check = run_api_check(db_session, monitored_api)

    assert check.is_success is False
    assert check.status_code == 500
    assert check.error_message == "HTTP 500"

    incident = db_session.query(Incident).filter_by(
        api_id=monitored_api.id,
        status="open",
    ).one()

    assert incident.title == "API failure: Monitor Test API"


def test_recovery_resolves_open_incident(db_session, monitored_api):
    incident = Incident(
        api_id=monitored_api.id,
        title="API failure: Monitor Test API",
        description="HTTP 500",
        severity="major",
        status="open",
    )
    db_session.add(incident)
    db_session.commit()
    db_session.refresh(incident)

    with patch("app.monitor.httpx.Client") as client_class:
        client_class.return_value.__enter__.return_value.request.return_value = (
            mock_http_response(200)
        )

        check = run_api_check(db_session, monitored_api)

    db_session.refresh(incident)

    assert check.is_success is True
    assert incident.status == "resolved"
    assert incident.resolved_at is not None


def test_repeated_failures_do_not_duplicate_incidents(
    db_session, monitored_api
):
    with patch("app.monitor.httpx.Client") as client_class:
        client_class.return_value.__enter__.return_value.request.return_value = (
            mock_http_response(503)
        )

        run_api_check(db_session, monitored_api)
        run_api_check(db_session, monitored_api)

    open_incidents = db_session.query(Incident).filter_by(
        api_id=monitored_api.id,
        status="open",
    ).all()

    assert len(open_incidents) == 1
