import werkzeug.wrappers
from werkzeug.utils import cached_property
from werkzeug.utils import redirect
import jsonpickle
from peewee import Model, SelectQuery


class Request(werkzeug.wrappers.Request):
	def __init__(self, options, **argw):
		super(Request, self).__init__(options, **argw)
	
	@cached_property
	def session(self):
		return self.environ["session"]


class Response(werkzeug.wrappers.Response):
	def __init__(self, text, **argw):
		if "mimetype" not in argw:
			argw["mimetype"] = "text/html"
		super(Response, self).__init__(text, **argw)


class RedirectResponse(werkzeug.wrappers.Response):
	def __new__(cls, path):
		return redirect(path)
		
		
class JsonResponse(Response):
	def __init__(self, inp, **argw):
		if isinstance(inp, SelectQuery):
			inp = self.fix_peewee_list(list(inp))
		elif isinstance(inp, list) and len(inp) > 0:
			if isinstance(inp[0], Model):
				inp = self.fix_peewee_list(inp)
		elif isinstance(inp, Model):
			inp = self.fix_peewee_obj(inp)
		json_str = jsonpickle.encode(inp, unpicklable=False)
		super(JsonResponse, self).__init__(json_str, mimetype="application/json", **argw)
		
	def fix_peewee_list(self, l):
		return [self.fix_peewee_obj(x) for x in l]
	
	def fix_peewee_obj(self, obj):
		new_dict = {}
		for key,value in obj.__dict__.items():
			new_dict[key[2:]] = value
		obj.__dict__ = new_dict
		return obj
