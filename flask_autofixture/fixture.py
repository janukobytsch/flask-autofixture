from flask import request
import re

__mime_types__ = ['application/json', 'application/.*\+json']


class Fixture(object):
    """The fixture object represents a single file containing the request
    or response payload. It also keeps track of additional metadata
    required to store itself in the generated fixture directory.

    TODO:
    - polymorph on mime type

    :param data: the fixture payload
    :param app_name: the name of the :class:`Flask` application
    :param request_path: the route from which the payload originated
    :param request_method:  the request method from which the payload
                            originated
    :param is_response: whether the fixture wraps a :class:`Response`
                        or :class:`Request
    :param name: the name of the fixture e.g. to be used as a filename
    """

    def __init__(self, data, app_name, request_path,
                 request_method, is_response=True,
                 name=None):
        self.data = data
        # Metadata for fixture directory
        self.app_name = app_name
        self.request_path = request_path
        self.request_method = request_method
        self.is_response = is_response
        self._name = name

    @property
    def name(self):
        name = self._name + '_' if self._name else ''
        if self.is_response:
            name += 'response'
        else:
            name += 'request'
        return name

    @property
    def payload(self):
        return self.data.decode('utf-8')

    @property
    def type(self):
        return 'json'

    @classmethod
    def from_request(cls, app, request, name=None):
        if not Fixture.is_supported(request.mimetype):
            raise TypeError
        fixture = cls(request.data, app.name, request.path,
                      request.method, is_response=False, name=name)
        return fixture

    @classmethod
    def from_response(cls, app, response, name=None):
        if not Fixture.is_supported(response.mimetype):
            raise TypeError
        fixture = cls(response.get_data(), app.name, request.path,
                      request.method, name=name)
        return fixture

    @staticmethod
    def is_supported(mime_type):
        for supported_mime_type in __mime_types__:
            if re.match(supported_mime_type, mime_type):
                return True
        return False

    def __str__(self):
        return '<{} {}: {}>'.format(self.request_method, self.request_path,
                                    self.data)
