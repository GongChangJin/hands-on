"""Credentials loaded from the runtime environment."""

import os


def service_api_key() -> str:
    return os.environ["SERVICE_API_KEY"]


def backup_password() -> str:
    return os.environ["BACKUP_PASSWORD"]
