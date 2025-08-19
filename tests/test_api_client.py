import os
import logging
import pytest
from config import LOGIN_URL

# Ensure log directory exists before importing the client module
os.makedirs('/home/tim/RFID3/logs', exist_ok=True)

from app.services.api_client import APIClient, session

class DummyAuthResponse:
    status_code = 200
    def json(self):
        return {'result': True, 'access_token': 'token'}

class DummyGetResponse:
    status_code = 200
    def json(self):
        return {'data': [], 'totalcount': 0}

class DummyPostResponse:
    status_code = 201
    def json(self):
        return {'result': 'ok'}


def test_limit_capped(monkeypatch, caplog):
    monkeypatch.setattr(session, 'post', lambda *args, **kwargs: DummyAuthResponse())
    monkeypatch.setattr(session, 'get', lambda *args, **kwargs: DummyGetResponse())

    client = APIClient()
    params = {'limit': 500}
    with caplog.at_level(logging.WARNING, logger='api_client'):
        client._make_request('dummy', params=params)
    assert params['limit'] == 200
    assert "exceeds API maximum of 200" in caplog.text


def test_post_uses_session(monkeypatch):
    calls = {'count': 0}

    def mock_post(url, *args, **kwargs):
        calls['count'] += 1
        if url == LOGIN_URL:
            return DummyAuthResponse()
        return DummyPostResponse()

    monkeypatch.setattr(session, 'post', mock_post)
    client = APIClient()
    response = client._make_request('dummy', method='POST', data={'foo': 'bar'})
    assert response == {'result': 'ok'}
    assert calls['count'] == 2
