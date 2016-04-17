*****************
Flask-AutoFixture
*****************

|version| |license|

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

    class APITestCase(unittest.TestCase):
        def setUp(self):
            self.app = create_app('testing')
            self.autofixture = AutoFixture(self.app)
            self.app_context = self.app.app_context()
            self.app_context.push()
            self.client = self.app.test_client()

        def tearDown(self):
            self.app_context.pop()

Alternatively, you can use ``init_app`` to initialize Flask after ``AutoFixture`` has been constructed.

Run your test suite and fixtures for every request executed by the ``test_client`` will magically appear in your instance folder afterwards.


Configuration
=============

Fixture directory
-----------------

By default, the generated fixtures will be stored in your app's instance folder (1) in an ``autofixture`` directory. You can specify an alternative path and name for the generated directory in the ``AutoFixture`` constructor like so:

.. code-block:: python

    from flask.ext.autofixture import AutoFixture, RouteLayout
    
    autofixture = AutoFixture(app,
                              fixture_dirname="mydir",
                              fixture_dirpath="/path/to/project",
                              layout=RouteLayout)


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

Test decorators
---------------

Flask-AutoFixture provides parametrized decorators to configure fixture generation on individual test methods.

To provide a descriptive name for the generated fixture, simply annotate the test method with ``autofixture`` like so:

.. code-block:: python

    from flask.ext.autofixture import autofixture

    @autofixture("missing_email")
    def test_missing_email_returns_bad_request(self):
        response = self.client.post(
            url_for('api.new_user'),
            data=json.dumps({'name': 'john'}))
        self.assertTrue(response.status_code == 400)

Roadmap
=======

- Support further mime types
- Support request context manager (trigger preprocess_request)
- Additional decorators for configuring individual test methods


.. |version| image:: http://img.shields.io/pypi/v/flask-autofixture.svg?style=flat
    :target: https://pypi.python.org/pypi/Flask-AutoFixture/

.. |license| image:: http://img.shields.io/pypi/l/flask-autofixture.svg?style=flat
    :target: https://pypi.python.org/pypi/Flask-AutoFixture/
