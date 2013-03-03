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
		
	def compile_file(self, filepath, need_compilation=True):
		result = self.get_content(filepath)
		if need_compilation:
			print "compiling ", filepath
			mimetype = mimetypes.guess_type(filepath)[0]
			result = self.compile_text(result, mimetype)
		return result
		
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
	def __init__(self, path, static_not_compile):
		self.path = path
		self.static_not_compile = static_not_compile
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
		rel_path = file.replace(self.path, "")
		need_compilation = True
		if rel_path in self.static_not_compile:
			need_compilation = False
		new_path = self.path + "/build" + rel_path
		result = self.compiler.compile_file(file, need_compilation=need_compilation)
		if result:
			try:
				os.makedirs(os.path.dirname(new_path))
			except:
				pass
			with open(new_path, "w") as f:
				f.write(result)
