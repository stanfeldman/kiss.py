import gevent
import signal
from gevent import monkey; monkey.patch_all()
from gevent.wsgi import WSGIServer
from putils.patterns import Singleton
from putils.dynamics import Importer, Introspector
from putils.types import Dict
from kiss.controllers.router import Router
from kiss.views.core import Request, Response
from beaker.middleware import SessionMiddleware
from werkzeug.wsgi import SharedDataMiddleware
from kiss.core.events import *
from kiss.views.static import StaticBuilder
from kiss.views.core import Templater
from kiss.models import metadata
import logging


class Application(Singleton):
	"""
	Main class of your application.
	Pass options to constructor and all subsystems(eventer, router, db_engine) will be configured.
	"""
	def __init__(self, options):
		self.init_options(options)
		self.init_eventer()
		self.init_router()
		self.init_templater()
		self.eventer.publish(BeforeDatabaseEngineConfiguration, self)
		self.init_db()
		self.eventer.publish(AfterDatabaseEngineConfiguration, self)
		self.init_session()
		self.eventer.publish(BeforeInitStatic, self)
		self.init_static()
		self.eventer.publish(AfterInitStatic, self)
		self.eventer.publish(BeforeInitServer, self)
		self.init_server()
		self.eventer.publish(AfterInitServer, self)
		self.eventer.publish(BeforeApplicationStarted, self)
	
	def init_options(self, options):
		logging.basicConfig(level=logging.CRITICAL)
		default_options = {
			"application": {
				"address": "127.0.0.1",
				"port": 8080
			},
			"urls": {},
			"views": {
				"templates_path": [],
				"templates_extensions": ["compressinja.html.HtmlCompressor", "jinja2.ext.i18n"],
				"static_path": [],
				'session_type': "cookie",
				"session_auto": True,
				'session_cookie_expires': True,
				'session_encrypt_key':'sldk24j0jf09w0jfg24',
				'session_validate_key':';l[pfghopkqeq1234,fs'
			},
			"events": {}
		}
		self.options = Dict.merge(default_options, options)
		
	def init_eventer(self):
		self.eventer = Eventer(self.options["events"])
		
	def init_router(self):
		self.router = Router(self.options)
		
	def init_templater(self):
		self.templater = Templater(self)
		
	def init_static(self):
		static_builder = None
		self.add_static(self.options["views"]["static_path"], merge=False)
		
	def add_static(self, sps, url_path="/", merge=True):
		static_path = []
		for sp in sps:
			try:
				sp = Importer.module_path(sp)
			except:
				pass
			try:
				static_path.append(sp)
				static_builder = StaticBuilder(sp)
				static_builder.build()
				self.wsgi_app = SharedDataMiddleware(self.wsgi_app, {url_path : sp + "/build"}, cache=False)
			except:
				pass
		if merge:
			self.options["views"]["static_path"] = self.options["views"]["static_path"] + static_path
		else:
			self.options["views"]["static_path"] = static_path
			
	def init_db(self):
		if "models" in self.options:
			metadata.bind = self.options["models"]["connection"]
			metadata.bind.echo = False
		
	def init_session(self):
		session_options = {
			'session.type': self.options["views"]['session_type'],
			"session.auto": self.options["views"]["session_auto"],
			'session.cookie_expires': self.options["views"]['session_cookie_expires'],
			'session.encrypt_key': self.options["views"]['session_encrypt_key'],
			'session.validate_key': self.options["views"]['session_validate_key']
		}
		self.wsgi_app = SessionMiddleware(self.wsgi_app, session_options, environ_key="session")
		
	def init_static_server(self):
		for sp in self.options["views"]["static_path"]:
			self.wsgi_app = SharedDataMiddleware(self.wsgi_app, {'/': sp + "/build"})
			
	def init_server(self):
		kwargs = dict(filter(lambda item: item[0] not in ["address", "port"], self.options["application"].iteritems()))
		self.server = WSGIServer((self.options["application"]["address"], self.options["application"]["port"]), self.wsgi_app, **kwargs)
			
	def wsgi_app(self, options, start_response):
		request = Request(options)
		response = self.router.route(request)
		return response(options, start_response)
	
	def start(self):
		gevent.signal(signal.SIGTERM, self.stop)
		gevent.signal(signal.SIGINT, self.stop)
		self.eventer.publish(ApplicationStarted, self)
		self.server.serve_forever()
		
	def start_no_wait(self):
		self.eventer.publish(ApplicationStarted, self)
		self.server.start()
		
	def stop(self):
		self.eventer.publish(ApplicationStopped, self)
		self.server.stop()
		if self.db_engine:
			self.db_engine.close()

