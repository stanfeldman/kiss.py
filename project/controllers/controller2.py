from kiss.views.templates import TemplateResponse
import time
		
class Controller2(object):
	def get(self, request):
		#time.sleep(3)
		return TemplateResponse("view.html", {"users": [{"url": "google.com", "username": "brin"}]})
