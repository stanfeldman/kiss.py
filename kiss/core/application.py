from gevent import monkey; monkey.patch_all()
from gevent.wsgi import WSGIServer
from helpers import Singleton, Importer
from kiss.controllers.router import Router
from kiss.views.base import Request, Response
from beaker.middleware import SessionMiddleware
from werkzeug.wsgi import SharedDataMiddleware

class Application(object):
	__metaclass__ = Singleton
	
	def __init__(self, options):
		self.options = options
		self.router = Router(self.options)
			
	def wsgi_app(self, options, start_response):
		request = Request(options)
		response = self.router.route(request)
		if not response:
			response = Response("404 Not Found")
		return response(options, start_response)
	
	def start(self):
		session_options = {
			'session.type': "cookie",
			"session.auto": True,
			'session.cookie_expires': True,
			'session.encrypt_key':'sldk24j0jf09w0jfg24',
			'session.validate_key':';l[pfghopkqeq1234,fs'
		}
		if "static_path" in self.options["views"]:
			self.wsgi_app = SharedDataMiddleware(self.wsgi_app, {'/': Importer.module_path(self.options["views"]["static_path"])})
		self.wsgi_app = SessionMiddleware(self.wsgi_app, session_options, environ_key="session")
		self.server = WSGIServer((self.options["application"]["address"], self.options["application"]["port"]), self.wsgi_app)
		self.server.serve_forever()
		
	def stop(self):
		self.server.stop()
		
if __name__ == "__main__":
	app = Application()
	app.start()
