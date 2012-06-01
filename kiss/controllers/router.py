from jinja2 import Environment, PackageLoader
import re
from kiss.controllers.core import Controller
from putils.patterns import Singleton
from putils.types import Dict
from kiss.core.exceptions import *
from kiss.core.events import Eventer
import traceback


class Router(Singleton):
	def __init__(self, options):
		self.options = options
		self.eventer = Eventer()
		urls = Dict.flat_dict(self.options["urls"])
		new_urls = {}
		for k, v in urls.iteritems():
			if k[len(k)-2] == "/":
				k = k[:len(k)-2] + k[len(k)-1]
			k = re.compile(k)
			new_urls[k] = v()
		self.options["urls"] = new_urls
		if "templates_path" in self.options["views"]:
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
					if not response:
						break
					return response
				except HTTPException, e:
					return self.get_err_page(e)
				except Exception, e:
					return self.get_err_page(InternalServerError(description=traceback.format_exc()))
		return self.get_err_page(NotFound(description="Not found %s" % request.url))
		
	def get_err_page(self, err):
		err_page = self.eventer.publish_and_get_result(err.code, err)
		if err_page:
			return err_page
		return err
		
