from kiss.views.templates import TemplateResponse
from kiss.views.core import RedirectResponse
from kiss.controllers.core import Controller
import requests
import json
from werkzeug.urls import url_decode
from putils.types import Dict, Regex
from urlparse import urljoin
from werkzeug.urls import url_encode
	
	
class AuthBackend(object):
	"""
	Base oauth backend
	"""
	def get_code(self, request, options):
		params = {
			"client_id": options["client_id"],
			"redirect_uri": options["redirect_uri"],
			"scope": options["scope"],
			"response_type": "code",
			"approval_prompt": "force",
			"access_type": "offline"
		}
		return RedirectResponse("%s?%s" % (options["authorization_uri"], url_encode(params)))
		
	def get_access_token(self, request, options):
		params = {
			"client_id": options["client_id"],
			"client_secret": options["client_secret"],
			"grant_type": "authorization_code",
			"code": request.args["code"],
			"redirect_uri": options["redirect_uri"]
		}
		response = requests.post(options["get_token_uri"], params).text
		return self.prepare_access_token_response(response)
		
	def prepare_access_token_response(self, response):
		return json.loads(response)
		
	def get_user_info(self, request, options, access_token_result):
		if "access_token" not in access_token_result or not access_token_result["access_token"]:
			return RedirectResponse(AuthController.options["common"]["error_uri"])
		self.access_token = access_token_result["access_token"]
		params = self.prepare_user_info_request_params(access_token_result)
		user_info_response = json.loads(requests.get("%s?%s" % (options["target_uri"], url_encode(params)), auth=self.auth).text)
		user_info_response = self.process_user_info_response(request, user_info_response)
		return RedirectResponse("%s?%s" % (AuthController.options["common"]["success_uri"], url_encode(user_info_response)))
				
	def prepare_user_info_request_params(self, access_token_result):
		return {"access_token": access_token_result["access_token"]}
		
	def process_user_info_response(self, request, user_info_response):
		result = {}
		print user_info_response
		result["id"] = user_info_response["id"]
		return result
		
	def auth(self, request):
		request.headers["Authorization"] = "Bearer %s" % self.access_token
		return request

		
class GoogleAuthBackend(AuthBackend):
	def process_user_info_response(self, request, user_info_response):
		result = {}
		print user_info_response
		result["id"] = user_info_response["id"]
		result["email"] = user_info_response["email"]
		result["firstname"] = user_info_response["name"]
		result["lastname"] = user_info_response["family_name"]
		return result

	
class VkAuthBackend(AuthBackend):
	def prepare_user_info_request_params(self, access_token_result):
		return {"access_token": access_token_result["access_token"], "uids": access_token_result["user_id"], "fields": "uid, first_name, last_name, nickname, screen_name, sex, bdate, city, country, photo, photo_medium, photo_big"}
		
	def process_user_info_response(self, request, user_info_response):
		result = {}
		user_info_response = user_info_response["response"][0]
		print user_info_response
		result["id"] = user_info_response["uid"]
		result["firstname"] = user_info_response["first_name"]
		result["lastname"] = user_info_response["last_name"]
		return result

	
class FacebookAuthBackend(AuthBackend):
	def prepare_access_token_response(self, response):
		return url_decode(response)
		
	def process_user_info_response(self, request, user_info_response):
		result = {}
		print user_info_response
		result["id"] = user_info_response["id"]
		result["email"] = user_info_response["email"]
		result["firstname"] = user_info_response["first_name"]
		result["lastname"] = user_info_response["last_name"]
		return result


class AuthController(object):
	"""
	Controller for social auth, use it in your url mappings
	"""
	options = {
		"common": {
			"base_uri": "http://localhost:8080/auth/",
			"success_uri": "success/",
			"error_uri": "error/"
		},
		"google": {
			"authorization_uri": "https://accounts.google.com/o/oauth2/auth",
			"scope": "https://www.googleapis.com/auth/userinfo.profile https://www.googleapis.com/auth/userinfo.email",
			"get_token_uri": "https://accounts.google.com/o/oauth2/token",
			"redirect_uri": "google/callback",
			"target_uri": "https://www.googleapis.com/oauth2/v1/userinfo",
			"backend": GoogleAuthBackend()
		},
		"vk": {
			"authorization_uri": "http://api.vk.com/oauth/authorize",
			"scope": "",
			"get_token_uri": "https://api.vk.com/oauth/token",
			"redirect_uri": "vk/callback",
			"target_uri": "https://api.vk.com/method/users.get",
			"backend": VkAuthBackend()
		},
		"facebook": {
			"authorization_uri": "https://www.facebook.com/dialog/oauth",
			"scope": "email",
			"get_token_uri": "https://graph.facebook.com/oauth/access_token",
			"redirect_uri": "facebook/callback",
			"target_uri": "https://graph.facebook.com/me",
			"backend": FacebookAuthBackend()
		}
	}
	
	def __new__(cls, opts):
		AuthController.options = Dict.merge(AuthController.options, opts)
		base_uri = AuthController.options["common"]["base_uri"]
		AuthController.options["common"]["success_uri"] = urljoin(base_uri, AuthController.options["common"]["success_uri"])
		AuthController.options["common"]["error_uri"] = urljoin(base_uri, AuthController.options["common"]["error_uri"])
		for backend, params in AuthController.options.items():
			if "redirect_uri" in params:
				params["redirect_uri"] = urljoin(base_uri, params["redirect_uri"])
		return {
			Regex.string_url_regex("backend"): {
				"": StartAuthController,
				"callback": EndAuthController,
			}
		}

	
class StartAuthController(Controller):
	"""
	Controller which starts oauth flow
	"""
	def get(self, request):
		current_options = AuthController.options[request.params["backend"]]
		return current_options["backend"].get_code(request, current_options)
		

class EndAuthController(Controller):
	"""
	Controller which finishes oauth flow
	def get(self, request):
		current_options = AuthController.options[request.params["backend"]]
		access_token_result = current_options["backend"].get_access_token(request, current_options)
		return current_options["backend"].get_user_info(request, current_options, access_token_result)

