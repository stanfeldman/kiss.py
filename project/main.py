from sys import path
path.append("/home/stanislavfeldman/projects/python/kiss.py/")
path.append("/home/stanislavfeldman/projects/python/compressinja/")
path.append("/home/stanislavfeldman/projects/python/putils/")
from kiss.core.application import Application
from settings import options


app = Application(options)
app.start()

