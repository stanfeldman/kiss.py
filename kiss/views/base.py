import werkzeug.wrappers
from werkzeug.utils import cached_property
from werkzeug.utils import redirect


class Request(werkzeug.wrappers.Request):
	def __init__(self, options, **argw):
		super(Request, self).__init__(options, **argw)
	
	@cached_property
	def session(self):
		return self.environ["session"]


class Response(werkzeug.wrappers.Response):
	def __init__(self, text, **argw):
		super(Response, self).__init__(text, mimetype="text/html", **argw)
	
	@staticmethod	
	def redirect(path):
		return redirect(path)
