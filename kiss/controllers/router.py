from jinja2 import Environment, PackageLoader, ChoiceLoader
import re
from kiss.controllers.core import Controller
from putils.patterns import Singleton
from putils.types import Dict
from kiss.core.exceptions import *
from kiss.core.events import Eventer
import traceback
import events
import inspect


class Router(Singleton):
	"""
	Router implements unique hierarhical url mapping.
	Pass dictionary with mapping of regex and controller.
	"""
	def __init__(self, options):
		self.options = options
		self.eventer = Eventer()
		self.add_urls(self.options["urls"], False)
		if "templates_path" in self.options["views"]:
			tps = []
			if isinstance(self.options["views"]["templates_path"], list):
				for tp in self.options["views"]["templates_path"]:
					tps.append(PackageLoader(tp, ""))
			else:
				tps.append(PackageLoader(self.options["views"]["templates_path"], ""))
			self.options["views"]["templates_environment"] = Environment(loader=ChoiceLoader(tps), extensions=self.options["views"]["templates_extensions"])
			
	def add_urls(self, urls, merge=True):
		urls = Dict.flat_dict(urls)
		new_urls = []
		for k, v in urls.iteritems():
			if k[len(k)-2] == "/":
				k = k[:len(k)-2] + k[len(k)-1]
			k = re.compile(k)
			if inspect.isclass(v):
				new_urls.append((k, v()))
			else:
				new_urls.append((k,v))
		if merge:
			self.options["urls"] = self.options["urls"] + new_urls
		else:
			self.options["urls"] = new_urls
		
	def route(self, request):
		for (re_url, controller) in self.options["urls"]:
			path = request.path.lower()
			if path[len(path)-1] == "/":
				path = path.rstrip('/')
			mtch = re_url.match(path)
			if mtch:
				request.params = mtch.groupdict()
				try:
					self.eventer.publish(events.BeforeControllerAction, request)
					action = getattr(controller, request.method.lower())
					response = action(request)
					self.eventer.publish(events.AfterControllerAction, request, response)
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
		
