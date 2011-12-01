from kiss.views.templates import TemplateResponse
from kiss.core.events import Eventer
		
class Controller2(object):
	def get(self, request):
		#publish some event
		eventer = Eventer()
		eventer.publish("some event", self)
		if not "foo" in request.session:
			request.session["foo"] = 0
		request.session["foo"] += 1
		return TemplateResponse("view.html", {"foo": request.session["foo"], "users": [{"url": "google.com", "username": "brin"}]})
		
	#on load handler via eventer
	def application_after_load(self, application):
		print application.options
