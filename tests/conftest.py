import pytest
from flask import Flask
from flask_autofixture import Fixture


@pytest.fixture
def app():
    """Provide instance for basic Flask app under test."""
    app = Flask(__name__)
    return app


@pytest.fixture(scope='function')
def testapp(request, app):
    """Return basic Flask app with an established app context."""
    ctx = app.app_context()
    ctx.push()

    def teardown():
        ctx.pop()

    request.addfinalizer(teardown)

    return app


@pytest.fixture
def fixture():
    return Fixture('"body":"lorem ipsum"'.encode("utf8"),
                   __name__, "/resource", "GET")
