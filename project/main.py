import sys
sys.path.append("..")
from kiss.core.application import Application
from settings import options

app = Application(options)
app.start()
