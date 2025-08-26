import os
import sys
import logging
import types
import pytest

# Ensure root directory is on sys.path for config and app imports
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from config import LOGIN_URL, BASE_DIR

# Ensure log directory exists before importing the client module
os.makedirs(os.path.join(BASE_DIR, 'logs'), exist_ok=True)

from app.services.api_client import APIClient

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
    captured = {}

    def dummy_get(url, headers=None, params=None, timeout=None):
        captured['limit'] = params.get('limit')
        return DummyGetResponse()

    dummy_session = types.SimpleNamespace(
        post=lambda *args, **kwargs: DummyAuthResponse(),
        get=dummy_get,
    )
    monkeypatch.setattr(
        'app.services.api_client.create_session', lambda: dummy_session
    )

    client = APIClient()
    params = {'limit': 500}
    with caplog.at_level(logging.WARNING, logger='api_client'):
        client._make_request('dummy', params=params)
    assert params['limit'] == 500
    assert captured['limit'] == 200
    assert "exceeds API maximum of 200" in caplog.text


def test_post_uses_session(monkeypatch):
    calls = {'count': 0}

    def mock_post(url, *args, **kwargs):
        calls['count'] += 1
        if url == LOGIN_URL:
            return DummyAuthResponse()
        return DummyPostResponse()

    dummy_session = types.SimpleNamespace(post=mock_post)
    monkeypatch.setattr(
        'app.services.api_client.create_session', lambda: dummy_session
    )

    client = APIClient()
    response = client._make_request('dummy', method='POST', data={'foo': 'bar'})
    assert response == {'result': 'ok'}
    assert calls['count'] == 2
