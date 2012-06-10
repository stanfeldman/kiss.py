from kiss.views.core import Response
from kiss.core.application import Application


class Template(object):
	@staticmethod
	def text_by_path(path, context={}):
		return Application().options["views"]["templates_path"].get_template(path).render(context).encode("utf-8")
		
	@staticmethod
	def text_by_text(text, context={}):
		return Application().options["views"]["templates_path"].from_string(text).render(context).encode("utf-8")
		

class TemplateResponse(Response):
	"""
	Template response via Jinja2. Pass template path and context.
	"""
	def __init__(self, path, context={}, **argw):
		super(TemplateResponse, self).__init__(Template.text_by_path(path, context), **argw)
		
				
class TextResponse(Response):
	def __init__(self, text, context={}, **argw):
		super(TextResponse, self).__init__(Template.text_by_text(text, context), **argw)
