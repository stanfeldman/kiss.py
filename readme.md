# Web framework on Gevent and Python

# Usage

Break your app to views, controllers and models(not supported now).
Kiss.py uses Django-like templates from Jinja2.
Controller is object from class with methods get, post, put, delete.
These methods get Request object param and return Response object.
Request and Response objects inherited from Werkzeug.
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
	from kiss.core.application import Event
	options = {
		"application": {
			"address": "127.0.0.1",
			"port": 8080
		},
		"urls": {
			"": Controller1(),
			"2": {
				"3": Controller1(),
				"4": Controller2()
			}
		},
		"views": {
			"templates_path": "views.templates",
			"static_path": "views.static"
		},
		"events": {
			Event.APPLICATION_AFTER_LOAD: [controller2.application_after_load]
		}
	}

# controllers/controller1.py

	from kiss.views.templates import TemplateResponse
	from kiss.core.events import Eventer
	class Controller2(object):
		def get(self, request):
			#publish some event
			eventer = Eventer()
			eventer.publish("some event", self)
			if not "foo" in request.session:
				request.session["foo"] = 0
			request.session["foo"] += 1
			return TemplateResponse("view.html", {"foo": request.session["foo"], "users": [{"url": "google.com", "username": "brin"}]})
		
		#on load handler via eventer
		def application_after_load(self, application):
			print application.options

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
