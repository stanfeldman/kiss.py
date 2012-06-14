from core import Controller
from kiss.views.core import JsonResponse

class RestController(object):
	"""
	Controller that creates REST API to your model.
	Pass model class to it and use url property and controller property in your urls settings.
	"""
	def __init__(self, model, id_regex=r"""(?P<id>\d+)"""):
		self.model = model
		self.id_regex = id_regex
		
	@property
	def url(self):
		return self.model.__name__.lower()
		
	@property
	def controller(self):
		return {
			"": RestListController(self.model),
			self.id_regex: RestShowController(self.model)
		}
	
	
def request_params_to_dict(params):
	result = {}
	for k,v in params.items():
		result[k] = v
	return result
	

class RestListController(Controller):
	def __init__(self, model):
		self.model = model
			
	def get(self, request):
		results = self.model.select()
		return JsonResponse(results)
	
	def post(self, request):
		result = self.model.create(**request_params_to_dict(request.form))
		return JsonResponse({"id": result.id}, status=201)

			
class RestShowController(Controller):
	def __init__(self, model):
		self.model = model
		
	def get(self, request):
		result = self.model.get(id=request.params["id"])
		return JsonResponse(result)
		
	def put(self, request):
		id = request.params["id"]
		self.model.update(**request_params_to_dict(request.form)).where(id=id).execute()
		return JsonResponse({"id": id})
	
	def delete(self, request):
		result = self.model.get(id=request.params["id"])
		result.delete_instance(recursive=True)
		return JsonResponse({"result": "ok"}, status=204)
