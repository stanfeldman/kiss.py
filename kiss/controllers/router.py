import os
from jinja2 import Environment, PackageLoader

class Request(object):
	pass
	
class Response(object):
	def __init__(self, result="not found", status="404 OK", headers=[("Content-Type", "text/html")]):
		self.result = result
		self.status = status
		self.headers = headers

class Router(object):
	def __init__(self, options):
		self.options = options
		self.options["views"]["templates_path"] = Environment(loader=PackageLoader(self.options["views"]["templates_path"], ""))
		
	def route(self, options):
		#print options
		request = Request()
		response = Response()
		request.path = options['PATH_INFO']
		request.method = options["REQUEST_METHOD"].lower()
		request.query = options["QUERY_STRING"]
		request.address = options["REMOTE_ADDR"]
		request.port = options["SERVER_PORT"]
		if request.path in self.options["urls"]:
			controller = self.options["urls"][request.path]
			action = getattr(controller, request.method)
			response = action(request)
		return response
		
