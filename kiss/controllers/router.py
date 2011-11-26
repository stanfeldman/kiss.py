import os
from jinja2 import Environment, PackageLoader
from kiss.core.helper import Helper
import re

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
		self.options["urls"] = Helper.flat_dict(self.options["urls"])
		#print self.options["urls"]
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
		request.session = options["session"]
		for re_url, controller in self.options["urls"].iteritems():
			match = re.match(re_url, request.path)
			if match:
				request.params = match.groupdict()
				#controller = self.options["urls"][request.path]
				action = getattr(controller, request.method)
				response = action(request)
				break
		return response
		
