import pytest
from unittest.mock import patch

from retry import retry_on_exception


class TestRetryDecorator:
    def test_succeeds_on_first_try(self):
        call_count = 0

        @retry_on_exception(max_retries=3, base_delay=0.01)
        def succeed():
            nonlocal call_count
            call_count += 1
            return "ok"

        assert succeed() == "ok"
        assert call_count == 1

    def test_retries_on_failure_then_succeeds(self):
        call_count = 0

        @retry_on_exception(max_retries=3, base_delay=0.01)
        def flaky():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ConnectionError("fail")
            return "recovered"

        assert flaky() == "recovered"
        assert call_count == 3

    def test_raises_after_max_retries(self):
        @retry_on_exception(max_retries=2, base_delay=0.01)
        def always_fails():
            raise ValueError("permanent")

        with pytest.raises(ValueError, match="permanent"):
            always_fails()

    def test_only_catches_specified_exceptions(self):
        @retry_on_exception(max_retries=3, base_delay=0.01, exceptions=(ValueError,))
        def raises_type_error():
            raise TypeError("wrong type")

        with pytest.raises(TypeError):
            raises_type_error()

    def test_respects_max_delay(self):
        call_count = 0

        @retry_on_exception(max_retries=5, base_delay=0.01, max_delay=0.02)
        def fail_a_lot():
            nonlocal call_count
            call_count += 1
            if call_count <= 4:
                raise RuntimeError("not yet")
            return "done"

        assert fail_a_lot() == "done"
        assert call_count == 5
