from gevent import monkey; monkey.patch_all()
from gevent.wsgi import WSGIServer
import sys
from helper import Helper
from kiss.controllers.router import Router

class Application(object):
	def __init__(self, options):
		self.options = options
		self.options["urls"] = Helper.flat(self.options["urls"])
		self.router = Router(self.options["urls"])
			
	def on_request(self, options, start_response):
		response = self.router.route(options)
		start_response(response.status, response.headers)
		return [response.result]
	
	def start(self):
		WSGIServer((self.options["application"]["address"], self.options["application"]["port"]), self.on_request).serve_forever()
		
	def stop(self):
		server.stop()
		
if __name__ == "__main__":
	app = Application()
	app.start()
