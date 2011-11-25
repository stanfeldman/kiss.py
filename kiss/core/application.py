from gevent import monkey; monkey.patch_all()
from gevent.wsgi import WSGIServer
import sys
from helper import Helper, Singleton
from kiss.controllers.router import Router

class Application(object):
	__metaclass__ = Singleton
	
	def __init__(self, options):
		self.options = options
		self.options["urls"] = Helper.flat(self.options["urls"])
		self.router = Router(self.options)
			
	def on_request(self, options, start_response):
		response = self.router.route(options)
		start_response(response.status, response.headers)
		return [response.result]
	
	def start(self):
		WSGIServer((self.options["application"]["address"], self.options["application"]["port"]), self.on_request).serve_forever()
		
	def stop(self):
		server.stop()
		
	@staticmethod
	def options():
		return self.options
		
if __name__ == "__main__":
	app = Application()
	app.start()
