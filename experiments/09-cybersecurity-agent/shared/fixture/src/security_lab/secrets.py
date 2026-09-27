"""Intentionally unsafe fake credentials. These are not real secrets."""

SERVICE_API_KEY = "fake_service_key_for_security_fixture"
BACKUP_PASSWORD = "fake_backup_password_for_security_fixture"


def service_api_key() -> str:
    return SERVICE_API_KEY


def backup_password() -> str:
    return BACKUP_PASSWORD
