import werkzeug.wrappers
from werkzeug.utils import cached_property
from werkzeug.utils import redirect
import json


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
	def __init__(self, js, **argw):
		js = json.dumps(js)
		super(JsonResponse, self).__init__(js, mimetype="application/json", **argw)
