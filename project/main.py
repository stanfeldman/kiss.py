import sys
sys.path.append("..")
from kiss.core.application import Application
from kiss.controllers.http import Response
import time

class Controller1(object):
	def get(self, request):
		return Response("<h1>hello first response!</h1>")
		
class Controller2(object):
	def get(self, request):
		#time.sleep(3)
		return Response("<h1>hello second response</h1>")

options = {
	"application": {
		"address": "127.0.0.1",
		"port": 8080
	},
	"urls": {
		"": Controller1(),
		"2": {
			"3": Controller2(),
			"4": Controller2()
		}
	}
}
app = Application(options)
app.start()
