from controllers.controller1 import Controller1
from controllers.controller2 import Controller2
from kiss.core.application import Event
from kiss.models.adapters.postgresql import PostgresqlEngine


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
		Event.APPLICATION_AFTER_LOAD: [Controller2.application_after_load]
	},
	"models": {
		"engine": PostgresqlEngine,
		"host": "localhost",
		"database": 'test',
		"user": 'postgres',
		"password": "postgres"
	}
}

