from jinja2 import Environment, PackageLoader
from re import match
from kiss.controllers.core import Controller
from putils.patterns import Singleton
from putils.types import Dict


class Router(Singleton):
	
	def __init__(self, options):
		self.options = options
		urls = Dict.flat_dict(self.options["urls"])
		for k, v in urls.iteritems():
			if issubclass(v, Controller):
				urls[k] = v()
		self.options["urls"] = urls
		self.options["views"]["templates_path"] = Environment(loader=PackageLoader(self.options["views"]["templates_path"], ""), extensions=['compressinja.html.HtmlCompressor'])
		
	def route(self, request):
		for re_url, controller in self.options["urls"].iteritems():
			path = request.path.lower()
			mtch = match(re_url, request.path)
			if mtch:
				print request.path
				request.params = mtch.groupdict()
				action = getattr(controller, request.method.lower())
				response = action(request)
				return response
		
