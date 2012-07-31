import gevent
import signal
from gevent import monkey; monkey.patch_all()
from gevent.wsgi import WSGIServer
from putils.patterns import Singleton
from putils.dynamics import Importer
from putils.types import Dict
from kiss.controllers.router import Router
from kiss.views.core import Request, Response
from beaker.middleware import SessionMiddleware
from werkzeug.wsgi import SharedDataMiddleware
from kiss.core.events import Eventer, ApplicationStarted, ApplicationStopped
from kiss.views.static import StaticBuilder
from kiss.models import Model
import logging


class Application(Singleton):
	"""
	Main class of your application.
	Pass options to constructor and all subsystems(eventer, router, db_engine) will be configured.
	"""
	def __init__(self, options):
		self.options = Application.init_options(options)
		self.options, self.eventer = Application.init_eventer(options)
		self.options, self.router = Application.init_router(options)
		self.options, self.db_engine = Application.init_db(self.options)
		self.options, self.static_builder = Application.init_static(self.options)
		self.options, self.wsgi_app = Application.init_session(self.options, self.wsgi_app)
		self.options, self.wsgi_app = Application.init_static_server(self.options, self.wsgi_app)
		self.options, self.server = Application.init_server(self.options, self.wsgi_app)
	
	@staticmethod	
	def init_options(options):
		logging.basicConfig(level=logging.CRITICAL)
		default_options = {
			"application": {
				"address": "127.0.0.1",
				"port": 8080
			},
			"views": {
				"templates_path": "views.templates",
				"templates_extensions": ["compressinja.html.HtmlCompressor"],
				"static_path": "views.static",
				'session_type': "cookie",
				"session_auto": True,
				'session_cookie_expires': True,
				'session_encrypt_key':'sldk24j0jf09w0jfg24',
				'session_validate_key':';l[pfghopkqeq1234,fs'
			},
			"events": {}
		}
		return Dict.merge(default_options, options)
		
	@staticmethod	
	def init_eventer(options):
		return (options, Eventer(options["events"]))
		
	@staticmethod	
	def init_router(options):
		return (options, Router(options))
		
	@staticmethod
	def init_static(options):
		static_builder = None
		if "static_path" not in options["views"]:
			return (options, static_builder)
		try:
			options["views"]["static_path"] = Importer.module_path(options["views"]["static_path"])
		except:
			pass
		if options["views"]["static_path"]:
			static_builder = StaticBuilder(options["views"]["static_path"])
			static_builder.build()
		return (options, static_builder)
	
	@staticmethod			
	def init_db(options):
		if "models" not in options:
			return (options, None)
		db_engine_class = options["models"].pop("engine")
		db_name = options["models"].pop("database")
		db_engine = db_engine_class(db_name, **options["models"])
		db_engine.connect()
		db_engine.set_autocommit(True)
		for m in Model.__subclasses__():
			m._meta.database = db_engine
		return (options, db_engine)
		
	@staticmethod
	def init_session(options, wsgi_app):
		session_options = {
			'session.type': options["views"]['session_type'],
			"session.auto": options["views"]["session_auto"],
			'session.cookie_expires': options["views"]['session_cookie_expires'],
			'session.encrypt_key': options["views"]['session_encrypt_key'],
			'session.validate_key': options["views"]['session_validate_key']
		}
		return (options, SessionMiddleware(wsgi_app, session_options, environ_key="session"))
		
	@staticmethod
	def init_static_server(options, wsgi_app):
		if "static_path" not in options["views"]:
			return (options, wsgi_app)
		else:
			return (options, SharedDataMiddleware(wsgi_app, {'/': options["views"]["static_path"] + "/build"}))
			
	@staticmethod
	def init_server(options, wsgi_app):
		kwargs = dict(filter(lambda item: item[0] not in ["address", "port"], options["application"].iteritems()))
		return (options, WSGIServer((options["application"]["address"], options["application"]["port"]), wsgi_app, **kwargs))
			
	def __del__(self):
		if self.db_engine:
			self.db_engine.close()
			
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

