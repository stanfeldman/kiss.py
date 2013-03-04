import werkzeug.wrappers
from werkzeug.exceptions import *
from werkzeug.utils import cached_property
from werkzeug.utils import redirect
import jsonpickle
from putils.patterns import Singleton
from putils.dynamics import Importer
from jinja2 import Environment, PackageLoader, PrefixLoader, FileSystemLoader, ChoiceLoader
import gettext


class Templater(Singleton):
	def __init__(self, app):
		self.app = app
		self.options = app.options
		if "templates_path" in self.options["views"]:
			self.add_template_paths(self.options["views"]["templates_path"])
			if "translations" in self.options["views"]:
				self.add_translation_paths(self.options["views"]["translations"])
			
	def add_template_paths(self, paths, prefix=""):
		tps = []
		for tp in paths:
			loader = None
			try:
				if Importer.module_path(tp): #if it module path
					loader = PackageLoader(tp, "")
			except:
				loader = FileSystemLoader(tp)
			if loader:
				if prefix:
					tps.append(PrefixLoader({prefix: loader}))
				else:
					tps.append(loader)
		if hasattr(self.app, "templates_environment"):
			for tl in tps:
				self.app.templates_environment.loader.loaders.append(tl)
		else:
			self.app.templates_environment = Environment(loader=ChoiceLoader(tps), extensions=self.options["views"]["templates_extensions"])
			
	def add_translation_paths(self, paths):
		if not paths:
			return
		for tr_path in paths:
			try:
				tr_path = Importer.module_path(tr_path)
			except:
				pass
			try:
				self.app.templates_environment.install_gettext_translations(gettext.translation("messages", tr_path, codeset="UTF-8"))
				gettext.install("messages", tr_path, codeset="UTF-8")
			except:
				pass


class Request(werkzeug.wrappers.Request):
	"""
	Base request object inhereted from werkzeug Request.
	Added session object.
	"""
	def __init__(self, options, **argw):
		super(Request, self).__init__(options, **argw)
	
	@cached_property
	def session(self):
		return self.environ["session"]


class Response(werkzeug.wrappers.Response):
	"""
	Base response object inhereted from werkzeug Response.
	Text/html mimetype is default.
	"""
	def __init__(self, text, **argw):
		if "mimetype" not in argw:
			argw["mimetype"] = "text/html"
		super(Response, self).__init__(text, **argw)


class RedirectResponse(werkzeug.wrappers.Response):
	"""
	Response for redirect. Pass path and server will do 302 request.
	"""
	def __new__(cls, path):
		return redirect(path)
		
		
class JsonResponse(Response):
	"""
	Json response. Pass any object you want, JsonResponse converts it to json.
	"""
	def __init__(self, inp, **argw):
		inp = self.fix_attributes(inp)
		json_str = jsonpickle.encode(inp, unpicklable=False)
		super(JsonResponse, self).__init__(json_str, mimetype="application/json", **argw)
		
	def fix_attributes(self, inp):
		if isinstance(inp, SelectQuery) or (isinstance(inp, list)):
			inp = [self.fix_attributes(x) for x in list(inp)]
		elif isinstance(inp, Model):
			inp = self.fix_attributes_obj(inp)
		return inp
	
	def fix_attributes_obj(self, obj):
		new_dict = {}
		for key,value in obj.__dict__.items():
			value = self.fix_attributes(value)
			if key[:2] == "__":
				new_dict[key[2:]] = value
			elif key[:7] == "_cache_":
				new_dict[key[7:]] = value
			else:
				new_dict[key] = value
		obj.__dict__ = new_dict
		return obj
