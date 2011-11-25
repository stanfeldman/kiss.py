class Request(object):
	pass
	
class Response(object):
	def __init__(self, result="not found", status="404 OK", headers=[("Content-Type", "text/html")]):
		self.result = result
		self.status = status
		self.headers = headers
