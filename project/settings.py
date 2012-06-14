from os import path
current_dir = path.dirname(path.abspath(__file__))
import sys
sys.path.append(path.join(current_dir, "../../kiss.py"))
sys.path.append(path.join(current_dir, "../../compressinja/"))
sys.path.append(path.join(current_dir, "../../putils/"))
from kiss.core.application import Application
from controllers.controller1 import Controller1
from controllers.controller2 import Controller2
from kiss.core.events import ApplicationStarted
from kiss.controllers.events import BeforeControllerAction
from kiss.models import SqliteDatabase
from kiss.core.exceptions import InternalServerError
from kiss.controllers.page import PageController
from kiss.controllers.rest import RestController
from models.models import Blog


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
			"3": Controller1(),
			"4": Controller2
		},
		"3": PageController("static_view.html", {"foo": "bar"}),
		RestController(Blog).url: RestController(Blog).controller
	},
	"views": {
		"templates_path": "views.templates",
		"static_path": "views.static"
	},
	"events": {
		ApplicationStarted: Controller2.application_after_load,
		BeforeControllerAction: Controller2.before_controller_action,
		InternalServerError.code: Controller2.internal_server_error
	},
	"models": {
		"engine": SqliteDatabase,
		#"host": "localhost",
		"database": path.join(current_dir, "kiss_py_project.sqldb")#,#,
		#"user": 'postgres',
		#"password": "postgres"
	}
}

