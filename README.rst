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

Alternatively, you can use ``init_app`` to initialize Flask after ``AutoFixture` has been constructed.

Run your test suite and fixtures for every request with the ``test_client`` will magically appear in your instance folder afterwards.


Roadmap
=======

- Support further mime types
- Support request context manager (trigger preprocess_request)
- Additional decorators for configuring individual test methods


.. |version| image:: http://img.shields.io/pypi/v/flask-autofixture.svg?style=flat
    :target: https://pypi.python.org/pypi/flask-logconfig/

.. |license| image:: http://img.shields.io/pypi/l/flask-autofixture.svg?style=flat
    :target: https://pypi.python.org/pypi/flask-logconfig/
