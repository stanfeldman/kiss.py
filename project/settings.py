from controllers.controller1 import Controller1
from controllers.controller2 import Controller2
from kiss.core.application import Event
from kiss.models import SqliteDatabase
from kiss.core.exceptions import InternalServerError


options = {
	"application": {
		"address": "127.0.0.1",
		"port": 8080
	},
	"urls": {
		"": Controller1,
		"users": {
			"(?P<user>\w+)": Controller2
		},
		"2": {
			"3": Controller1,
			"4": Controller2
		}
	},
	"views": {
		"templates_path": "views.templates",
		"static_path": "views.static"
	},
	"events": {
		Event.ApplicationAfterLoad: Controller2.application_after_load,
		InternalServerError.code: Controller2.internal_server_error
	},
	"models": {
		"engine": SqliteDatabase,
		#"host": "localhost",
		"database": 'test'#,
		#"user": 'postgres',
		#"password": "postgres"
	}
}

