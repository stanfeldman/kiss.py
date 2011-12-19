from putils.patterns import Singleton
from putils.filesystem import Dir
import mimetypes
from scss.parser import Stylesheet
from jsmin import jsmin
import os

class StaticBuilder(Singleton):
	def __init__(self):
		self.css_parser = Stylesheet(options={"compress": True})
		self.path = ""
		
	def build(self, path):
		self.path = path
		Dir.walk(path, self.build_file)
		
	def build_file(self, file):
		mime_type = mimetypes.guess_type(file)[0]
		new_path = self.path + "/build" + file.replace(self.path, "")
		result = ""
		if mime_type == "text/css":
			result = self.css_parser.loads(self.get_content(file))
		elif mime_type == "application/javascript":
			result = jsmin(self.get_content(file))
		if result:
			try:
				os.makedirs(os.path.dirname(new_path))
			except:
				pass
			with open(new_path, "w") as f:
				f.write(result)
				
	def get_content(self, file):
		return open(file).read()
