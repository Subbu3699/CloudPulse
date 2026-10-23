
from unittest.mock import Mock, patch

from app import scheduler as scheduler_module
from app.models import MonitoredAPI


def make_api(api_id, interval=60):
    api = Mock(spec=MonitoredAPI)
    api.id = api_id
    api.name = f"Test API {api_id}"
    api.check_interval_seconds = interval
    api.is_active = True
    return api


def setup_db(apis):
    db = Mock()
    db.query.return_value.filter.return_value.all.return_value = apis
    return db


def test_new_api_is_queued_immediately():
    api = make_api(1)
    db = setup_db([api])
    scheduler_module._last_dispatch_times.clear()

    with (
        patch.object(scheduler_module, "SessionLocal", return_value=db),
        patch.object(scheduler_module.check_monitored_api, "delay") as queue_task,
        patch.object(scheduler_module.time, "monotonic", side_effect=[100.0, 100.1]),
    ):
        scheduler_module.check_all_active_apis()

    queue_task.assert_called_once_with(1)
    assert scheduler_module._last_dispatch_times[1] == 100.1
    db.close.assert_called_once()


def test_api_is_not_queued_before_interval_is_due():
    api = make_api(1, interval=60)
    db = setup_db([api])
    scheduler_module._last_dispatch_times.clear()
    scheduler_module._last_dispatch_times[1] = 100.0

    with (
        patch.object(scheduler_module, "SessionLocal", return_value=db),
        patch.object(scheduler_module.check_monitored_api, "delay") as queue_task,
        patch.object(scheduler_module.time, "monotonic", return_value=130.0),
    ):
        scheduler_module.check_all_active_apis()

    queue_task.assert_not_called()
    db.close.assert_called_once()


def test_api_is_queued_when_interval_is_due():
    api = make_api(1, interval=60)
    db = setup_db([api])
    scheduler_module._last_dispatch_times.clear()
    scheduler_module._last_dispatch_times[1] = 100.0

    with (
        patch.object(scheduler_module, "SessionLocal", return_value=db),
        patch.object(scheduler_module.check_monitored_api, "delay") as queue_task,
        patch.object(scheduler_module.time, "monotonic", side_effect=[160.0, 160.1]),
    ):
        scheduler_module.check_all_active_apis()

    queue_task.assert_called_once_with(1)
    assert scheduler_module._last_dispatch_times[1] == 160.1
    db.close.assert_called_once()


def test_inactive_apis_are_not_queued_and_state_is_cleared():
    db = setup_db([])
    scheduler_module._last_dispatch_times.clear()
    scheduler_module._last_dispatch_times[7] = 100.0

    with (
        patch.object(scheduler_module, "SessionLocal", return_value=db),
        patch.object(scheduler_module.check_monitored_api, "delay") as queue_task,
    ):
        scheduler_module.check_all_active_apis()

    queue_task.assert_not_called()
    assert 7 not in scheduler_module._last_dispatch_times
    db.close.assert_called_once()
