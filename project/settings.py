from controllers.controller1 import Controller1
from controllers.controller2 import Controller2
from kiss.core.application import Event
from kiss.models.adapters.postgresql import PostgresqlDatabase


controller1 = Controller1()
controller2 = Controller2()
options = {
	"application": {
		"address": "127.0.0.1",
		"port": 8080
	},
	"urls": {
		"": controller1,
		"users": {
			"(?P<user>\w+)": controller2
		},
		"2": {
			"3": controller1,
			"4": controller2
		}
	},
	"views": {
		"templates_path": "views.templates",
		"static_path": "views.static"
	},
	"events": {
		Event.APPLICATION_AFTER_LOAD: [controller2.application_after_load]
	},
	"models": {
		"engine": PostgresqlDatabase,
		"host": "localhost",
		"database": 'test',
		"user": 'postgres',
		"password": "postgres"
	}
}

