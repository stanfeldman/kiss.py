from putils.patterns import Singleton
from kiss.views.core import Response
from werkzeug.exceptions import MethodNotAllowed


class Controller(object):
	"""
	Base class of all controllers.
	"""
	def get(self, request):
		raise MethodNotAllowed()
		
	def post(self, request):
		raise MethodNotAllowed()
		
	def put(self, request):
		raise MethodNotAllowed()
		
	def delete(self, request):
		raise MethodNotAllowed()


