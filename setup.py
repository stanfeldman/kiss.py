from distutils.core import setup
try:
	from setuptools import setup
except:
	pass

setup(
    name = "kiss.py",
    version = "0.0.5",
    author = "Stanislav Feldman",
    description = ("MVC web framework on Gevent"),
    keywords = "web framework gevent",
    packages=[
    	'kiss', "kiss.controllers", "kiss.core", "kiss.views"
    ],
    install_requires = ['gevent', "jinja2", "beaker", "werkzeug"],
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Topic :: Software Development",
        "Topic :: Software Development :: Libraries :: Application Frameworks"
    ],
)
