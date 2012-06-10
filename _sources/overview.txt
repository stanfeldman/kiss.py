***********************
Overview
***********************

Kiss.py is MVC web framework in Python with Gevent, Jinja2, Werkzeug.

You can break your app to views, controllers and models.

Controller is class inherited from class Controller and may have methods get, post, put, delete.
These methods get Request object param and return Response object.
Request and Response objects inherited from Werkzeug.

Features
========
* Django-like templates from Jinja2.
* You can add your static path in settings and all css and javascript files will be minified.
* Also html templates will be minified.
* In css files you can use SCSS syntax.
* ORM with PostgreSQL, MySQL and SQLite(Peewee).
* Event dispatcher. You can subscribe to event or publish event.
