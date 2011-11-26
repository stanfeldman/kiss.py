from setuptools import setup

setup(
    name = "kiss.py",
    version = "0.0.1",
    author = "Stanislav Feldman",
    description = ("Web framework on gevent"),
    keywords = "web framework gevent",
    packages=['kiss', 'project'],
    install_requires = ['gevent', "Jinja2", "Beaker"],
    classifiers=[
        "Development Status :: 1 - Alpha",
        "Topic :: Software Development"
    ],
)
