# Web framework on Gevent and Python

Object-oriented web framework on Gevent and Python.

# Usage

* main.py
	<pre>
	import sys
	sys.path.append("..")
	from kiss.core.application import Application
	from settings import options
	app = Application(options)
	app.start()
	</pre>
* settings.py
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
* controllers/controller1.py
	<pre>
	from kiss.views.templates import TemplateResponse
	import time
	class Controller2(object):
		def get(self, request):
			return TemplateResponse("view.html", {"users": [{"url": "google.com", "username": "brin"}]})
	</pre>
* view.html
	Kiss.py uses Django-like templates from Jinja1. See project folder.
