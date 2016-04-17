from flask import jsonify, Response
from flask_autofixture import AutoFixture, autofixture
from unittest import mock
import os


def add_route(testapp):
    url = '/resource'

    @testapp.route(url)
    def get():
        return jsonify(title="lorem ipsum",
                       body="lorem ipsum dolor sit amet...")

    return url


def test_extract_fixtures_after_request(testapp):
    # Given
    auto_fixture = AutoFixture()

    with mock.patch.object(auto_fixture, '_extract_fixtures',
                           autospec=True) as mock_method:
        auto_fixture.init_app(testapp)

        with testapp.test_request_context('/resource'):
            assert not mock_method.called
            # When
            resp = Response('payload')
            # For the test request context, after request hooks need
            # to be triggered manually
            testapp.process_response(resp)

            # Then
            assert mock_method.called


def test_flush_fixtures_on_app_ctx_teardown(app):
    # Given
    auto_fixture = AutoFixture()

    with mock.patch.object(auto_fixture, '_flush_fixtures',
                           autospec=True) as mock_method:
        ctx = app.app_context()
        ctx.push()
        auto_fixture.init_app(app)
        assert not mock_method.called

        # When
        ctx.pop()

        # Then
        assert mock_method.called


def test_record_json_response(testapp):
    # Given
    auto_fixture = AutoFixture()
    auto_fixture.init_app(testapp)
    url = add_route(testapp)

    # When
    with testapp.test_client() as client:
        response = client.get(url)

    # Then
    assert len(auto_fixture.cache) == 1


def test_name_decorator(testapp):
    # Given
    auto_fixture = AutoFixture()
    auto_fixture.init_app(testapp)
    name = "foobar"

    class TestCase(object):
        def __init__(self, auto_fixture):
            self.autofixture = auto_fixture

        @autofixture(name)
        def run_test_method(self):
            url = add_route(testapp)
            with testapp.test_client() as client:
                response = client.get(url)
            assert response is not None

    # When
    test_case = TestCase(auto_fixture)
    test_case.run_test_method()

    # Then
    fixture = auto_fixture.cache[0]
    assert name in fixture.name


def test_flush_entries_from_cache(testapp, fixture):
    # Given
    cwd = os.path.dirname(os.path.realpath(__file__))
    auto_fixture = AutoFixture(fixture_dirpath=cwd)
    auto_fixture.init_app(testapp)
    auto_fixture.cache = [fixture, fixture]

    # When
    auto_fixture._flush_fixtures(object())  # call directly, not by hook

    # Then
    assert not len(auto_fixture.cache)

    # When
    file_count = 0
    for root, dirs, files in os.walk(auto_fixture.storage.fixture_directory):
        for file in files:
            file_count += 1

    # Then
    assert file_count == 2
