from gevent import monkey; monkey.patch_all()
from gevent.wsgi import WSGIServer
from helper import Singleton
from kiss.controllers.router import Router
from kiss.views.base import Request, Response
from beaker.middleware import SessionMiddleware

class Application(object):
	__metaclass__ = Singleton
	
	def __init__(self, options):
		self.options = options
		self.router = Router(self.options)
			
	def on_request(self, options, start_response):
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
		self.session_middleware = SessionMiddleware(self.on_request, session_options, environ_key="session")
		self.server = WSGIServer((self.options["application"]["address"], self.options["application"]["port"]), self.session_middleware)
		self.server.serve_forever()
		
	def stop(self):
		self.server.stop()
		
if __name__ == "__main__":
	app = Application()
	app.start()
