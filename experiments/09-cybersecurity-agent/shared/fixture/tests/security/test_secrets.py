from security_lab.secrets import backup_password, service_api_key


def test_service_key_comes_from_environment(monkeypatch):
    monkeypatch.setenv("SERVICE_API_KEY", "runtime-service-key")
    assert service_api_key() == "runtime-service-key"


def test_backup_password_comes_from_environment(monkeypatch):
    monkeypatch.setenv("BACKUP_PASSWORD", "runtime-backup-password")
    assert backup_password() == "runtime-backup-password"
