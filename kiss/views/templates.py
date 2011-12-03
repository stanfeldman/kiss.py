from kiss.views.base import Response
from kiss.core.application import Application


class TemplateResponse(Response):
	def __init__(self, path, context={}, **argw):
		self.application = Application()
		self.template = self.application.options["views"]["templates_path"].get_template(path)
		self.context = context
		super(TemplateResponse, self).__init__(self.template.render(self.context).encode("utf-8"), **argw)
		print self
