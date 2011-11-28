import os
from jinja2 import Environment, PackageLoader
from kiss.core.helper import Helper, Singleton
import re
import werkzeug.wrappers
from werkzeug.utils import cached_property

class Request(werkzeug.wrappers.Request):
	def __init__(self, options):
		super(Request, self).__init__(options)
	
	@cached_property
	def session(self):
		return self.environ["session"]
	
class Response(werkzeug.wrappers.Response):
	def __init__(self, text):
		super(Response, self).__init__(text)
		self.headers['content-type'] = 'text/html; charset=utf-8'

class Router(object):
	__metaclass__ = Singleton
	
	def __init__(self, options):
		self.options = options
		self.options["urls"] = Helper.flat_dict(self.options["urls"])
		self.options["views"]["templates_path"] = Environment(loader=PackageLoader(self.options["views"]["templates_path"], ""))
		
	def route(self, request):
		for re_url, controller in self.options["urls"].iteritems():
			path = request.path.lower()
			match = re.match(re_url, request.path)
			if match:
				print request.path
				request.params = match.groupdict()
				action = getattr(controller, request.method.lower())
				response = action(request)
				return response
		
