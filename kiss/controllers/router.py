from jinja2 import Environment, PackageLoader
import re
from kiss.controllers.core import Controller
from putils.patterns import Singleton
from putils.types import Dict
from kiss.core.exceptions import *
from kiss.core.events import Eventer


class Router(Singleton):
	def __init__(self, options):
		self.options = options
		self.eventer = Eventer()
		urls = Dict.flat_dict(self.options["urls"])
		new_urls = {}
		for k, v in urls.iteritems():
			if issubclass(v, Controller):
				if k[len(k)-1] == "/":
					k = k.rstrip('/')
				k = re.compile(k)
				new_urls[k] = v()
		self.options["urls"] = new_urls
		self.options["views"]["templates_path"] = Environment(loader=PackageLoader(self.options["views"]["templates_path"], ""), extensions=['compressinja.html.HtmlCompressor'])
		
	def route(self, request):
		eventer = Eventer()
		for re_url, controller in self.options["urls"].iteritems():
			path = request.path.lower()
			if path[len(path)-1] == "/":
				path = path.rstrip('/')
			mtch = re_url.match(path)
			if mtch:
				request.params = mtch.groupdict()
				try:
					action = getattr(controller, request.method.lower())
					response = action(request)
					return response
				except HTTPException, e:
					return self.get_err_page(e, request)
				except Exception, e:
					return self.get_err_page(InternalServerError(), request)
		return self.get_err_page(NotFound(), request)
		
	def get_err_page(self, err, request):
		err_page = self.eventer.publish_and_get_result(err.code, request)
		if err_page:
			return err_page
		return err
		
