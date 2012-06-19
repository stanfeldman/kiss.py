from kiss.views.templates import TemplateResponse
from kiss.controllers.core import Controller

class AuthPageController(Controller):
	def get(self, request):
		return TemplateResponse("auth_page.html")
		

class AuthSuccessController(Controller):
	def get(self, request):
		return TemplateResponse("auth_result.html", {"result": request.args})

