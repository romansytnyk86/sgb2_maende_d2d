"""
tests/test_config.py - Unit tests for config loading and parsing.
No MicroStrategy connection required.
"""

import sys
import pytest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from config import load_config, _parse_revoke_pairs, _require


# ── _parse_revoke_pairs ───────────────────────────────────────────────────────

class TestParseRevokePairs:
    def test_single_pair(self):
        result = _parse_revoke_pairs("Normale Benutzer|Everyone")
        assert result == [("Normale Benutzer", "Everyone")]

    def test_multiple_pairs(self):
        raw = "Normale Benutzer|Everyone,Normale Benutzer|SGB II Projektzugriff"
        result = _parse_revoke_pairs(raw)
        assert len(result) == 2
        assert result[0] == ("Normale Benutzer", "Everyone")
        assert result[1] == ("Normale Benutzer", "SGB II Projektzugriff")

    def test_empty_string(self):
        assert _parse_revoke_pairs("") == []

    def test_whitespace_trimmed(self):
        result = _parse_revoke_pairs("  Role A | Group B  ")
        assert result == [("Role A", "Group B")]

    def test_malformed_entry_skipped(self):
        # Entry without "|" separator should be silently skipped
        result = _parse_revoke_pairs("NoSeparatorEntry,Role|Group")
        assert result == [("Role", "Group")]

    def test_three_pairs(self):
        raw = "Role1|Group1,Role2|Group2,Role3|Group3"
        result = _parse_revoke_pairs(raw)
        assert len(result) == 3
        assert result[2] == ("Role3", "Group3")


# ── _require ──────────────────────────────────────────────────────────────────

class TestRequire:
    def test_valid_value_returned(self):
        # _require(key, value, env_file) — env_file has a default so 2 args is fine
        assert _require("KEY", "value") == "value"

    def test_none_exits(self):
        with pytest.raises(SystemExit):
            _require("MISSING_KEY", None)

    def test_empty_string_exits(self):
        with pytest.raises(SystemExit):
            _require("EMPTY_KEY", "")

    def test_custom_env_file_named_in_error(self, capsys):
        # Error message should mention the env file so the user knows where to look
        with pytest.raises(SystemExit):
            _require("KEY", None, "my_custom.env")
        captured = capsys.readouterr()
        assert "my_custom.env" in captured.out


# ── load_config ───────────────────────────────────────────────────────────────

class TestLoadConfig:
    def test_loads_valid_env(self, tmp_path):
        env_file = tmp_path / "credentials.env"
        env_file.write_text(
            "MSTR_BASE_URL=http://localhost:8080/MicroStrategyLibrary\n"
            "MSTR_USERNAME=Administrator\n"
            "MSTR_PASSWORD=secret\n"
            "MSTR_LOGIN_MODE=1\n"
            "MSTR_PROJECT_NAME=SGB II MaEnde\n"
            "DB_CONNECTION_NAME=SGB II - MaEnde - MSAS@DST\n"
            "DB_CATALOG_NAME=SGB2_MaEnde\n"
            "REVOKE_ROLE_GROUP_PAIRS=Normale Benutzer|Everyone\n"
        )
        cfg = load_config(str(env_file))

        assert cfg.mstr.base_url == "http://localhost:8080/MicroStrategyLibrary"
        assert cfg.mstr.username == "Administrator"
        assert cfg.mstr.login_mode == 1
        assert cfg.project.project_name == "SGB II MaEnde"
        assert cfg.project.db_catalog_name == "SGB2_MaEnde"
        assert cfg.project.revoke_role_group_pairs == [("Normale Benutzer", "Everyone")]

    def test_missing_env_file_exits(self, tmp_path):
        with pytest.raises(SystemExit):
            load_config(str(tmp_path / "nonexistent.env"))

    def test_missing_required_field_exits(self, tmp_path):
        env_file = tmp_path / "credentials.env"
        # MSTR_PASSWORD intentionally missing
        env_file.write_text(
            "MSTR_BASE_URL=http://localhost:8080/MicroStrategyLibrary\n"
            "MSTR_USERNAME=Administrator\n"
            "MSTR_PROJECT_NAME=SGB II MaEnde\n"
            "DB_CONNECTION_NAME=SGB II - MaEnde - MSAS@DST\n"
            "DB_CATALOG_NAME=SGB2_MaEnde\n"
        )
        with pytest.raises(SystemExit):
            load_config(str(env_file))

    def test_default_login_mode(self, tmp_path):
        env_file = tmp_path / "credentials.env"
        # MSTR_LOGIN_MODE not set — should default to 1
        env_file.write_text(
            "MSTR_BASE_URL=http://localhost:8080/MicroStrategyLibrary\n"
            "MSTR_USERNAME=Administrator\n"
            "MSTR_PASSWORD=secret\n"
            "MSTR_PROJECT_NAME=SGB II MaEnde\n"
            "DB_CONNECTION_NAME=conn\n"
            "DB_CATALOG_NAME=catalog\n"
        )
        cfg = load_config(str(env_file))
        assert cfg.mstr.login_mode == 1

    def test_backup_base_name_defaults_to_project_name(self, tmp_path):
        env_file = tmp_path / "credentials.env"
        # BACKUP_PROJECT_BASE_NAME not set — should fall back to MSTR_PROJECT_NAME
        env_file.write_text(
            "MSTR_BASE_URL=http://localhost:8080/MicroStrategyLibrary\n"
            "MSTR_USERNAME=Administrator\n"
            "MSTR_PASSWORD=secret\n"
            "MSTR_PROJECT_NAME=SGB II MaEnde\n"
            "DB_CONNECTION_NAME=conn\n"
            "DB_CATALOG_NAME=catalog\n"
        )
        cfg = load_config(str(env_file))
        assert cfg.project.backup_base_name == "SGB II MaEnde"

    def test_log_file_defaults_to_project_name(self, tmp_path):
        env_file = tmp_path / "credentials.env"
        env_file.write_text(
            "MSTR_BASE_URL=http://localhost:8080/MicroStrategyLibrary\n"
            "MSTR_USERNAME=Administrator\n"
            "MSTR_PASSWORD=secret\n"
            "MSTR_PROJECT_NAME=My Project\n"
            "DB_CONNECTION_NAME=conn\n"
            "DB_CATALOG_NAME=catalog\n"
        )
        cfg = load_config(str(env_file))
        assert cfg.log.log_file_name == "LOG_My Project.txt"

    def test_empty_revoke_pairs(self, tmp_path):
        env_file = tmp_path / "credentials.env"
        env_file.write_text(
            "MSTR_BASE_URL=http://localhost:8080/MicroStrategyLibrary\n"
            "MSTR_USERNAME=Administrator\n"
            "MSTR_PASSWORD=secret\n"
            "MSTR_PROJECT_NAME=SGB II MaEnde\n"
            "DB_CONNECTION_NAME=conn\n"
            "DB_CATALOG_NAME=catalog\n"
            "REVOKE_ROLE_GROUP_PAIRS=\n"
        )
        cfg = load_config(str(env_file))
        assert cfg.project.revoke_role_group_pairs == []
