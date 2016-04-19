import pytest
import os
from flask import Flask, jsonify
from flask_autofixture import AutoFixture, Fixture


def cwd():
    return os.path.dirname(os.path.realpath(__file__))


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


@pytest.fixture(scope='function')
def routeapp(request, testapp):
    """Returns Flask app with established app context and registered routes."""
    url, url2, url3, url4 = '/lorem', '/life', '/world', '/echo'

    # Store routes for later retrieval
    testapp.routes = [url, url2, url3, url4]

    @testapp.route(url, methods=['GET'])
    def lorem():
        return jsonify(title="lorem ipsum",
                       body="lorem ipsum dolor sit amet...")

    @testapp.route(url2, methods=['GET'])
    def life():
        return jsonify(title="about life",
                       body="life is beautiful")

    @testapp.route(url3, methods=['GET'])
    def world():
        return jsonify(title="hello",
                       body="world")

    @testapp.route(url4, methods=['POST'])
    def echo():
        from flask import request
        return jsonify(echo=request.data.decode('utf8'))

    return testapp


@pytest.fixture
def auto_fixture():
    return AutoFixture(fixture_dirpath=cwd())


@pytest.fixture
def fixture():
    return Fixture('{"body":"lorem ipsum"}'.encode("utf8"), 'fixture-name',
                   __name__, "/resource", "GET")


def record_decorator_config():
    yield ('foo', 'bar')
    yield ('foo', None)
    yield (None, 'bar')
    yield (None, None)
