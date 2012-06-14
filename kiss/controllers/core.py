from putils.patterns import Singleton
from kiss.views.core import Response


class Controller(object):
	"""
	Base class of all controllers.
	"""
	def get(self, request):
		return Response("Method is not supported", status=405)
		
	def post(self, request):
		return Response("Method is not supported", status=405)
		
	def put(self, request):
		return Response("Method is not supported", status=405)
		
	def delete(self, request):
		return Response("Method is not supported", status=405)


