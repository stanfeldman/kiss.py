from putils.patterns import Singleton
from putils.filesystem import Dir
import mimetypes
from scss.parser import Stylesheet
from jsmin import jsmin
import os
import shutil


class StaticCompiler(Singleton):
	def __init__(self):
		self.css_parser = Stylesheet(options={"compress": True})
		
	def compile_file(self, filepath):
		mimetype = mimetypes.guess_type(filepath)[0]
		return self.compile_text(self.get_content(filepath), mimetype)
		
	def compile_text(self, text, mimetype):
		result = ""
		if mimetype == "text/css":
			result = self.css_parser.loads(text)
		elif mimetype == "application/javascript":
			result = jsmin(text)
		else:
			result = text
		return result
		
	def get_content(self, file):
		return open(file).read()


class StaticBuilder(Singleton):
	def __init__(self):
		self.path = ""
		self.compiler = StaticCompiler()
		
	def build(self, path):
		self.path = path
		try:
			shutil.rmtree(self.path + "/build")
			Dir.walk(path, self.build_file)
		except:
			pass
		
	def build_file(self, file):
		new_path = self.path + "/build" + file.replace(self.path, "")
		result = self.compiler.compile_file(file)
		if result:
			try:
				os.makedirs(os.path.dirname(new_path))
			except:
				pass
			with open(new_path, "w") as f:
				f.write(result)
