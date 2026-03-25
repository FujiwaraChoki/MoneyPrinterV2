import os
import logging

import status


class TestLogging:
    def test_get_logger_returns_logger(self):
        logger = status.get_logger()
        assert isinstance(logger, logging.Logger)
        assert logger.name == "mpv2"

    def test_logger_has_handlers(self):
        logger = status.get_logger()
        assert len(logger.handlers) > 0

    def test_error_logs_to_logger(self, capfd):
        status.error("test error message", show_emoji=False)
        captured = capfd.readouterr()
        assert "test error message" in captured.err

    def test_success_prints_message(self, capfd):
        status.success("test success", show_emoji=False)
        captured = capfd.readouterr()
        assert "test success" in captured.out

    def test_info_prints_message(self, capfd):
        status.info("test info", show_emoji=False)
        captured = capfd.readouterr()
        assert "test info" in captured.out

    def test_warning_prints_message(self, capfd):
        status.warning("test warning", show_emoji=False)
        captured = capfd.readouterr()
        assert "test warning" in captured.out

    def test_logger_level_is_debug(self):
        logger = status.get_logger()
        assert logger.level == logging.DEBUG
