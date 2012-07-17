from os import path
current_dir = path.dirname(path.abspath(__file__))
import sys
sys.path.append(path.join(current_dir, "../../kiss.py"))
sys.path.append(path.join(current_dir, "../../compressinja/"))
sys.path.append(path.join(current_dir, "../../putils/"))
sys.path.append(path.join(current_dir, "../../pev/"))
from kiss.core.application import Application
from controllers.controller1 import Controller1
from controllers.controller2 import Controller2
from kiss.core.events import ApplicationStarted
from kiss.controllers.events import BeforeControllerAction
from kiss.models import SqliteDatabase
from kiss.core.exceptions import InternalServerError
from kiss.controllers.page import PageController
from kiss.controllers.rest import RestController
from kiss.controllers.auth import AuthController
from models.models import Blog
from controllers.auth import AuthPageController, AuthSuccessController


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
		RestController(Blog).url: RestController(Blog).controller,
		"auth": AuthController({
			"common": {
				"base_uri": "http://test.com:8080/auth/",
				"success_uri": "/authsuccess/"
			},
			"google": {
				"client_id": "691519038986.apps.googleusercontent.com",
				"client_secret": "UsLDDLu-1ry8IgY88zy6qNiU"
			},
			"vk": {
				"client_id": "2378631",
				"client_secret": "oX5geATcgJgWbkfImli9"
			},
			"facebook": {
				"client_id": "485249151491568",
				"client_secret": "66f2503d9806104dd47fca55a6fbbac3"
			},
			"yandex": {
				"client_id": "e1dbe6ca53c14389922d6b77e36e9dee",
				"client_secret": "7f1cb1a0c1534a9f8af98b60d8d187bb"
			}
		}),
		"authsuccess": AuthSuccessController,
		"authpage": AuthPageController
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

