from unittest.mock import Mock

import pytest

from app import connection_manager


class StopLoop(BaseException):
    pass


@pytest.mark.parametrize("failure", [None, RuntimeError("temporary database error")])
def test_refresh_waits_between_attempts_and_recovers(monkeypatch, failure):
    manager = object.__new__(connection_manager.ConnectionManager)
    manager.get_current_server_id = Mock(return_value=0)
    manager.refresh_best_server = Mock(side_effect=[failure, None])
    sleep = Mock(side_effect=[None, StopLoop()])
    monkeypatch.setattr(connection_manager.time, "sleep", sleep)
    with pytest.raises(StopLoop):
        manager.refresh_best_server_thread_handler()
    assert manager.refresh_best_server.call_count == 2
    assert sleep.call_count == 2
    assert all(
        call.args == (connection_manager.config.MULTISERVER_REFRESH_BEST_SERVER_PERIOD,)
        for call in sleep.call_args_list
    )
