# Web framework on Gevent and Python

# Usage

Break your app to views, controllers and models(not supported now).

# main.py
	<pre>
	import sys
	sys.path.append("..")
	from kiss.core.application import Application
	from settings import options
	app = Application(options)
	app.start()
	</pre>
# settings.py
	<pre>
	from controllers.controller1 import Controller1
	from controllers.controller2 import Controller2
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
			"templates_path": "views.templates"
		}
	}
	</pre>
# controllers/controller1.py
	<pre>
	from kiss.views.templates import TemplateResponse
	import time
	class Controller2(object):
		if not "foo" in request.session:
			request.session["foo"] = 0
		request.session["foo"] += 1
		return TemplateResponse("view.html", {"foo": request.session["foo"], "users": [{"url": "google.com", "username": "brin"}]})
	</pre>
# views/templates/view.html
	Kiss.py uses Django-like templates from Jinja2.
	
	<html>
		<head>
			<title>{% block title %}{% endblock %}</title>
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
