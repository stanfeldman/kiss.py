from kiss.controllers.router import Response
from kiss.core.application import Application

class TemplateResponse(Response):
	def __init__(self, path, context):
		super(TemplateResponse, self).__init__()
		self.application = Application()
		self.template = self.application.options["views"]["templates_path"].get_template(path)
		self.context = context
		self.result = self.template.render(self.context).encode("utf-8")
