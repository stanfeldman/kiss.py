***********************
Example
***********************

Git repository includes example minimal project. You can use it as start point.

main.py
=======

.. code-block:: python

	from settings import options
	from kiss.core.application import Application
	app = Application(options)
	app.start()
	
settings.py
=============

.. code-block:: python

	from kiss.core.application import Application
	from controllers.controller1 import Controller1
	from controllers.controller2 import Controller2
	from kiss.core.events import ApplicationStarted
	from kiss.controllers.events import BeforeControllerAction
	from kiss.models import SqliteDatabase
	from kiss.core.exceptions import InternalServerError
	options = {
		"application": {
			"address": "127.0.0.1",
			"port": 8080
		},
		"urls": {
			"": Controller1,
			"users": {
				"(?P<user>\w+)": Controller2
			},
			"2": {
				"3": Controller1,
				"4": Controller2
			}
		},
		"views": {
			"templates_path": "views.templates",
			"static_path": "views.static"
		},
		"events": {
			ApplicationStarted: Controller2.application_after_load,
			BeforeControllerAction: Controller2.before_controller_action,
			InternalServerError.code: Controller2.internal_server_error
		},
		"models": {
			"engine": SqliteDatabase,
			#"host": "localhost",
			"database": path.join(current_dir, "kiss_py_project.sqldb")#,#,
			#"user": 'postgres',
			#"password": "postgres"
		}
	}

models/models.py
===================

.. code-block:: python

	from kiss.models import Model, CharField, TextField, DateTimeField, BooleanField, ForeignKeyField
	class Blog(Model):
		creator = CharField()
		name = CharField()
	class Entry(Model):
		blog = ForeignKeyField(Blog)
		title = CharField()
		body = TextField()
		pub_date = DateTimeField()
		published = BooleanField(default=True)
	
controllers/controller2.py
==========================

.. code-block:: python

	from kiss.views.templates import TemplateResponse
	from kiss.core.events import Eventer
	from models.models import Blog, Entry
	import datetime	
	class Controller2(object):
		def get(self, request):
			#publish some event
			eventer = Eventer()
			eventer.publish("some event", self)
			if not "foo" in request.session:
				request.session["foo"] = 0
			request.session["foo"] += 1
			#blog = Blog()
			blog = Blog.get(id=1)
			blog.name = "super blog"
			blog.creator = "Stas"
			blog.save()
			#entry = Entry()
			entry = Entry.get(id=2)
			entry.blog = blog
			entry.title = "super post"
			entry.body = "lkoeirsldfkwierj"
			entry.pub_date = datetime.datetime.now()
			entry.save()
			return TemplateResponse("view.html", {
				"foo": request.session["foo"], 
				"users": [{"url": "google.com", "username": "brin"}],
				"blog": blog
			})		
		#on load handler via eventer
		def application_after_load(self, application):
			print "app loaded"
			#Blog.create_table()
			#Entry.create_table()
	
views/templates/view.html
=========================

.. code-block:: html

	<html>
		<head>
			<title>{% block title %}{% endblock %}</title>
			<script src="/scripts/j.js"></script>
		</head>
		<body>
			<div>{{foo}}</div>
			<ul>
			{% for user in users %}
			  <li><a href="{{ user.url }}">{{ user.username }}</a></li>
			{% endfor %}
			</ul>
		</body>
	</html>
