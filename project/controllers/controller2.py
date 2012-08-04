from kiss.views.templates import TemplateResponse
from kiss.views.core import Response
from kiss.core.events import Eventer
from models.models import Blog, Entry
import datetime
from kiss.controllers.core import Controller
from kiss.models import setup_all, drop_all, create_all, session

	
class Controller2(Controller):
	def get(self, request):
		#publish some event
		eventer = Eventer()
		eventer.publish("some event", self)
		if not "foo" in request.session:
			request.session["foo"] = 0
		request.session["foo"] += 1
		blog = Blog(name="super blog", creator="Stas")
		if not Entry.get_by(title="super post"):
			entry = Entry(title="super post", body="saifjo", blog=blog)
		session.commit()
		print Entry.query.all()
		return TemplateResponse("view.html", {
			"foo": request.session["foo"], 
			"users": [{"url": "google.com", "username": "brin"}],
			"blog": blog
		})
		
	#on load handler via eventer
	def application_after_load(self, application):
		setup_all()
		drop_all()
		create_all()
		print "app loaded"
		
	def internal_server_error(self, request):
		return Response("<h1>error: %s</h1>" % request.description)
