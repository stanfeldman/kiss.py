from http import Request, Response

class Router(object):
	def __init__(self, mapping):
		self.mapping = mapping
		
	def route(self, options):
		#print options
		request = Request()
		response = Response()
		request.path = options['PATH_INFO']
		request.method = options["REQUEST_METHOD"].lower()
		print request.method
		if request.path in self.mapping:
			controller = self.mapping[request.path]
			action = getattr(controller, request.method)
			response = action(request)
		return response
		
