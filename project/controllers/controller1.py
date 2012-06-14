from kiss.views.core import Response
from kiss.controllers.core import Controller


class Controller1:
	def get(self, request):
		return Response("<h1>hello first response!</h1>")
		
