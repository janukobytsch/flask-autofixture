import warnings
from flask import request, has_request_context
from .fixture import Fixture, __default_names__


class Command(object):
    """
    An abstract command to be executed by :class:`AutoFixture`.

    :param auto_fixture: the active :class:`AutoFixture`
    :param request_scope: whether the command should be executed for a
                          single request or all requests in the test
    """

    def __init__(self, auto_fixture, request_scope=True):
        self.auto_fixture = auto_fixture
        self.request_scope = request_scope

    def before_test(self, func, *args, **kwargs):
        """Hook to be invoked before the test method has been executed. May
        perform expensive setup here.

        :param func: the test method to be executed
        :param args: the test method's args
        :param kwargs: the test method's kwargs
        """
        pass

    def after_test(self, func, *args, **kwargs):
        """Hook to be invoked after the test method has been executed. May
        perform additional cleanup required by the command here.

        :param func: the test method to be executed
        :param args: the test method's args
        :param kwargs: the test method's kwargs
        """
        pass

    def execute(self, response):
        """Executes the command once with the response of the active
        request. This is called as a request hook on :class:`Flask`.

        :param response: the recorded :class:`Response`
        :return: the recorded :class:`Response
        """
        raise NotImplementedError()

    @property
    def has_request_scope(self):
        """Whether the command is scoped only for the current request or the
        whole test method. Request-specific commands will be executed once
        per request, test-specific commands only once per test.

        :return: true if request-scoped
        """
        return self.request_scope


class CreateFixtureCommand(Command):
    """
    A command which generates fixtures from a response object.

    :param request_name: the name of the :class:`Fixture` generated
                         from the :class:`Request`
    :param response_name: the name of the :class:`Fixture` generated
                          from the :class:`Response`
    :param request_scope: whether the command should be executed for a
                          single request or all requests in the test
    """

    def __init__(self,
                 auto_fixture,
                 request_name=None,
                 response_name=None,
                 request_scope=True):

        super().__init__(auto_fixture, request_scope=request_scope)

        self.request_name = request_name
        self.response_name = response_name

    def before_test(self, func, *args, **kwargs):
        if not self.auto_fixture.use_method_names:
            return

        # Use test method to determine fixture names
        if not self.request_name:
            self.request_name = func.__name__
        if not self.response_name:
            self.response_name = func.__name__

    def execute(self, response):
        """Generates fixture objects from the given response and stores them
        in the application-specific cache.

        :param response: the recorded :class:`Response`
        """
        if not has_request_context:
            return

        self._fallback_fixture_names()

        try:
            app = self.auto_fixture.app

            # Create response fixture
            fixture = Fixture.from_response(response, app, self.response_name)
            self.auto_fixture.add_fixture(fixture)

            # Create request fixture
            if request.data:
                fixture = Fixture.from_request(request, app, self.request_name)
                self.auto_fixture.add_fixture(fixture)
        except TypeError:  # pragma: no cover
            warnings.warn("Could not create fixture for unsupported mime type")

        return response

    def _fallback_fixture_names(self):
        """Falls back to the default fixture names if no names could be
        determined up to this point.
        """
        if not self.request_name or not self.response_name:
            warnings.warn(
                "No name was specified for the recorded fixture. Falling "
                "back to default names.")

        if not self.request_name:
            self.request_name = __default_names__[0]
        if not self.response_name:
            self.response_name = __default_names__[1]


class IgnoreFixtureCommand(object):
    pass
