import sys
sys.path.append("..")
from kiss.application import Application

options = {
	"application": {
		"address": "127.0.0.1",
		"port": 8080
	},
	"urls": {
		"/": 1,
		"/2": 2
	}
}
app = Application(options)
app.start()
