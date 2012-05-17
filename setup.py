from distutils.core import setup
try:
	from setuptools import setup
except:
	pass

setup(
    name = "kiss.py",
    version = "0.2.2",
    author = "Stanislav Feldman",
    description = ("MVC web framework in Python with Gevent, Jinja2, Werkzeug"),
    url = "https://github.com/stanislavfeldman/kiss.py",
    keywords = "web framework gevent jinja2 werkzeug orm",
    packages=[
    	"kiss", "kiss.controllers", "kiss.core", "kiss.views", "kiss.models"
    ],
    install_requires = ['gevent', "jinja2", "compressinja", "beaker", "werkzeug", "putils", "jsmin", "scss", "peewee"],
    classifiers=[
        "Development Status :: 4 - Beta",
        "Topic :: Software Development",
        "Topic :: Software Development :: Libraries :: Application Frameworks"
    ],
)
