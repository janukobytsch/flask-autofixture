*****************
Flask-AutoFixture
*****************

|version| |license| |travis|

Flask-AutoFixture is an extension that automatically records JSON fixtures right from the test suite by hooking into the request callbacks of your Flask application.


Installation
============


::

    pip install flask-autofixture


Quickstart
==========

To get started, simply wrap your ``Flask`` application under test in the setup method of your testing framework like this:

.. code-block:: python

    import unittest
    from app import create_app
    from flask.ext.autofixture import AutoFixture

    autofixture = AutoFixture()

    class APITestCase(unittest.TestCase):
        def setUp(self):
            self.app = create_app('testing')
            # Register the app for recording
            autofixture.init_app(self.app)
            self.app_context = self.app.app_context()
            self.app_context.push()
            self.client = self.app.test_client()

        def tearDown(self):
            self.app_context.pop()

Instead of passing the Flask instance directly to the ``AutoFixture`` constructor, you can use ``init_app`` to initialize Flask afterwards. If you are using a factory to create your Flask instance or want to configure the recording of your fixtures (see below), this is the recommended approach.

Then simply run your test suite. Fixtures for every request executed by the ``test_client`` will magically appear in your instance folder.


Configuration
=============

Recording
---------

Flask-AutoFixture provides parametrized decorators to configure fixture generation on individual test methods.

To provide a descriptive name for the generated fixture, simply annotate the test method with the ``record`` decorator like so:

.. code-block:: python

    from app import create_app
    from flask.ext.autofixture import AutoFixture

    app = create_app('testing')
    autofixture = AutoFixture(app)

    @autofixture.record(request_name="missing_email_request",
                        response_name="missing_email_resonse")
    def test_missing_email_returns_bad_request(self):
        response = self.client.post(
            url_for('api.new_user'),
            data=json.dumps({'name': 'john'}))
        self.assertTrue(response.status_code == 400)


By default, ``AutoFixture`` will record all requests and responses automatically. If you want to record requests only in a specific set of test methods, you can disable this behaviour in the ``AutoFixture`` constructor by means of the ``explicit_recording`` argument:

.. code-block:: python

    from app import create_app
    from flask.ext.autofixture import AutoFixture

    app = create_app('testing')
    autofixture = AutoFixture(app, explicit_recording=True)


If ``explicit_recording`` is enabled, you must declare individual requests to be recorded using the ``record`` decorator. Alternatively, if a test methods performs multiple requests, you can apply the ``record_all`` decorator to avoid nested ``record`` decorators.

Fixture directory
-----------------

By default, the generated fixtures will be stored in your app's instance folder (1) in an ``autofixture`` directory. You can specify an alternative path and name for the generated directory in the ``AutoFixture`` constructor like so:

.. code-block:: python

    from flask.ext.autofixture import AutoFixture, RouteLayout
    
    autofixture = AutoFixture(app,
                              fixture_dirname="mydir",
                              fixture_dirpath="/path/to/project",
                              storage_layout=RouteLayout)


The generated directory is laid out according to the ``StorageLayout`` specified in the ``AutoFixture`` constructor. The default layout is ``RequestMethodLayout``:

.. code-block:: python

    class RequestMethodLayout(StorageLayout):
        """This strategy lays out a :class:`Fixture` by its request method first.

        Example directory structure:

            /autofixture                        (the name of the extension)
                /app                            (the name of the app)
                    /GET                        (the request method)
                        /api-posts              (the request path)
                            response.json
                    /POST
                        /api-posts
                            request.json        (the request payload)
                            response.json       (the response data)
                            request_2.json
                            response_2.json
        """

(1) http://flask.pocoo.org/docs/0.10/config/#instance-folders


Roadmap
=======

- Support further mime types
- Support request context manager (trigger preprocess_request)
- Get listed in the Flask extension registry


.. |version| image:: http://img.shields.io/pypi/v/flask-autofixture.svg?style=flat
    :target: https://pypi.python.org/pypi/Flask-AutoFixture/

.. |license| image:: http://img.shields.io/pypi/l/flask-autofixture.svg?style=flat
    :target: https://pypi.python.org/pypi/Flask-AutoFixture/

.. |travis| image:: https://api.travis-ci.org/janukobytsch/flask-autofixture.svg?branch=master
    :target: https://travis-ci.org/janukobytsch/flask-autofixture
