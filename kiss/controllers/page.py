from core import Controller
from kiss.views.templates import TemplateResponse

class PageController(Controller):
	"""
	If you need just to show page, create PageController and pass to it your page and optional context.
	Use it like another controllers in urls settings of your app.
	"""
	def __init__(self, page, context={}):
		self.page = page
		self.context = context
		
	def get(self, request):
		self.context["request"] = request
		return TemplateResponse(self.page, self.context)
