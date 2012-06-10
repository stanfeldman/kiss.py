# MVC web framework in Python with Gevent, Jinja2, Werkzeug

# Usage

	Break your app to views, controllers and models.
	Kiss.py uses Django-like templates from Jinja2.
	You can add your static path in settings and all css and javascript files will be minified.
	Also html templates will be minified.
	In css files you can use SCSS syntax.
	Controller is class inherited from class Controller and may have methods get, post, put, delete.
	These methods get Request object param and return Response object.
	Request and Response objects inherited from Werkzeug.
	There is ORM with PostgreSQL, MySQL and SQLite(Peewee).
	Models consist of fields(class variables inherited from Field class).
	There is event dispatcher named Eventer. You can subscribe to event
	or publish event.

# main.py

	from kiss.core.application import Application
	from settings import options
	app = Application(options)
	app.start()

# settings.py

	from controllers.controller1 import Controller1
	from controllers.controller2 import Controller2
	from kiss.core.events import ApplicationStarted
	from kiss.models import PostgresqlDatabase
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
			ApplicationStarted: [Controller2.application_after_load]
		},
		"models": {
			"engine": PostgresqlDatabase,
			"host": "localhost",
			"database": 'test',
			"user": 'postgres',
			"password": "postgres"
		}
	}
	
# models/models.py

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

# controllers/controller1.py

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

# views/templates/view.html
	
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
	
# License

	This software is licensed under the BSD License. See the license file in the top distribution directory for the full license text.
