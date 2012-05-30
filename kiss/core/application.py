from gevent import monkey; monkey.patch_all()
from gevent.wsgi import WSGIServer
from putils.patterns import Singleton
from putils.dynamics import Importer
from putils.types import Dict
from kiss.controllers.router import Router
from kiss.views.core import Request, Response
from beaker.middleware import SessionMiddleware
from werkzeug.wsgi import SharedDataMiddleware
from kiss.core.events import Eventer, Event
from kiss.views.static import StaticBuilder
from kiss.models import Model
import logging


class Application(Singleton):
	
	def __init__(self, options):
		logging.basicConfig(level=logging.CRITICAL)
		self.options = {
			"application": {
				"address": "127.0.0.1",
				"port": 8080
			},
			"views": {
				"templates_path": "views.templates",
				"static_path": "views.static",
				'session_type': "cookie",
				"session_auto": True,
				'session_cookie_expires': True,
				'session_encrypt_key':'sldk24j0jf09w0jfg24',
				'session_validate_key':';l[pfghopkqeq1234,fs'
			},
			"events": {}
		}
		self.options = Dict.merge(self.options, options)
		self.eventer = Eventer(self.options["events"])
		self.router = Router(self.options)
		self.static_builder = None
		if "static_path" in self.options["views"]:
			try:
				self.options["views"]["static_path"] = Importer.module_path(self.options["views"]["static_path"])
			except:
				pass
			if self.options["views"]["static_path"]:
				self.static_builder = StaticBuilder(self.options["views"]["static_path"])
		if "models" in self.options:
			db_engine = self.options["models"].pop("engine")
			db_name = self.options["models"].pop("database")
			self.db_engine = db_engine(db_name, **self.options["models"])
			self.db_engine.connect()
			for m in Model.__subclasses__():
				m._meta.database = self.db_engine
			
	def __del__(self):
		self.db_engine.close()
			
	def wsgi_app(self, options, start_response):
		request = Request(options)
		response = self.router.route(request)
		return response(options, start_response)
	
	def start(self):
		session_options = {
			'session.type': self.options["views"]['session_type'],
			"session.auto": self.options["views"]["session_auto"],
			'session.cookie_expires': self.options["views"]['session_cookie_expires'],
			'session.encrypt_key': self.options["views"]['session_encrypt_key'],
			'session.validate_key': self.options["views"]['session_validate_key']
		}
		if self.static_builder:
			self.static_builder.build()
			self.wsgi_app = SharedDataMiddleware(self.wsgi_app, {'/': self.options["views"]["static_path"] + "/build"})
		self.wsgi_app = SessionMiddleware(self.wsgi_app, session_options, environ_key="session")
		kwargs = dict(filter(lambda item: item[0] not in ["address", "port"], self.options["application"].iteritems()))
		self.server = WSGIServer((self.options["application"]["address"], self.options["application"]["port"]), self.wsgi_app, **kwargs)
		self.eventer.publish(Event.ApplicationStarted, self)
		self.server.serve_forever()
		
	def stop(self):
		self.eventer.publish(Event.ApplicationStopped, self)
		self.server.stop()

