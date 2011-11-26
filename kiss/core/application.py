from gevent import monkey; monkey.patch_all()
from gevent.wsgi import WSGIServer
import sys
from helper import Singleton
from kiss.controllers.router import Router
from beaker.middleware import SessionMiddleware

class Application(object):
	__metaclass__ = Singleton
	
	def __init__(self, options):
		self.options = options
		self.router = Router(self.options)
			
	def on_request(self, options, start_response):
		response = self.router.route(options)
		start_response(response.status, response.headers)
		return [response.result]
	
	def start(self):
		session_options = {
			'session.type': "cookie",
			"session.auto": True,
			'session.cookie_expires': True,
			'session.encrypt_key':'sldk24j0jf09w0jfg24',
			'session.validate_key':';l[pfghopkqeq1234,fs'
		}
		self.session_middleware = SessionMiddleware(self.on_request, session_options, environ_key="session")
		self.server = WSGIServer((self.options["application"]["address"], self.options["application"]["port"]), self.session_middleware)
		self.server.serve_forever()
		
	def stop(self):
		self.server.stop()
		
	@staticmethod
	def options():
		return self.options
		
if __name__ == "__main__":
	app = Application()
	app.start()
