from distutils.core import setup
try:
	from setuptools import setup
except:
	pass

setup(
    name = "kiss.py",
    version = "0.0.7",
    author = "Stanislav Feldman",
    description = ("MVC web framework in Python with Gevent, Jinja2, Werkzeug"),
    url = "https://github.com/stanislavfeldman/kiss.py",
    keywords = "web framework gevent jinja2 werkzeug orm",
    packages=[
    	'kiss', "kiss.controllers", "kiss.core", "kiss.views"
    ],
    install_requires = ['gevent', "jinja2", "beaker", "werkzeug", "putils"],
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Topic :: Software Development",
        "Topic :: Software Development :: Libraries :: Application Frameworks"
    ],
)
