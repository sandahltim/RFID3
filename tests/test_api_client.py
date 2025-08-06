import os
import logging
import pytest

# Ensure log directory exists before importing the client module
os.makedirs('/home/tim/RFID3/logs', exist_ok=True)

from app.services.api_client import APIClient

class DummyAuthResponse:
    status_code = 200
    def json(self):
        return {'result': True, 'access_token': 'token'}

class DummyGetResponse:
    status_code = 200
    def json(self):
        return {'data': [], 'totalcount': 0}


def test_limit_capped(monkeypatch, caplog):
    import requests
    monkeypatch.setattr(requests, 'post', lambda *args, **kwargs: DummyAuthResponse())
    monkeypatch.setattr(requests, 'get', lambda *args, **kwargs: DummyGetResponse())

    client = APIClient()
    params = {'limit': 500}
    with caplog.at_level(logging.WARNING, logger='api_client'):
        client._make_request('dummy', params=params)
    assert params['limit'] == 200
    assert "exceeds API maximum of 200" in caplog.text
