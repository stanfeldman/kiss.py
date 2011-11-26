from controllers.controller1 import Controller1
from controllers.controller2 import Controller2

options = {
	"application": {
		"address": "127.0.0.1",
		"port": 8080
	},
	"urls": {
		"": Controller1(),
		"users": {
			"(?P<user>\w+)": Controller2()
		},
		"2": {
			"3": Controller1(),
			"4": Controller2()
		}
	},
	"views": {
		"templates_path": "views.templates"
	}
}

