from flask import jsonify, Response
from unittest import mock
from flask_autofixture import AutoFixture
from .conftest import record_decorator_config
import os
import pytest


# ==== Callbacks ====


def test_execute_commands_after_request(auto_fixture, testapp):
    # Given
    with mock.patch.object(auto_fixture, '_execute_commands',
                           autospec=True) as mock_method:
        auto_fixture.init_app(testapp)

        with testapp.test_request_context('/foobar'):
            assert not mock_method.called

            # When
            resp = Response('payload')
            # For the test request context, after request hooks need
            # to be triggered manually
            testapp.process_response(resp)

            # Then
            assert mock_method.called


def test_flush_fixtures_on_app_ctx_teardown(auto_fixture, app):
    # Given
    with mock.patch.object(auto_fixture, 'flush_fixtures',
                           autospec=True) as mock_method:
        ctx = app.app_context()
        ctx.push()
        auto_fixture.init_app(app)
        assert not mock_method.called

        # When
        ctx.pop()

        # Then
        assert mock_method.called


# ==== Recording ====


@pytest.mark.parametrize("decorator_name, decorator_kwargs", [
    (AutoFixture.record.__name__, {
        'request_name': 'foo',
        'response_name': 'bar'}),
    (AutoFixture.record.__name__, {
        'request_name': None,
        'response_name': None})  # should fall back to default names
])
def test_decorator_push_cmd_on_stack(auto_fixture, testapp, decorator_name,
                                     decorator_kwargs):
    # Given
    auto_fixture.explicit_recording = True

    decorator = getattr(auto_fixture, decorator_name)
    if decorator_kwargs:
        decorator = decorator(auto_fixture, decorator_kwargs)

    def dummy_test_method():
        assert True

    # Apply parametrized decorator
    dummy_test_method = decorator(dummy_test_method)

    with mock.patch.object(auto_fixture, '_push_cmd',
                           autospec=True) as mock_method:
        assert not mock_method.called

        # When
        dummy_test_method()

        # Then
        assert mock_method.called


def test_record_if_implicit(auto_fixture, routeapp):
    # Given
    auto_fixture.init_app(routeapp)

    def dummy_test_method():
        with routeapp.test_client() as client:
            _ = client.get(routeapp.routes[0])
            _ = client.get(routeapp.routes[1])

    # When
    dummy_test_method()

    # Then
    assert len(auto_fixture.cache) == 2


def test_record_if_explicit_and_request_decorator(auto_fixture, routeapp):
    # Given
    auto_fixture.explicit_recording = True
    auto_fixture.init_app(routeapp)
    request_name1, request_name2 = 'foo', 'foo2'

    @auto_fixture.record(request_name=request_name2, response_name='bar')
    @auto_fixture.record(request_name=request_name1, response_name='bar')
    def dummy_test_method():
        with routeapp.test_client() as client:
            _ = client.get(routeapp.routes[0])
            _ = client.get(routeapp.routes[1])
            # Last request shouldn't be recorded due to missing decorator
            _ = client.get(routeapp.routes[2])

    # When
    dummy_test_method()

    # Then
    assert len(auto_fixture.cache) == 2
    assert auto_fixture.cache[0].name == request_name1
    assert auto_fixture.cache[1].name == request_name2


@pytest.mark.parametrize("explicit_recording", [True, False])
def test_record_all__test_decorator(auto_fixture, routeapp,
                                    explicit_recording):
    # Given
    auto_fixture.explicit_recording = explicit_recording
    auto_fixture.init_app(routeapp)

    @auto_fixture.record_all
    def dummy_test_method():
        with routeapp.test_client() as client:
            _ = client.get(routeapp.routes[0])
            _ = client.get(routeapp.routes[1])
            _ = client.get(routeapp.routes[2])

    # When
    dummy_test_method()

    # Then
    assert len(auto_fixture.cache) == 3


def test_dont_record_if_explicit_and_missing_decorator(auto_fixture, routeapp):
    # Given
    auto_fixture.explicit_recording = True
    auto_fixture.init_app(routeapp)

    def dummy_test_method():
        with routeapp.test_client() as client:
            response = client.get(routeapp.routes[0])

    # When
    dummy_test_method()

    # Then
    assert len(auto_fixture.cache) == 0


@pytest.mark.parametrize("request_name, response_name",
                         [cfg for cfg in record_decorator_config()])
def test_record_only_once_if_implicit_and_decorator(auto_fixture,
                                                    routeapp,
                                                    request_name,
                                                    response_name):
    # Given
    auto_fixture.init_app(routeapp)

    @auto_fixture.record(request_name=request_name,
                         response_name=response_name)
    def dummy_test_method():
        with routeapp.test_client() as client:
            response = client.post(routeapp.routes[3],
                                   data='{"hello":"world"}',
                                   content_type='application/json')

    # When
    dummy_test_method()

    # Then
    assert len(auto_fixture.cache) == 2


@pytest.mark.parametrize("request_name, response_name",
                         [cfg for cfg in record_decorator_config()])
def test_post_request_records_two_fixtures(auto_fixture, routeapp,
                                           request_name,
                                           response_name):
    auto_fixture.explicit_recording = True
    test_record_only_once_if_implicit_and_decorator(auto_fixture,
                                                    routeapp,
                                                    request_name,
                                                    response_name)


# ==== Storage ====


def test_flush_entries_from_cache(auto_fixture, testapp, fixture):
    # Given
    auto_fixture.init_app(testapp)
    auto_fixture.cache = [fixture, fixture]

    # When
    auto_fixture.flush_fixtures()  # call directly, not by hook

    # Then
    assert not len(auto_fixture.cache)

    # When
    file_count = 0
    for root, dirs, files in os.walk(
            auto_fixture.storage.fixture_directory):
        for file in files:
            file_count += 1

    # Then
    assert file_count == 2


def test_reset_fixture_directory(auto_fixture, testapp):
    # Given
    with mock.patch('flask_autofixture.storage.shutil') as mock_shutil:
        assert not mock_shutil.rmtree.called

        # When
        auto_fixture.init_app(testapp)
        auto_fixture.init_app(testapp)

        # Then
        assert mock_shutil.rmtree.called
        assert mock_shutil.rmtree.call_count == 1
