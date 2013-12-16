from jinja2 import Environment, PackageLoader, ChoiceLoader
import re
from kiss.controllers.core import Controller
from putils.patterns import Singleton
from putils.types import Dict
from kiss.views.core import *
from kiss.core.events import Eventer
import traceback
import inspect
import logging


class Router(Singleton):
	"""
	Router implements unique hierarchical url mapping.
	Pass dictionary with mapping of regex and controller.
	"""
	def __init__(self, options):
		self.options = options
		self.logger = logging.getLogger(__name__)
		self.eventer = Eventer()
		self.add_urls(self.options["urls"], False)
		if "templates_path" in self.options["views"]:
			tps = []
			for tp in self.options["views"]["templates_path"]:
				tps.append(PackageLoader(tp, ""))
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
					self.eventer.publish("BeforeControllerAction", request)
					#check if controller has method for all requests
					if hasattr(controller, "process") and inspect.ismethod(getattr(controller, "process")):
						action = getattr(controller, "process")
					else:
						action = getattr(controller, request.method.lower())
					response = action(request)
					self.eventer.publish("AfterControllerAction", request, response)
					if not response:
						break
					log_code = 0
					if hasattr(response, "status_code"):
						log_code = response.status_code
					else:
						log_code = response.code
					self.logger.info(Router.format_log(request, log_code))
					return response
				except HTTPException, e:
					response = self.get_err_page(e)
					self.logger.warning(Router.format_log(request, response.code, str(e)), exc_info=True)
					return response
				except Exception, e:
					response = self.get_err_page(InternalServerError(description=traceback.format_exc()))
					self.logger.error(Router.format_log(request, response.code, str(e)), exc_info=True)
					return response
		response = self.get_err_page(NotFound(description="Not found %s" % request.url))
		self.logger.warning(Router.format_log(request, response.code))
		return response
		
	def get_err_page(self, err):
		err_page = self.eventer.publish_and_get_result(err.code, err)
		if err_page:
			return err_page
		return err

	@staticmethod
	def format_log(request, status_code, msg=None):
		addr = request.remote_addr
		provided_ips = request.access_route
		if provided_ips and len(provided_ips) > 0:
			addr = provided_ips[0]
		result = '%d %s %s <- %s %s' % (status_code, request.method, request.url, addr, request.headers['User-Agent'])
		if msg:
			result = "%s %s" % (msg, result)
		return result
