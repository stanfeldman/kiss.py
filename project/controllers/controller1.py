from kiss.controllers.router import Response

class Controller1(object):
	def get(self, request):
		return Response("<h1>hello first response!</h1>")
		
