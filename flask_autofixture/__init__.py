"""
    flask.ext.autofixture
    ---------------
    This extension provides automatic recording of JSON fixtures for Flask
    right from your test suite.

    :copyright: (c) 2016 by Janusch Jacoby.
    :license: MIT/X11, see LICENSE for more details.
"""
import warnings
from flask import current_app, has_app_context
from functools import wraps
from contextlib import contextmanager
from .fixture import Fixture
from .storage import FileStorage, RouteLayout, RequestMethodLayout
from .command import CreateFixtureCommand

__all__ = ('AutoFixture', 'FileStorage', 'RouteLayout', 'RequestMethodLayout')
__ext_name__ = 'autofixture'

# prevent pyflakes from failing due to unused imports
assert (Fixture, FileStorage, RouteLayout, RequestMethodLayout,
        CreateFixtureCommand)


class AutoFixture(object):
    """
    A wrapper around the application for which to automatically generate
    fixtures by recording the incoming requests and outgoing responses.
    Once the application context is torn down, the recorded fixtures are
    flushed from the cache and persisted by the given :class:`Storage`
    in a fixture directory within the instance folder. The structure of
    the fixture directory is determined by the given :class:`StorageLayout`.

    To get started, you wrap your :class:`Flask` application under test
    in the setup method of your testing framework like this::

        app = create_app('testing')
        autofixture = AutoFixture(app)

    Alternatively, you can use :meth:`init_app` to set the Flask application
    after it has been constructed.

    :param app: :class:`Flask` application under test to be observed
    :param explicit_recording: whether test methods need to be annotated to
                               record fixtures
    :param fixture_directory: the name of the fixture directory to be generated
    :param fixture_dirpath: the path of the fixture directory's parent folder
    :param storage_class: the :class:`Storage` to which the cache is flushed
    :param storage_layout: the :class:`StorageLayout` for the fixture directory
    """

    def __init__(self, app=None,
                 explicit_recording=False,
                 fixture_dirname=__ext_name__,
                 fixture_dirpath=None,
                 storage_class=FileStorage,
                 storage_layout=RequestMethodLayout):

        self.explicit_recording = explicit_recording
        self.fixture_dirname = fixture_dirname
        self.fixture_dirpath = fixture_dirpath
        self.storage_layout = storage_layout
        self.storage_class = storage_class

        self._app = app

        # Stack for request-specific commands. These are pushed at the
        # beginning of the test and popped when executing the request hooks.
        self._request_cmd_stack = []

        # Stack for test-specific commands. These are pushed at the
        # beginning of the test and popped at the end of the test.
        self._test_cmd_stack = []

        # Internal flag whether the fixture directory has been reset
        # Required to avoid deletion of directory due to init_app in setUp
        self._has_reset_dir = False

        if app is not None:  # pragma: no cover
            self.init_app(app)

    def init_app(self, app):
        app.config.setdefault('RECORD_REQUESTS_ENABLED', True)

        # The storage responsible for persisting the cached fixtures
        self.storage = self.storage_class(self.storage_layout,
                                          self.fixture_dirname,
                                          self.fixture_path)

        # Setup app-specific cache
        if not hasattr(app, 'extensions'):  # pragma: no cover
            app.extensions = {}
        if __ext_name__ not in app.extensions:
            app.extensions[__ext_name__] = []

        if app.config['RECORD_REQUESTS_ENABLED']:
            # Reset the directory only once
            if not self._has_reset_dir:
                self.storage.reset_directory()
                self._has_reset_dir = True

            # Register hooks
            app.after_request(self._execute_commands)
            app.teardown_appcontext(self._teardown_callback)

    @property
    def app(self):
        """Convenience property to access the current application.

        :return: the active :class:`Flask` application
        """
        if self._app is not None:  # pragma: no cover
            return self._app

        return current_app

    @property
    def fixture_path(self):
        """The path of the parent folder containing the fixture directory.
        By default, the fixture directory is generated in the instance folder.
        """
        if self.fixture_dirpath:
            return self.fixture_dirpath
        return self.app.instance_path

    # ==== Caching ====

    @property
    def cache(self):
        """Convenience property to an application-specific fixture cache.

        :return: list of cached :class:`Fixtures`
        """
        return self.app.extensions[__ext_name__]

    @cache.setter
    def cache(self, value):
        """Setter for the application-specific fixture cache.

        :param value: the new cache
        """
        self.app.extensions[__ext_name__] = value

    def add_fixture(self, fixture):
        """Stores the given fixture in the application-specific fixture cache.

        :param fixture: the :class:`Fixture` to store
        """
        self.cache.append(fixture)

    def flush_fixtures(self):
        """Flushes the application-specific fixture cache to the persistent
        storage."""

        for fixture in self.cache:
            self.storage.store_fixture(fixture)

        # Clear cache
        self.cache = []

    # ==== Commands ====

    def _push_cmd(self, cmd):
        """Registers the given command on the request- or test-specific stack
        based on the request's scope.

        :param cmd: the :class:`Command` to register
        """
        if cmd.has_request_scope:
            self._push_request_cmd(cmd)
        else:
            self._push_test_cmd(cmd)

    def _clear_cmds(self):
        """Clears the internal stack for all commands regardless of scope."""
        self._clear_request_cmds()
        self._clear_test_cmds()

    def _push_request_cmd(self, cmd):
        """Registers the given request-specific command on the internal stack.

        :param cmd: the :class:`Command` to register
        """
        self._request_cmd_stack.append(cmd)

    def _pop_request_cmd(self):
        """Pops the last request-specific command from the internal stack.
        :return: the :class:`Command
        """
        return self._request_cmd_stack.pop()

    def _clear_request_cmds(self):
        """Clears the internal stack for request-specific commands."""
        self._request_cmd_stack = []

    def _push_test_cmd(self, cmd):
        """Registers the given test-specific command on the internal stack.

        :param cmd: the :class:`Command` to register
        """
        self._test_cmd_stack.append(cmd)

    def _clear_test_cmds(self):
        """Clear the internal stack for test-specific commands."""
        self._test_cmd_stack = []

    def _execute_commands(self, response):
        """Executes all commands registered on the internal stacks to e.g.
        to generate fixtures. Request-specific commands will be executed once
        per request, test-specific commands only once per test.

        :param response: the recorded :class:`Response`
        :return: the recorded :class:`Response`
        """

        # Collect applicable commands
        commands = []
        if len(self._request_cmd_stack):
            # Pop command scoped for the current request
            cmd = self._pop_request_cmd()
            commands.append(cmd)
        commands += self._test_cmd_stack

        if not self.explicit_recording:
            # Lazily add the command to generate fixtures
            if not any(isinstance(x, CreateFixtureCommand) for x in commands):
                cmd = CreateFixtureCommand()
                self._push_cmd(cmd)
                commands.append(cmd)

        for command in commands:
            command.execute(response, self)

        return response

    # ==== Decorators ====

    def record(self, request_name=None, response_name=None):
        """A parametrized per-request decorator for usage in test methods to
        generate a fixture with a descriptive name. Falls back to the
        default names if not specified otherwise.

        Example usage:

            @autofixture.record(request_name="missing_email",
                                response_name="missing_email_response")
            def test_missing_email_returns_bad_request(self):
                response = self.client.post(
                    url_for('api.new_user'),
                    data=json.dumps({'name': 'john'}))
                self.assertTrue(response.status_code == 400)

        When performing multiple request in a single test method, please
        note that decorators need to be applied in the reverse order.

        :param request_name: the name of the request :class:`Fixture` to be
                             generated
        :param response_name: the name of the request :class:`Fixture` to be
                              generated
        :return: the decorator
        """
        if not request_name and not response_name:
            warnings.warn(
                "Please specify a name for the fixture to generate. Falling "
                "back to default names.")
            cmd = CreateFixtureCommand()
        else:
            cmd = CreateFixtureCommand(request_name, response_name)

        return self._create_command_decorator(cmd)

    def record_all(self, func):
        """A per-test decorator to automatically generate fixtures for all
        requests executed the the decorated test method.

        Example usage:

            @autofixture.record_all
            def test_missing_email_returns_bad_request(self):
                response1 = client.get('/route1')
                response2 = client.get('/route2')

        This should not be used together with the :meth:`record` decorator if
        requests should not be recorded twice.

        :param func: the test method to be decorated
        :return: the decorated test method
        """

        # Setup command with test scope
        cmd = CreateFixtureCommand()
        cmd.request_scope = False

        decorator = self._create_command_decorator(cmd)

        return decorator(func)

    def _create_command_decorator(self, cmd):
        """Factory method to create a test method decorator which manages the
        lifecycle of the given command on the internal stack and calls the
        appropriate hooks.

        :param cmd: the :class:`Command` to manage
        :return: the decorator
        """

        @contextmanager
        def command_context(cmd, *args, **kwargs):
            """A context manager to wrap test methods.

            :param cmd: the :class:`Command` to be registered
            :param args: the test methods args
            :param kwargs: the test method kwargs
            """
            self._push_cmd(cmd)
            # Invoke hooks and execute test method
            for command in self._request_cmd_stack:
                command.before_test(*args, **kwargs)
            yield  # to the test method
            for command in self._request_cmd_stack:
                command.after_test(*args, **kwargs)
            # Clear all commands regardless of scope
            # This will clear any remaining request-scoped commands hence
            self._clear_cmds()

        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                # Execute test method with command context
                with command_context(cmd, *args, **kwargs):
                    result = func(*args, **kwargs)
                return result

            return wrapper

        return decorator

    # ==== Callbacks ====

    def _teardown_callback(self, exception):
        """The custom callback to be called when tearing down the application
        context.

        :param exception:
        """
        if not has_app_context:
            return

        self.flush_fixtures()
