"""Pytest global config.

This is used here to provide fixtures across all test files."""

import os
import tempfile

import pytest

from wdra_extender import app as wdrax


@pytest.fixture
def client():
    """Flask test client fixture.

    See https://flask.palletsprojects.com/en/1.1.x/testing/.
    """
    db_fd, wdrax.app.config['DATABASE'] = tempfile.mkstemp()
    wdrax.app.config['TESTING'] = True

    with wdrax.app.test_client() as client:
        with wdrax.app.app_context():
            wdrax.register_extensions()
        yield client

    os.close(db_fd)
    os.unlink(wdrax.app.config['DATABASE'])


def test_empty_db(client):
    """Start with a blank database."""

    rv = client.get('/')
    assert b'No entries here so far' in rv.data


def login(client, username, password):
    return client.post('/login', data=dict(
        username=username,
        password=password
    ), follow_redirects=True)


def logout(client):
    return client.get('/logout', follow_redirects=True)