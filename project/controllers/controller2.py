from kiss.views.templates import TemplateResponse
		
class Controller2(object):
	def get(self, request):
		#print request.params
		if not "foo" in request.session:
			request.session["foo"] = 0
		request.session["foo"] += 1
		return TemplateResponse("view.html", {"foo": request.session["foo"], "users": [{"url": "google.com", "username": "brin"}]})
