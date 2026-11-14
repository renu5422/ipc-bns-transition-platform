"""Tests for JWT secret resolution (backend.api.auth.resolve_secret).

resolve_secret is a pure function of an env mapping, so these tests never
reload the module and cannot disturb the session ``auth_headers`` fixture.
"""

import logging

import pytest

from backend.api.auth import (
    DEV_SECRET,
    MIN_SECRET_LENGTH,
    InsecureSecretError,
    resolve_secret,
)

STRONG = "x" * MIN_SECRET_LENGTH + "-strong-random-looking-secret"


class TestProduction:
    @pytest.mark.parametrize("env", [
        {"APP_ENV": "production"},
        {"APP_ENV": "production", "AUTH_SECRET_KEY": ""},
        {"APP_ENV": "production", "AUTH_SECRET_KEY": "   "},
    ])
    def test_missing_key_raises(self, env):
        with pytest.raises(InsecureSecretError, match="is not set"):
            resolve_secret(env)

    def test_dev_default_raises(self):
        with pytest.raises(InsecureSecretError, match="dev default"):
            resolve_secret({"APP_ENV": "production", "AUTH_SECRET_KEY": DEV_SECRET})

    def test_placeholder_raises(self):
        env = {"APP_ENV": "production",
               "AUTH_SECRET_KEY": "change-me-generate-a-real-secret-please"}
        with pytest.raises(InsecureSecretError, match="placeholder"):
            resolve_secret(env)

    def test_short_key_raises(self):
        env = {"APP_ENV": "production", "AUTH_SECRET_KEY": "a" * (MIN_SECRET_LENGTH - 1)}
        with pytest.raises(InsecureSecretError, match="shorter than"):
            resolve_secret(env)

    def test_error_message_includes_generate_command(self):
        with pytest.raises(InsecureSecretError, match=r"secrets\.token_urlsafe\(48\)"):
            resolve_secret({"APP_ENV": "production"})

    def test_strong_key_ok(self):
        assert resolve_secret({"APP_ENV": "production", "AUTH_SECRET_KEY": STRONG}) == STRONG

    def test_app_env_case_insensitive(self):
        with pytest.raises(InsecureSecretError):
            resolve_secret({"APP_ENV": " Production "})


class TestDevelopment:
    @pytest.mark.parametrize("env", [{}, {"APP_ENV": "development"},
                                     {"AUTH_SECRET_KEY": ""}])
    def test_missing_key_falls_back_with_warning(self, env, caplog):
        with caplog.at_level(logging.WARNING, logger="ipc_bns.auth"):
            assert resolve_secret(env) == DEV_SECRET
        warnings = [r for r in caplog.records if r.levelno == logging.WARNING]
        assert len(warnings) == 1
        assert "insecure dev secret" in warnings[0].getMessage()

    def test_explicit_key_used_without_warning(self, caplog):
        with caplog.at_level(logging.WARNING, logger="ipc_bns.auth"):
            assert resolve_secret({"AUTH_SECRET_KEY": "short-is-fine-in-dev"}) == (
                "short-is-fine-in-dev"
            )
        assert not caplog.records
