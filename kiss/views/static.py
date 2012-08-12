from putils.patterns import Singleton
from putils.filesystem import Dir
import mimetypes
import scss
from scss import Scss
from jsmin import jsmin
import os
import shutil
import traceback


class StaticCompiler(object):
	"""
	Static files minifier.
	"""
	def __init__(self, path):
		self.css_parser = Scss()
		scss.LOAD_PATHS = path
		
	def compile_file(self, filepath):
		mimetype = mimetypes.guess_type(filepath)[0]
		return self.compile_text(self.get_content(filepath), mimetype)
		
	def compile_text(self, text, mimetype):
		result = ""
		if mimetype == "text/css":
			result = self.css_parser.compile(text)
		elif mimetype == "application/javascript":
			result = jsmin(text)
		else:
			result = text
		return result
		
	def get_content(self, file):
		return open(file).read()


class StaticBuilder(object):
	"""
	Uses StaticCompiler to minify and compile js and css.
	"""
	def __init__(self, path):
		self.path = path
		self.compiler = StaticCompiler(self.path)
		
	def build(self):
		try:
			shutil.rmtree(self.path + "/build")
		except:
			pass
		try:
			Dir.walk(self.path, self.build_file)
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
