from kiss.views.templates import TemplateResponse
from kiss.core.events import Eventer
from models.models import Blog, Entry
import datetime
from kiss.controllers.core import Controller
from kiss.models import Model, SqliteDatabase

	
class Controller2(Controller):
	def get(self, request):
		#publish some event
		eventer = Eventer()
		eventer.publish("some event", self)
		if not "foo" in request.session:
			request.session["foo"] = 0
		request.session["foo"] += 1
		blog = Blog()
		#blog = Blog.get(id=1)
		blog.name = "super blog"
		blog.creator = "Stas"
		blog.save()
		entry = Entry()
		#entry = Entry.get(id=2)
		entry.blog = blog
		entry.title = "super post"
		entry.body = "lkoeirsldfkwierj"
		entry.pub_date = datetime.datetime.now()
		entry.save()
		return TemplateResponse("view.html", {
			"foo": request.session["foo"], 
			"users": [{"url": "google.com", "username": "brin"}],
			"blog": blog
		})
		
	#on load handler via eventer
	def application_after_load(self, application):
		print "app loaded"
		Blog.create_table(fail_silently=True)
		Entry.create_table(fail_silently=True)
