import pytest


@pytest.fixture(autouse=True)
def set_up(monkeypatch):
    monkeypatch.setenv('TABLE_NAME', 'test-table')
    monkeypatch.setenv('TWILIO_ACCOUNT_SID', 'ACXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX')
    monkeypatch.setenv('TWILIO_AUTH_TOKEN', 'my_auth_token')