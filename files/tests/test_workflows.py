"""
tests/test_workflows.py - Unit tests for workflow orchestration logic.

All MicroStrategy API calls are mocked — no live server needed.
Tests verify:
  - All steps are called in the correct order
  - A failing step aborts the workflow immediately
  - Correct return values (True/False)
  - Backup project name correctly uses the --backup-month suffix
  - Revoke is called once per configured role/group pair
"""

import sys
import logging
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from config import AppConfig, MstrConfig, ProjectConfig, LogConfig
import workflows.ohne_backup as workflow_ohne
import workflows.mit_backup as workflow_mit


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture(autouse=True)
def silence_logger():
    """Suppress log output during tests so pytest output stays clean."""
    logging.getLogger("sgb2_maende").setLevel(logging.CRITICAL)


@pytest.fixture
def cfg():
    return AppConfig(
        mstr=MstrConfig(
            base_url="http://localhost:8080/MicroStrategyLibrary",
            username="Administrator",
            password="secret",
            login_mode=1,
        ),
        project=ProjectConfig(
            project_name="SGB II MaEnde",
            project_id=None,
            backup_base_name="SGB II MaEnde",
            db_connection_name="SGB II - MaEnde - MSAS@DST",
            db_catalog_name="SGB2_MaEnde",
            revoke_role_group_pairs=[
                ("Normale Benutzer", "Everyone"),
                ("Normale Benutzer", "SGB II Projektzugriff"),
            ],
        ),
        log=LogConfig(
            log_file_name="test.log",
            log_dir=Path("/tmp"),
        ),
    )


@pytest.fixture
def mock_conn():
    """Return a context manager mock that yields a fake connection."""
    ctx = MagicMock()
    ctx.__enter__ = MagicMock(return_value=MagicMock())
    ctx.__exit__ = MagicMock(return_value=False)
    return ctx


# ── ohne_backup workflow ──────────────────────────────────────────────────────

class TestOhneBackupWorkflow:

    @patch("workflows.ohne_backup.load_project", return_value=True)
    @patch("workflows.ohne_backup.alter_db_connection_catalog", return_value=True)
    @patch("workflows.ohne_backup.unload_project", return_value=True)
    @patch("workflows.ohne_backup.disconnect_users", return_value=True)
    @patch("workflows.ohne_backup.mstr_connection")
    def test_all_steps_succeed(self, mock_ctx, mock_disc, mock_unload,
                               mock_alter, mock_load, mock_conn, cfg):
        mock_ctx.return_value = mock_conn
        result = workflow_ohne.run(cfg)

        assert result is True
        mock_disc.assert_called_once()
        mock_unload.assert_called_once()
        mock_alter.assert_called_once()
        mock_load.assert_called_once()

    @patch("workflows.ohne_backup.unload_project", return_value=True)
    @patch("workflows.ohne_backup.disconnect_users", return_value=False)  # FAILS
    @patch("workflows.ohne_backup.mstr_connection")
    def test_aborts_on_disconnect_failure(self, mock_ctx, mock_disc,
                                          mock_unload, mock_conn, cfg):
        mock_ctx.return_value = mock_conn
        result = workflow_ohne.run(cfg)

        assert result is False
        mock_unload.assert_not_called()  # must not proceed past failed step

    @patch("workflows.ohne_backup.load_project", return_value=True)
    @patch("workflows.ohne_backup.alter_db_connection_catalog", return_value=False)  # FAILS
    @patch("workflows.ohne_backup.unload_project", return_value=True)
    @patch("workflows.ohne_backup.disconnect_users", return_value=True)
    @patch("workflows.ohne_backup.mstr_connection")
    def test_aborts_on_alter_failure(self, mock_ctx, mock_disc, mock_unload,
                                     mock_alter, mock_load, mock_conn, cfg):
        mock_ctx.return_value = mock_conn
        result = workflow_ohne.run(cfg)

        assert result is False
        mock_load.assert_not_called()  # load must not run after alter fails

    @patch("workflows.ohne_backup.load_project", return_value=False)  # FAILS
    @patch("workflows.ohne_backup.alter_db_connection_catalog", return_value=True)
    @patch("workflows.ohne_backup.unload_project", return_value=True)
    @patch("workflows.ohne_backup.disconnect_users", return_value=True)
    @patch("workflows.ohne_backup.mstr_connection")
    def test_returns_false_on_load_failure(self, mock_ctx, mock_disc, mock_unload,
                                           mock_alter, mock_load, mock_conn, cfg):
        mock_ctx.return_value = mock_conn
        result = workflow_ohne.run(cfg)
        assert result is False

    @patch("workflows.ohne_backup.load_project", return_value=True)
    @patch("workflows.ohne_backup.alter_db_connection_catalog", return_value=True)
    @patch("workflows.ohne_backup.unload_project", return_value=True)
    @patch("workflows.ohne_backup.disconnect_users", return_value=True)
    @patch("workflows.ohne_backup.mstr_connection")
    def test_alter_called_with_correct_settings(self, mock_ctx, mock_disc, mock_unload,
                                                mock_alter, mock_load, mock_conn, cfg):
        mock_ctx.return_value = mock_conn
        workflow_ohne.run(cfg)

        # Verify DB connection settings from cfg are passed correctly
        _, kwargs = mock_alter.call_args
        assert kwargs["connection_name"] == "SGB II - MaEnde - MSAS@DST"
        assert kwargs["new_catalog"] == "SGB2_MaEnde"


# ── mit_backup workflow ───────────────────────────────────────────────────────

class TestMitBackupWorkflow:

    @patch("workflows.mit_backup.revoke_security_role", return_value=True)
    @patch("workflows.mit_backup.load_project", return_value=True)
    @patch("workflows.mit_backup.alter_db_connection_catalog", return_value=True)
    @patch("workflows.mit_backup.duplicate_project", return_value=True)
    @patch("workflows.mit_backup.unload_project", return_value=True)
    @patch("workflows.mit_backup.disconnect_users", return_value=True)
    @patch("workflows.mit_backup.mstr_connection")
    def test_all_steps_succeed(self, mock_ctx, mock_disc, mock_unload, mock_dup,
                               mock_alter, mock_load, mock_revoke, mock_conn, cfg):
        mock_ctx.return_value = mock_conn
        result = workflow_mit.run(cfg, backup_month="202512")

        assert result is True
        mock_disc.assert_called_once()
        mock_unload.assert_called_once()
        mock_dup.assert_called_once()
        mock_alter.assert_called_once()
        assert mock_load.call_count == 2      # main project + backup project
        assert mock_revoke.call_count == 2    # one per role/group pair

    @patch("workflows.mit_backup.duplicate_project", return_value=False)  # FAILS
    @patch("workflows.mit_backup.unload_project", return_value=True)
    @patch("workflows.mit_backup.disconnect_users", return_value=True)
    @patch("workflows.mit_backup.mstr_connection")
    def test_aborts_on_duplicate_failure(self, mock_ctx, mock_disc,
                                         mock_unload, mock_dup, mock_conn, cfg):
        mock_ctx.return_value = mock_conn
        result = workflow_mit.run(cfg, backup_month="202512")
        assert result is False

    @patch("workflows.mit_backup.revoke_security_role", return_value=True)
    @patch("workflows.mit_backup.load_project", return_value=True)
    @patch("workflows.mit_backup.alter_db_connection_catalog", return_value=True)
    @patch("workflows.mit_backup.duplicate_project", return_value=True)
    @patch("workflows.mit_backup.unload_project", return_value=True)
    @patch("workflows.mit_backup.disconnect_users", return_value=True)
    @patch("workflows.mit_backup.mstr_connection")
    def test_backup_project_name_uses_month(self, mock_ctx, mock_disc, mock_unload,
                                            mock_dup, mock_alter, mock_load,
                                            mock_revoke, mock_conn, cfg):
        mock_ctx.return_value = mock_conn
        workflow_mit.run(cfg, backup_month="202503")

        _, kwargs = mock_dup.call_args
        assert kwargs["target_project_name"] == "SGB II MaEnde 202503"

    @patch("workflows.mit_backup.revoke_security_role", return_value=True)
    @patch("workflows.mit_backup.load_project", return_value=True)
    @patch("workflows.mit_backup.alter_db_connection_catalog", return_value=True)
    @patch("workflows.mit_backup.duplicate_project", return_value=True)
    @patch("workflows.mit_backup.unload_project", return_value=True)
    @patch("workflows.mit_backup.disconnect_users", return_value=True)
    @patch("workflows.mit_backup.mstr_connection")
    def test_revoke_called_for_each_pair(self, mock_ctx, mock_disc, mock_unload,
                                         mock_dup, mock_alter, mock_load,
                                         mock_revoke, mock_conn, cfg):
        mock_ctx.return_value = mock_conn
        workflow_mit.run(cfg, backup_month="202512")

        # Collect all (role, group) pairs that were revoked
        revoked_pairs = [
            (call.args[1], call.args[2])   # revoke_security_role(conn, role, group, project)
            for call in mock_revoke.call_args_list
        ]
        assert ("Normale Benutzer", "Everyone") in revoked_pairs
        assert ("Normale Benutzer", "SGB II Projektzugriff") in revoked_pairs

    @patch("workflows.mit_backup.revoke_security_role", return_value=True)
    @patch("workflows.mit_backup.load_project", return_value=True)
    @patch("workflows.mit_backup.alter_db_connection_catalog", return_value=True)
    @patch("workflows.mit_backup.duplicate_project", return_value=True)
    @patch("workflows.mit_backup.unload_project", return_value=True)
    @patch("workflows.mit_backup.disconnect_users", return_value=True)
    @patch("workflows.mit_backup.mstr_connection")
    def test_revoke_targets_backup_not_main_project(self, mock_ctx, mock_disc,
                                                    mock_unload, mock_dup, mock_alter,
                                                    mock_load, mock_revoke,
                                                    mock_conn, cfg):
        mock_ctx.return_value = mock_conn
        workflow_mit.run(cfg, backup_month="202512")

        # Security roles must be revoked on the BACKUP project, not the main project
        for call in mock_revoke.call_args_list:
            project_arg = call.args[3]  # revoke_security_role(conn, role, group, project)
            assert project_arg == "SGB II MaEnde 202512"
            assert project_arg != "SGB II MaEnde"


# ── Logger setup test ─────────────────────────────────────────────────────────

class TestLogger:

    def test_setup_creates_log_file(self, tmp_path):
        """Logger should create the log file on first run."""
        from utils.logger import setup_logger
        setup_logger(log_dir=tmp_path, log_file_name="test_run.log", command="ohne-backup")
        assert (tmp_path / "test_run.log").exists()

    def test_run_footer_written(self, tmp_path):
        """log_run_footer should append a footer line to the log file."""
        from utils.logger import setup_logger, log_run_footer
        setup_logger(log_dir=tmp_path, log_file_name="test_footer.log", command="test")
        log_run_footer(success=True)
        content = (tmp_path / "test_footer.log").read_text(encoding="utf-8")
        assert "RUN FINISHED" in content
        assert "SUCCESS" in content

    def test_failed_run_footer(self, tmp_path):
        """Footer should say FAILED when success=False."""
        from utils.logger import setup_logger, log_run_footer
        setup_logger(log_dir=tmp_path, log_file_name="test_fail.log", command="test")
        log_run_footer(success=False)
        content = (tmp_path / "test_fail.log").read_text(encoding="utf-8")
        assert "FAILED" in content
